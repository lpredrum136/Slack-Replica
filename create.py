from flask import Flask
from models import *

app = Flask(__name__)

# commented out to try deploying app
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://postgres:legolas136@localhost/postgres"
# app.config['SQLALCHEMY_DATABASE_URI'] = "postgres://fkrrwcrbpazwzy:d91e42e15d71e1faab561ad19c006f22090503a5db973c08e4d40dc5271a5417@ec2-54-243-208-234.compute-1.amazonaws.com:5432/daorepv9mko282"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

def main():
    db.create_all()

if __name__ == "__main__":
    with app.app_context():
        main()