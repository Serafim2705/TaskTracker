from flask_httpauth import HTTPTokenAuth
auth = HTTPTokenAuth()
active_tokens = {"test_token": "user11"}
from flask import Flask, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()
app = Flask(__name__)

CORS(app)

app.secret_key = 'my_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:123@localhost:5432/postgres'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)



