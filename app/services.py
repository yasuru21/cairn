from sqlalchemy import func
from app import db
from app.models import Card, Review
import re


def get_day_view(deck_id: int, day_number: int):
    """
    Returns every card from day 1..day_number for this deck, each annotated
    with its most recent review result *for this specific day_number*.

    This is the core mechanic: a card's color on Day 3 depends only on how
    it was reviewed during Day 3's session, not on any other day's history.
    """
    cards = (
        Card.query.filter(Card.deck_id == deck_id, Card.day_number <= day_number)
        .order_by(Card.day_number, Card.id)
        .all()
    )

    if not cards:
        return []

    card_ids = [c.id for c in cards]

    # Subquery: latest review timestamp per card, scoped to this day_number
    latest_review_subq = (
        db.session.query(
            Review.card_id, func.max(Review.reviewed_at).label("latest_time")
        )
        .filter(Review.card_id.in_(card_ids), Review.day_number == day_number)
        .group_by(Review.card_id)
        .subquery()
    )

    latest_reviews = (
        db.session.query(Review)
        .join(
            latest_review_subq,
            (Review.card_id == latest_review_subq.c.card_id)
            & (Review.reviewed_at == latest_review_subq.c.latest_time),
        )
        .all()
    )
    result_by_card = {r.card_id: r.result for r in latest_reviews}

    return [
        {
            "card": c,
            "status": (
                "correct"
                if result_by_card.get(c.id) is True
                else "incorrect"
                if result_by_card.get(c.id) is False
                else "unreviewed"
            ),
        }
        for c in cards
    ]


def record_review(card_id: int, day_number: int, result: bool):
    review = Review(card_id=card_id, day_number=day_number, result=result)
    db.session.add(review)
    db.session.commit()
    return review

def parse_bulk_cards(raw_text: str):
    """
    Parses pasted text into a list of (front, back) tuples.
    Supports lines separated by tab, comma, or ' - ' (Quizlet/Anki export formats).
    Skips blank lines and lines that can't be split into two parts.
    """
    pairs = []
    for line in raw_text.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        if "\t" in line:
            parts = line.split("\t", 1)
        elif "," in line:
            parts = line.split(",", 1)
        elif " - " in line:
            parts = line.split(" - ", 1)
        else:
            continue  # can't parse this line, skip it
        if len(parts) == 2 and parts[0].strip() and parts[1].strip():
            pairs.append((parts[0].strip(), parts[1].strip()))
    return pairs


def split_into_days(pairs, terms_per_day: int):
    """
    Chunks a list of (front, back) pairs into groups of terms_per_day,
    returning a list of (day_number, front, back) tuples.
    """
    result = []
    for i, (front, back) in enumerate(pairs):
        day_number = (i // terms_per_day) + 1
        result.append((day_number, front, back))
    return result
