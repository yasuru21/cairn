# Cumulative Flashcards

A customizable cumulative-review flashcard app, inspired by GregMat's Vocab
Mountain. Add cards in daily batches; review cumulatively (all days up to
today), with pass/fail tracked per card per day.

## Local setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # then edit .env with real values
```

By default `DATABASE_URL` in `app/__init__.py` falls back to a local SQLite
file if `.env` isn't set, so you can run immediately without MySQL installed.
Once you have MySQL running locally, set `DATABASE_URL` in `.env` to your
MySQL connection string (see `.env.example`) and re-run migrations.

```bash
flask --app run db init        # first time only
flask --app run db migrate -m "initial schema"
flask --app run db upgrade
python run.py
```

Visit http://localhost:5000, sign up, create a deck, add Day 1 cards, and
review.

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

## Git workflow

1. Commit at the end of each working unit (not each file).
2. Push after every commit — no need for branches solo, until collaborating.
3. `.env` is gitignored — never commit real secrets; keep `.env.example`
   updated as a template for whoever (including future-you) sets this up
   again.

```bash
git add -A
git commit -m "describe the working unit you just finished"
git push origin main
```

## Deployment

Target: Render or Railway (both support Flask + managed Postgres/MySQL
cleanly). Steps once MVP works locally:
1. Push final MVP commit to GitHub.
2. Create a new Web Service on Render/Railway, connect the GitHub repo.
3. Add a managed database addon; copy its connection string into the
   platform's environment variables as `DATABASE_URL`.
4. Set `SECRET_KEY` as an environment variable (never commit it).
5. Set the start command to `gunicorn run:app` (add `gunicorn` to
   requirements.txt before deploying).
6. Run migrations against the production DB (`flask db upgrade`) via the
   platform's shell/console feature.
