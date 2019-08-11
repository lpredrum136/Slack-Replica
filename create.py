from flask import Flask
from models import *

app = Flask(__name__)

# commented out to try deploying app
# app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://postgres:legolas136@localhost/postgres"
app.config['SQLALCHEMY_DATABASE_URI'] = "postgres://slrdxhcahegldy:d08aa992a6d5d714b50c66dece9cca10c9d4b61d01ac705fbb9d205fe857bac7@ec2-50-19-222-129.compute-1.amazonaws.com:5432/dam82ofh6k9khf"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

def main():
    db.create_all()

if __name__ == "__main__":
    with app.app_context():
        main()