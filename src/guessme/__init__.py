import asyncio
import json
from os import environ
from typing import Any

from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from openai import OpenAI

app = FastAPI()

MODEL_DEFAULT = "llama3-hermes-8b"


def parse_response(choice) -> dict[str, Any]:
    return json.loads(
        choice.message.content.replace("<end_of_turn>", "")
        .replace("”", '""')
        .replace("```json", "")
        .strip()
        .strip("`")
    )


async def game_start(client: OpenAI) -> dict[str, Any]:
    try:
        completion = client.chat.completions.create(
            model=environ.get("OPENAI_MODEL", MODEL_DEFAULT),
            messages=[
                {
                    "role": "user",
                    "content": "I want to welcome users to play a word guessing game called GuessMe. "
                    "Please craft a welcome message, "
                    "and quickly explain that the user can either ask a yes no question, "
                    "or attempt to answer. "
                    "Then, pick a random noun from the dictionary as the answer to the game. "
                    "Construct a JSON following the template below and fill the placeholder accordingly,\n"
                    '{"message": <the welcome message>, "type": "answer", "response": <random noun from dictionary>}\n'
                    "Return only the JSON without comments, do not include answer in welcome message.",
                },
            ],
        )
        return parse_response(completion.choices[0])
    except Exception:
        print(completion)

        await asyncio.sleep(5)

        return await game_start(client)


async def game_progress(client: OpenAI, answer: str, input: str) -> dict[str, Any]:
    try:
        completion = client.chat.completions.create(
            model=environ.get("OPENAI_MODEL", MODEL_DEFAULT),
            messages=[
                {
                    "role": "user",
                    "content": "You are a stateless chatbot in a word guessing game, "
                    "expecting either a yes/no question, or an answer. "
                    'Treat most "is it X" sentences as answer attempt. '
                    "If the input does not meet the expectation, reject the input. "
                    "Craft a descriptive response text for each case accordingly, do not mention the answer. "
                    "Return just a JSON for each of the type of input:\n"
                    '1. For yes/no questions: {"type": "question", "input": <given input>, "response": <true or false>, "message": <response text>}\n'
                    '2. For answer attempt: {"type": "guess", "input": <extract the guessed noun from input text>, "response": <true or false>, "message": <response text>}\n'
                    '3. For invalid input: {"type": "invalid", "message": [response text]}\n'
                    f'The answer you are expecting is "{answer}", '
                    "and the input is as follows, \n"
                    f"{input}",
                }
            ],
        )
        return parse_response(completion.choices[0])
    except Exception:
        print(completion)

        await asyncio.sleep(5)

        return await game_progress(client, answer, input)


@app.websocket("/chat")
async def chat(websocket: WebSocket) -> None:
    client = OpenAI(
        base_url=environ.get("OPENAI_BASE_URL", "http://localhost:1337/v1"),
        api_key=environ.get("OPENAI_API_KEY", "n/a"),
    )

    await websocket.accept()

    response_initial = await game_start(client)
    await websocket.send_text(json.dumps(response_initial))

    while True:
        data = await websocket.receive_text()

        response = await game_progress(client, response_initial["response"], data)
        await websocket.send_text(json.dumps(response))


app.mount("/", StaticFiles(directory="static", html=True), name="static")


def main() -> FastAPI:
    return app
