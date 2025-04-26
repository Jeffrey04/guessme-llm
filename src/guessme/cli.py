from ast import literal_eval
from collections.abc import Callable
from os import environ
from typing import Literal

import dspy

DEBUG = bool(literal_eval(environ.get("DEBUG", "False")))


class NewGame(dspy.Signature):
    speech: str = dspy.OutputField(
        desc="The welcome text for a word guessing game called GuessMe, with gameplay explanation adapted from the game 20 questions without the question limit."
    )
    answer: str = dspy.OutputField(
        desc="The chosen random noun as the answer for a 20 questions game session"
    )


class Classify(dspy.Signature):
    attempt: str = dspy.InputField(desc="The user input in a 20 questions game")
    category: Literal["question", "invalid"] = dspy.OutputField(
        desc="The type of attempt supplied by the user in a 20 questions word guessing game"
    )


class Question(dspy.Signature):
    question: str = dspy.InputField(
        desc="The user's question or a guess in a 20 questions game."
    )
    answer: str = dspy.InputField(
        desc="The noun user is attempting to guess in a 20 questions game."
    )
    response: str = dspy.OutputField(
        desc="The yes/no answer to the user's question in a sentence with the answer word replaced by 'the answer' whenever applicable"
    )
    result: bool = dspy.OutputField(desc="The true/false response to the user question")
    found: bool = dspy.OutputField(
        desc="True only if this is a guess and it matches the answer"
    )


class Invalid(dspy.Signature):
    attempt: str = dspy.InputField(desc="The user input in a 20 questions game")
    response: str = dspy.OutputField(
        desc="An explanation on why the user input cannot be accepted in a 20 questions game."
    )


def new_game_verifier(_args, pred: dspy.Prediction) -> float:
    DEBUG and print(pred)  # type: ignore

    return 1.0 if len(pred.answer.split()) == 1 else 0.0


def do_not_spoil(answer: str) -> Callable[..., float]:
    def inner(_args, pred: dspy.Prediction) -> float:
        if hasattr(pred, "found") and pred.found:
            return 1.0

        DEBUG and print(pred)  # type: ignore

        return (
            1.0
            if answer.lower() not in pred.response.lower()
            and len(pred.response.split()) > 1
            else 0.0
        )

    return inner


def start_new_game(module: dspy.BestOfN) -> tuple[str, str]:
    result = module()

    return result.speech, result.answer


def process_attempt(
    attempt, answer, classifier, question, invalid
) -> tuple[str, bool, bool]:
    match classifier(attempt=attempt, answer=answer).category:
        case "question":
            response = question(question=attempt, answer=answer)
            return response.response, response.result, response.found

        case _:
            response = invalid(attempt=attempt)

            return response.response, False, False


def main() -> None:
    answer = None

    dspy.configure(
        lm=dspy.LM(
            f"openai/{environ['OPENAI_MODEL']}",
            api_base=environ["OPENAI_BASE_URL"],
            api_key=environ["OPENAI_API_KEY"],
            temperature=1.0,
            cache=False,
        )
    )
    module_new = dspy.BestOfN(
        module=dspy.Predict(NewGame),
        N=5,
        reward_fn=new_game_verifier,
        threshold=1.0,
    )
    module_classify = dspy.ChainOfThought(Classify)
    module_question = None
    module_invalid = None

    while True:
        if answer is None:
            speech, answer = start_new_game(module_new)

            print(speech)

            module_question = dspy.BestOfN(
                module=dspy.ChainOfThought(Question),
                N=10,
                reward_fn=do_not_spoil(answer),
                threshold=1.0,
            )
            module_invalid = dspy.BestOfN(
                module=dspy.Predict(Invalid),
                N=5,
                reward_fn=do_not_spoil(answer),
                threshold=1.0,
            )

        match input("> "):
            case command if command == "quit":
                break

            case command if command == "end" and answer is not None:
                answer = None

            case attempt:
                response, _result, guessed = process_attempt(
                    attempt,
                    answer,
                    module_classify,
                    module_question,
                    module_invalid,
                )

                if guessed:
                    answer = None

                print(response)


if __name__ == "__main__":
    main()
