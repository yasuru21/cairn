from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import login_required, current_user
from app import db
from app.models import Deck, Card, Review
from app.services import get_day_view, record_review, parse_bulk_cards, split_into_days
from itertools import groupby

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
        raw_text = request.form["word_list"]
        terms_per_day = int(request.form["terms_per_day"])

        pairs = parse_bulk_cards(raw_text)
        if not pairs:
            flash("Couldn't parse any terms — check your formatting.")
            return redirect(url_for("main.new_deck"))

        assigned = split_into_days(pairs, terms_per_day)
        total_days = assigned[-1][0]  # day number of the last card = total days

        deck = Deck(name=request.form["name"], user_id=current_user.id, target_days=total_days, terms_per_day=terms_per_day)
        db.session.add(deck)
        db.session.commit()

        for day_number, front, back in assigned:
            db.session.add(Card(deck_id=deck.id, front_text=front, back_text=back, day_number=day_number))
        db.session.commit()

        return redirect(url_for("main.view_deck", deck_id=deck.id))
    return render_template("new_deck.html")

@main_bp.route("/decks/<int:deck_id>/edit-list", methods=["GET", "POST"])
@login_required
def edit_deck_list(deck_id):
    deck = Deck.query.get_or_404(deck_id)

    if request.method == "POST":
        raw_text = request.form["word_list"]
        terms_per_day = int(request.form["terms_per_day"])

        pairs = parse_bulk_cards(raw_text)
        if not pairs:
            flash("Couldn't parse any terms — check your formatting.")
            return redirect(url_for("main.edit_deck_list", deck_id=deck.id))

        # Wipe existing cards (cascades to delete their reviews too)
        for card in list(deck.cards):
            db.session.delete(card)
        db.session.commit()

        assigned = split_into_days(pairs, terms_per_day)
        total_days = assigned[-1][0]

        deck.target_days = total_days
        deck.terms_per_day = terms_per_day
        for day_number, front, back in assigned:
            db.session.add(Card(deck_id=deck.id, front_text=front, back_text=back, day_number=day_number))
        db.session.commit()

        return redirect(url_for("main.view_deck", deck_id=deck.id))

    # GET: pre-fill the textarea with the current list
    cards = Card.query.filter_by(deck_id=deck.id).order_by(Card.day_number, Card.id).all()
    current_text = "\n".join(f"{c.front_text}\t{c.back_text}" for c in cards)
    return render_template(
        "edit_deck_list.html",
        deck=deck,
        current_text=current_text,
    )

@main_bp.route("/decks/<int:deck_id>")
@login_required
def view_deck(deck_id):
    deck = Deck.query.get_or_404(deck_id)
    current_day = request.args.get("day", default=max(deck.max_day, 1), type=int)
    day_view = get_day_view(deck_id, current_day)
    grouped = [
        (day_num, list(items))
        for day_num, items in groupby(day_view, key=lambda item: item["card"].day_number)
    ]
    cards_json = [
        {
            "id": item["card"].id,
            "front_text": item["card"].front_text,
            "back_text": item["card"].back_text,
            "status": item["status"],
        }
        for item in day_view
    ]
    return render_template(
        "deck.html", deck=deck, grouped=grouped, day_view=day_view, cards_json=cards_json, current_day=current_day
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

@main_bp.route("/cards/<int:card_id>/unreview", methods=["POST"])
@login_required
def unreview_card(card_id):
    day_number = int(request.form["day_number"])
    Review.query.filter_by(card_id=card_id, day_number=day_number).delete()
    db.session.commit()
    return ("", 204)

@main_bp.route("/decks/<int:deck_id>/delete", methods=["POST"]) #delete deck
@login_required
def delete_deck(deck_id):
    deck = Deck.query.get_or_404(deck_id)
    db.session.delete(deck)
    db.session.commit()
    return redirect(url_for("main.dashboard"))

@main_bp.route("/decks/<int:deck_id>/manage")
@login_required
def manage_cards(deck_id):
    deck = Deck.query.get_or_404(deck_id)
    cards = Card.query.filter_by(deck_id=deck_id).order_by(Card.day_number, Card.id).all()
    return render_template("manage_cards.html", deck=deck, cards=cards)


@main_bp.route("/cards/<int:card_id>/edit", methods=["GET", "POST"])
@login_required
def edit_card(card_id):
    card = Card.query.get_or_404(card_id)
    if request.method == "POST":
        card.front_text = request.form["front_text"]
        card.back_text = request.form["back_text"]
        card.day_number = int(request.form["day_number"])
        db.session.commit()
        return redirect(url_for("main.manage_cards", deck_id=card.deck_id))
    return render_template("edit_card.html", card=card)


@main_bp.route("/cards/<int:card_id>/delete", methods=["POST"])
@login_required
def delete_card(card_id):
    card = Card.query.get_or_404(card_id)
    deck_id = card.deck_id
    db.session.delete(card)
    db.session.commit()
    return redirect(url_for("main.manage_cards", deck_id=deck_id))