# Cairn

A customizable cumulative-review flashcard app, inspired by GregMat's Vocab
Mountain. Add cards in daily batches; review cumulatively (all days up to
today), with pass/fail tracked per card per day.


```bash
flask --app run db init        # first time only
flask --app run db migrate -m "initial schema"
flask --app run db upgrade
python run.py
```

Visit http://localhost:5000 and sign up to save decks locally

## Data model

- `User` — one per person, owns decks
- `Deck` — a named collection of cards
- `Card` — front/back text, tagged with the day it was introduced
- `Review` — one row per review event: which card, which day it was
  reviewed *in*, and the result. This is what lets a card be marked
  correct on Day 3 and incorrect on Day 5 independently.

The core query lives in `app/services.py::get_day_view` — given a deck and a
day number, it returns every card introduced on or before that day, each
annotated with its most recent review result *for that specific day*.
