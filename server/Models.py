from db import *
from sqlalchemy import Enum
import enum


class Role(enum.Enum):
    Manager = 1
    Team_lead = 2
    Developer = 3
    Tester = 4


class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    user_password = db.Column(db.String(1000), nullable=False)  # хеш пароля
    role_name = db.Column(Enum(Role), primary_key=False)  # менеджер, тимлид, разработчик, тест-инженер


class Status(enum.Enum):
    To_do = 1
    In_progress = 2
    Code_review = 3
    Dev_test = 4
    Testing = 5
    Done = 6
    Wont_fix = 7


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, unique=True)
    type_of_task = db.Column(db.Integer, nullable=False)
    priority = db.Column(db.Integer, nullable=False)
    status = db.Column(db.Enum(Status), primary_key=False, nullable=False)
    topic = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(50), nullable=True)
    executor = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    owner_task = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date_of_found = db.Column(db.DateTime, nullable=False)
    date_of_edit = db.Column(db.DateTime, nullable=False)


class TaskBlockTask(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    blocked_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    block_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)


class SubtaskForTask(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    main_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    subtask_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
