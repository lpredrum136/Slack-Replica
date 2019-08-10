from flask import Flask, session
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from sqlalchemy.sql import func

app = Flask(__name__)

# For localhost only
# app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://postgres:legolas136@localhost/postgres"
app.config['SQLALCHEMY_DATABASE_URI'] = "postgres://fkrrwcrbpazwzy:d91e42e15d71e1faab561ad19c006f22090503a5db973c08e4d40dc5271a5417@ec2-54-243-208-234.compute-1.amazonaws.com:5432/daorepv9mko282"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
ma = Marshmallow(app)

class Chatter(db.Model):
    __tablename__ = "chatters"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    hash = db.Column(db.String, nullable=False)
    # Cascade in the following line is to delete the messages in db (see in app.py route '/channel') if there are more than 100 msgs stored.
    # Normally it would cause an error. See https://www.tutorialspoint.com/sqlalchemy/sqlalchemy_orm_deleting_related_objects
    messages = db.relationship("Message", backref="chatter", lazy=True, cascade = "all, delete, delete-orphan")

class Channel(db.Model):
    __tablename__ = "channels"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    topic = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=False)
    datetime = db.Column(db.DateTime(timezone=True), server_default=func.now())
    messages = db.relationship("Message", order_by="Message.id", backref="channel", lazy=True, cascade = "all, delete, delete-orphan")

    def add_message(self, message):
        msg = Message(message=message, channel_id=self.id, chatter_id=session['user_id']) # session['user_id'] will be available in app.py 
                                                                                        # by the time this method is executed
        db.session.add(msg)
        db.session.commit()

class Message(db.Model):
    __tablename__ = "messages"
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String, nullable=False)
    datetime = db.Column(db.DateTime(timezone=True), server_default=func.now())
    channel_id = db.Column(db.Integer, db.ForeignKey("channels.id"), nullable=False)
    chatter_id = db.Column(db.Integer, db.ForeignKey("chatters.id"), nullable=False)

"""This following class is for the typeahead only
Because SQLAlchemy object returned from the query can not be jsonified for typeahead. We need help from
https://flask-marshmallow.readthedocs.io/en/latest/ to jsonify them, so that they can be plug into typeahead plugin"""


class ChannelSchema(ma.ModelSchema):
    class Meta:
        model = Channel