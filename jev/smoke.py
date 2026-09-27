import os
import sys

from typesafe_sdk import Choice, TypeSafeClient


if not os.environ.get("TYPESAFE_API_KEY"):
    print("TYPESAFE_API_KEY is required", file=sys.stderr)
    sys.exit(3)

try:
    with TypeSafeClient(timeout=10) as client:
        response = client.system_one(
            state={"message": "Please remember that our demo uses the hackathon GBrain."},
            questions={
                "route": Choice(
                    instructions="Should the assistant save this fact, recall a prior fact, or answer without memory?",
                    criteria={
                        "save": "The user explicitly asks to remember a fact",
                        "recall": "The user asks to retrieve an existing memory",
                        "other": "Neither memory action is requested",
                    },
                ),
            },
        )
    answer = response.choices["route"]
    assert answer.choice in {"save", "recall", "other"}
    assert set(answer.probabilities) == {"save", "recall", "other"}
    assert isinstance(answer.confidence, float)
    print(f"JEV HTTP {response.raw_http_response.status_code}; typed Choice answer verified")
except Exception as error:
    status = getattr(error, "status_code", None)
    print(f"JEV test failed: {type(error).__name__}; HTTP status: {status or 'unavailable'}", file=sys.stderr)
    sys.exit(1)
