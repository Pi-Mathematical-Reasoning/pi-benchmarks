#!/usr/bin/env python3
"""A stand-in for the AWS CLI's `s3api put-object` and `get-object`, for tests.

Objects live as files under $FAKE_AWS_STORE/<bucket>/<key>. Every call's
arguments are appended to $FAKE_AWS_STORE/calls.jsonl. $FAKE_AWS_FAIL, when
set, is printed as the error of every call, as the real CLI prints one.
Messages and the exit code 254 are the real CLI's.
"""

import json
import os
import shutil
import sys
from pathlib import Path

store = Path(os.environ["FAKE_AWS_STORE"])
arguments = sys.argv[1:]
with (store / "calls.jsonl").open("a") as calls:
    calls.write(json.dumps(arguments) + "\n")


def fail(code: str, operation: str, message: str) -> None:
    print(
        f"\nAn error occurred ({code}) when calling the {operation} operation: {message}",
        file=sys.stderr,
    )
    sys.exit(254)


def option(name: str) -> str:
    return arguments[arguments.index(name) + 1]


if os.environ.get("FAKE_AWS_FAIL"):
    fail(os.environ["FAKE_AWS_FAIL"], "GetObject", "simulated")

stored = store / option("--bucket") / option("--key")
if arguments[:2] == ["s3api", "put-object"]:
    if option("--if-none-match") == "*" and stored.exists():
        fail(
            "PreconditionFailed",
            "PutObject",
            "At least one of the pre-conditions you specified did not hold",
        )
    stored.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(option("--body"), stored)
    print(json.dumps({"ETag": '"0"'}))
elif arguments[:2] == ["s3api", "get-object"]:
    if not stored.exists():
        fail("NoSuchKey", "GetObject", "The specified key does not exist.")
    shutil.copyfile(stored, arguments[-1])
    print(json.dumps({"ContentLength": stored.stat().st_size}))
else:
    sys.exit(f"fake aws: unsupported call {arguments}")
