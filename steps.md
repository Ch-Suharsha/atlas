```bash
cp .env.example .env
# Add HF_ENDPOINT_URL/HF_TOKEN or select the Groq provider and add GROQ_API_KEY.


docker compose --profile dev-mail up --build -d

# The API applies Alembic migrations during startup. To run explicitly:
docker compose run --rm api alembic upgrade head

docker compose run --rm --build api python -m app.seed # this will load user data to the DB

docker compose run --rm --build api python -m app.ingest --batch-size 256 # run this in a seperate terminal, this will take a lot of time, so dont worry

docker compose run --rm --build api python -m app.ingest_policies # run this in a different terminal should take  max 2 mins

# UI   http://localhost:8000 this is your actual UI
# Mail http://localhost:8025 this is where you will see the mail, think of it like your local gmail

# Use the demo email `demo@atlas.local` when the identity flow asks for it.

# command to stop it
docker compose --profile dev-mail down
```
