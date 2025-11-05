from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True, nullable=False)
    password = db.Column(db.String(300), nullable=False)
    theme = db.Column(db.String(20), default="default")
    monthly_budget = db.Column(db.Float, default=0)
    expenses = db.relationship('Expense', backref='user', lazy=True)
    incomes = db.relationship('Income', backref='user', lazy=True)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40), nullable=False)
    color = db.Column(db.String(7), nullable=False)
    icon = db.Column(db.String(2), nullable=False)
    budget = db.Column(db.Float, default=0)
    expenses = db.relationship('Expense', backref='category', lazy=True)
    incomes = db.relationship('Income', backref='category', lazy=True)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(100), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    date = db.Column(db.Date, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    tags = db.Column(db.String(120))
    currency = db.Column(db.String(8), default="INR")

class Income(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    source = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    recurring = db.Column(db.Boolean, default=False)
    interval = db.Column(db.String(16), default="monthly")
    currency = db.Column(db.String(8), default="INR")
    tags = db.Column(db.String(120))
