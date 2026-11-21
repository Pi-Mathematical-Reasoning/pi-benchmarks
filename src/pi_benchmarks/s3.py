"""The bucket, reached through the AWS CLI with whatever credentials the shell has."""

import re
import subprocess
from pathlib import Path

_ERROR = re.compile(r"An error occurred \(([A-Za-z]+)\)")
_SIGN_IN = {"ExpiredToken", "ExpiredTokenException", "InvalidClientTokenId", "UnauthorizedSSOToken"}


class S3Error(Exception):
    """The AWS CLI failed for a reason other than the outcome a caller asked about."""


class AwsCli:
    def __init__(self, profile: str | None = None):
        self._profile = profile

    def put_new(self, bucket: str, key: str, path: Path) -> bool:
        """Upload `path` unless the key exists: True if uploaded, False if it was there.

        S3 refuses to replace the key (If-None-Match) and checks the bytes it
        receives against a SHA-256 the CLI computes.
        """
        code = self._run(
            "put-object",
            "--bucket",
            bucket,
            "--key",
            key,
            "--body",
            str(path),
            "--if-none-match",
            "*",
            "--checksum-algorithm",
            "SHA256",
            expected={"PreconditionFailed"},
        )
        return code is None

    def get(self, bucket: str, key: str, destination: Path) -> bool:
        """Download the object to `destination`: False if there is no such key."""
        code = self._run(
            "get-object", "--bucket", bucket, "--key", key, str(destination), expected={"NoSuchKey"}
        )
        return code is None

    def _run(self, operation: str, *arguments: str, expected: set[str]) -> str | None:
        """None on success, or the error code if it is one of `expected`."""
        command = ["aws", "s3api", operation, *arguments]
        if self._profile:
            command += ["--profile", self._profile]
        try:
            done = subprocess.run(command, capture_output=True, text=True)
        except FileNotFoundError:
            raise S3Error("the AWS CLI (`aws`) is not installed or not on PATH") from None
        if done.returncode == 0:
            return None

        match = _ERROR.search(done.stderr)
        code = match.group(1) if match else None
        if code in expected:
            return code
        if code in _SIGN_IN or "aws sso login" in done.stderr:
            raise S3Error(
                f"the AWS credentials have expired or are missing ({code}): run "
                "`aws sso login --profile jaws-prod` and set AWS_PROFILE=jaws-prod"
            )
        raise S3Error(f"aws s3api {operation} failed: {done.stderr.strip() or done.returncode}")
