# GuessMe (backed by LLM)

GuessMe is a classic word guessing game implemented with LLM.

The game itself is a simple conversational game, where players get to do one of two things:

1. Guess the secret word
2. Ask an question that can only be answered with yes or no.


## Setting up the game

You would need the following:

1. uv
2. Access to OpenAI-compatible API service

Set up the project by running

```
uv sync
```

## Setting up LLM Access

The game is design and tested to run well with Gemini, however some self-hosted options
were also tested during the development. The script expects the following parameters

1. `OPENAI_BASE_URL`: The base URL to OpenAI-compatible API e.g. `"http://localhost:1337/v1"`
2. `OPENAI_API_KEY`: The key to the API
3. `OPENAI_MODEL`: The model to use that is offered by the API, e.g. `"llama3-hermes-8b"`

You can make these environment variables available with tools such as direnv, or specify them
when you issue the command to start the web application.

## Starting the web application

You can start the web application by

```
uv run uvicorn guessme:main
```

Then visit `http://localhost:8000` in your browser to play.