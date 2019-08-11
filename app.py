"""IMPORTANT: Must run python create.py first to create table by SQLAlchemy"""

""" ALSO, TO RUN THE APP:
# Fix SocketIO bug
# https://stackoverflow.com/questions/54734072/flask-socketio-raises-a-valueerror
# https://stackoverflow.com/questions/53522052/flask-app-valueerror-signal-only-works-in-main-thread
# IN terminal, type python app.py to run the web app"""

import nltk
from flask import Flask, session, render_template, request, redirect, jsonify
from flask_session import Session
from flask_jsglue import JSGlue
# from sqlalchemy import create_engine
# from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import login_required
from flask_socketio import SocketIO, emit, join_room
from sqlalchemy.sql import func
from flask_sqlalchemy import get_debug_queries

# Import table definitions
from models import *

"""Configure app"""
app = Flask(__name__)
# app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
socketio = SocketIO(app) # For chat
JSGlue(app) # For typeahead

# ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database (the old way), pool size and max overflow is to send more requests to sql
# engine = create_engine("postgres://nmveeatzgvsvqz:71ac6602574819f555d2c89d38367361795ddf1474c92c763f1ecc67b2951d0c@ec2-23-21-156-171.compute-1.amazonaws.com:5432/d1ta26pb3lelfn", pool_size=10, max_overflow=20)
# db = scoped_session(sessionmaker(bind=engine))

# Set up database (new way)
# Commented out to try deploying app
# app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://postgres:legolas136@localhost/postgres"
app.config['SQLALCHEMY_DATABASE_URI'] = "postgres://slrdxhcahegldy:d08aa992a6d5d714b50c66dece9cca10c9d4b61d01ac705fbb9d205fe857bac7@ec2-50-19-222-129.compute-1.amazonaws.com:5432/dam82ofh6k9khf"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Link the Flask app with the database
db.init_app(app)

'''=============START============='''

@app.route("/")
@login_required
def index():
    rows = Channel.query.order_by(func.random()).limit(5)
    return render_template('indexSidebar2.html', username=session['username'], rows=rows)

@app.route("/login", methods=['GET', 'POST'])
def login():
    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Get info
        username = request.form.get("username")
        password = request.form.get("password")

        # Query database for username
        rows = Chatter.query.filter_by(username=username).all()

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0].hash, password):
            # If not, return login page
            message = f"Username {username} or password is not correct. Please try again"
            return render_template("login.html", message=message)

        # Remember which user has logged in
        session["user_id"] = rows[0].id
        session["username"] = rows[0].username

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == "GET":
        return render_template("register.html")
    else:
        # Get info
        username = request.form.get("username")
        password = request.form.get("password")
        # confirmation = request.form.get("confirmation") No need because just for confirmation, already check validation in register.html
        passwordHash = generate_password_hash(password)
        # Validate info
            # Already validate in register.html
        # Check if username exists:
        rows = Chatter.query.filter_by(username=username).all()
        if len(rows) == 0:
            # If not exist yet, add to db
            chatter = Chatter(username=username, hash=passwordHash)
            db.session.add(chatter)
            db.session.commit()
            return render_template("login.html", message_success_registration="Registration successful. Now you can log in.")
        else:
            # If exists, return register page
            message = f"Username {username} is not available. Please try again."
            return render_template("register.html", message=message)

@app.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'GET':
        return render_template("create.html")
    else:
        # Get info
        channel_name = request.form.get("channelName")
        channel_desc = request.form.get("channelDesc")
        channel_topic = request.form.get("channelTopic")

        # See if channel is already made yet
        rows = Channel.query.filter_by(name=channel_name).all()
        if len(rows) == 0:
            # If not exist yet, add to db
            # Create and add channel
            channel = Channel(name=channel_name, topic=channel_topic, description=channel_desc)
            db.session.add(channel)
            db.session.commit()
            # Redirect to that channel
            return redirect(f'/channel/{channel_name}')
        else:
            # If exists, return register page
            message = f"Channel {channel_name} is not available. Please choose another name."
            return render_template("create.html", message=message)
       
@app.route('/search')
@login_required
def search():
    """This route is for the typeahead only
    Because SQLAlchemy object returned from the query can not be jsonified. We need help from
    https://flask-marshmallow.readthedocs.io/en/latest/ to jsonify them, so that they can be plug into typeahead plugin"""
    channel_schema = ChannelSchema() # Read the marshmallow above
    q = request.args.get("q")  
    qTokens = nltk.word_tokenize(q) # Extract all the word
    queryInput = '%'.join(qTokens) + '%' # Join them with * in between and at the end. For example, "ac ri" will become ac*ri*

    # Find the channels, fed as suggestions for typeahead
    rows = Channel.query.filter(Channel.name.ilike(queryInput)).all()
    data_list = [] # Because we can't jsonify the whole list
    for row in rows: # So we separate row by row
        data_list.append(channel_schema.dump(row).data) # Jsonify each row then append to the list
    return jsonify(data_list) # Finally jsonify the whole list

@app.route('/channel/<string:name>')
@login_required
def channel(name):
    # Find channel
    current_channel = Channel.query.filter_by(name=name).first()
    current_channel_id = Channel.query.with_entities(Channel.id).filter_by(name=name).first()
    # print(f"CURRENT CHANNEL ID {current_channel_id}")

    # Save the channel (SQLAlchemy object) for the sockets/chat below
    session['current_channel'] = current_channel

    # If there are more than 100 rows, delete in db so that only 100 messages are stored
    number_of_msgs = Message.query.filter_by(channel_id=current_channel_id).count()
    # print(f"NUMBER OF MSG {number_of_msgs}")
    if number_of_msgs > 100:
        number_to_delete = number_of_msgs - 100
        rows_to_delete = Message.query.filter_by(channel_id=current_channel_id).order_by(Message.id.asc()).limit(number_to_delete)
        # Note: Cannot do db.session.delete(rows_to_delete) simply because you can't
        for row in rows_to_delete:
            db.session.delete(row)
            db.session.commit()

    # Query all messages saved in db
    rows = current_channel.messages

    # Return
    return render_template('channel.html', name=name, rows=rows, channel_name=name, username=session['username'])

"""========EVERY SOCKET HERE======"""

# A dict to save clients in the form of username: session_id
clients = {}

# When connected, i.e. when you literally access the page, any page (because in JS it's 
# var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);)
# More info https://flask-socketio.readthedocs.io/en/latest/
@socketio.on('connect') # connect is a reserved keyword of Flask-SocketIO
@login_required
def addClient():
    # Get the current username to use as key
    # Value is the session_id of the connection to Socket. So each user has a unique session_id
    # Also, in this way, whenever user 'connects', i.e. visits a page (any page, as explained above),
    # The session_id is automatically updated
    clients[session['username']] = request.sid
    # Send message 'save client' to the CURRENT USER only. The data will be saved in localStorage in JS. See JS for more info.
    # This step is to validate later in JS: who is sending the message, me? or someone else?
    emit('save client', {'client_id': request.sid})
    print(f"LIST OF CLIENT: {clients}") # Just for checking in console cmd

@socketio.on('group users into room') # from JS
def groupUsersToRoom(data): # data is sent from JS
    user_room = data['room'] # Get the room, i.e. the channel name
    join_room(user_room) # Add the user into this room

@socketio.on('disconnect') # When user disconnect (close the browser tab). Again, 'disconnect' is a reserved keyword
                            # So no need to receive this event from JS side
def removeClient():
    del clients[session['username']] # Remove the client (by removing the key in the dict)

@socketio.on("send msg") # When user CLICKS on button to send message
def sendmsg(data): # 'data' is the data received from 'emit' in JS
    # The message get from socket/JS
    msg = data['msg']

    # Save the room (channel name in this case, name extracted from JS)
    # Purpose: You don't want to receive messages from someone in another room, like who the fuck is this guy and why am I
    # receiving messages from him
    # More info: https://flask-socketio.readthedocs.io/en/latest/, https://stackoverflow.com/questions/39423646/flask-socketio-emit-to-specific-user
    # And Google 'Flask socketio room'
    # This is actually the same room as route 'group users into room' because it's the same room data from JS
    thisroom = data['room']

    # So this user will join this room (channel). Other users in the same room will just receive messages from people in that room only
    join_room(thisroom)

    # Call method add_message on the SQLAlchemy Channel object, see models.py for more info on this method
    session['current_channel'].add_message(msg)

    # The sender username
    sender = Chatter.query.get(session['user_id']).username

    # The sender id, i.e. the session_id when the user CLICKS button to send msg
    sender_id = request.sid

    # The datetime
    msg_just_added = Message.query.order_by(Message.id.desc()).first()
    date_and_time = str(msg_just_added.datetime)
    msg_id = msg_just_added.id

    # Announce the msg to the channel, i.e. call 'on('announce msg')' in JS
    # Don't use broadcast=True or you will send this message to all channels
    # Instead, room=thisroom is the parameter that ensures you only send message to people in this room (channel) only
    emit("announce msg", {'msg': msg, "sender": sender, "datetime": date_and_time, "sender_id": sender_id, "msg_id": msg_id}, room=thisroom)

@socketio.on('delete msg')
def deleteMsg(data):
    record_to_delete = Message.query.get(data['msg_id'])
    db.session.delete(record_to_delete)
    db.session.commit()
    emit("deleted msg", {'deleted_msg_id': data['msg_id']}, broadcast=True)

"""===========END SOCKET=========="""

@app.route("/delete/<string:row_id>")
@login_required
def delete(row_id):
    return f"delete {row_id}"

@app.route('/channels')
@login_required
def channels():
    rows = Channel.query.all()
    return render_template("channels.html", username=session['username'], rows=rows)

"""===PM==="""
@app.route("/private")
@login_required
def privateMessage():
    return "pm"

"""DEBUG SQL-ALCHEMY QUERIES"""
"""https://www.youtube.com/watch?v=5puPZ3n06EE AND https://gist.github.com/dhrrgn/6022858"""
def sql_debug(response):
    queries = list(get_debug_queries())
    query_str = ''
    total_duration = 0.0
    for q in queries:
        total_duration += q.duration
        stmt = str(q.statement % q.parameters).replace('\n', '\n       ')
        query_str += 'Query: {0}\nDuration: {1}ms\n\n'.format(stmt, round(q.duration * 1000, 2))

    print('=' * 80)
    print(' SQL Queries - {0} Queries Executed in {1}ms'.format(len(queries), round(total_duration * 1000, 2)))
    print('=' * 80)
    print(query_str.rstrip('\n'))
    print('=' * 80 + '\n')

    return response

app.after_request(sql_debug)
"""END DEBUG SQLALCHEMY"""

# Fix SocketIO bug
# https://stackoverflow.com/questions/54734072/flask-socketio-raises-a-valueerror
# https://stackoverflow.com/questions/53522052/flask-app-valueerror-signal-only-works-in-main-thread
# IN terminal, type python app.py to run the web app
if __name__ == '__main__':
    socketio.run(app, debug=True)