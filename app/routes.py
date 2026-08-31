from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import login_required, current_user
from app import db
from app.models import Deck, Card
from app.services import get_day_view, record_review

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
@login_required
def dashboard():
    decks = Deck.query.filter_by(user_id=current_user.id).all()
    return render_template("dashboard.html", decks=decks)


@main_bp.route("/decks/new", methods=["GET", "POST"])
@login_required
def new_deck():
    if request.method == "POST":
        deck = Deck(name=request.form["name"], user_id=current_user.id)
        db.session.add(deck)
        db.session.commit()
        return redirect(url_for("main.view_deck", deck_id=deck.id))
    return render_template("new_deck.html")


@main_bp.route("/decks/<int:deck_id>")
@login_required
def view_deck(deck_id):
    deck = Deck.query.get_or_404(deck_id)
    current_day = request.args.get("day", default=max(deck.max_day, 1), type=int)
    day_view = get_day_view(deck_id, current_day)
    return render_template(
        "deck.html", deck=deck, day_view=day_view, current_day=current_day
    )


@main_bp.route("/decks/<int:deck_id>/cards/new", methods=["GET", "POST"])
@login_required
def new_card(deck_id):
    deck = Deck.query.get_or_404(deck_id)
    if request.method == "POST":
        card = Card(
            deck_id=deck.id,
            front_text=request.form["front_text"],
            back_text=request.form["back_text"],
            day_number=int(request.form["day_number"]),
        )
        db.session.add(card)
        db.session.commit()
        return redirect(url_for("main.view_deck", deck_id=deck.id))
    next_day = deck.max_day + 1
    return render_template("new_card.html", deck=deck, next_day=next_day)


@main_bp.route("/cards/<int:card_id>/review", methods=["POST"])
@login_required
def review_card(card_id):
    day_number = int(request.form["day_number"])
    result = request.form["result"] == "correct"
    record_review(card_id, day_number, result)
    deck_id = Card.query.get_or_404(card_id).deck_id
    return redirect(url_for("main.view_deck", deck_id=deck_id, day=day_number))
