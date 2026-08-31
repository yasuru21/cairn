from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    decks = db.relationship("Deck", backref="owner", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Deck(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    cards = db.relationship("Card", backref="deck", lazy=True, cascade="all, delete-orphan")

    @property
    def max_day(self):
        latest = (
            db.session.query(db.func.max(Card.day_number))
            .filter(Card.deck_id == self.id)
            .scalar()
        )
        return latest or 0


class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    deck_id = db.Column(db.Integer, db.ForeignKey("deck.id"), nullable=False)
    front_text = db.Column(db.String(500), nullable=False)
    back_text = db.Column(db.Text, nullable=False)
    day_number = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    reviews = db.relationship("Review", backref="card", lazy=True, cascade="all, delete-orphan")


class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    card_id = db.Column(db.Integer, db.ForeignKey("card.id"), nullable=False)
    day_number = db.Column(db.Integer, nullable=False)  # which review-session day this happened on
    result = db.Column(db.Boolean, nullable=False)  # True = correct, False = incorrect
    reviewed_at = db.Column(db.DateTime, default=datetime.utcnow)
