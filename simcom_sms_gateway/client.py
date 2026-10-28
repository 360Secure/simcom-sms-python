"""Authenticated Cloudflare Worker SMS client using curl (Python 3.9+)."""
import json
import re
import shutil
import subprocess
import time
from urllib.parse import quote

DEFAULT_BASE_URL = "https://simcom-sms-gateway.noreply-174.workers.dev"
PHONE_RE = re.compile(r"^\+[1-9]\d{7,14}$")
VALID_TYPES = {"otp", "notification", "alert"}


class SMSGatewayError(RuntimeError):
    """An SMS gateway API or network operation failed."""


def _request(method, url, api, payload=None, timeout=15):
    if not shutil.which("curl"):
        raise SMSGatewayError("curl is required. Install curl and try again.")
    command = ["curl", "--silent", "--show-error", "--fail-with-body",
               "--max-time", str(timeout), "--request", method,
               "--header", "Authorization: Bearer " + api,
               "--header", "Accept: application/json"]
    if payload is not None:
        command.extend(["--header", "Content-Type: application/json",
                        "--data", json.dumps(payload)])
    command.append(url)
    try:
        response = subprocess.run(command, capture_output=True, text=True,
                                  timeout=timeout + 3, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise SMSGatewayError(
            "Network request failed. If this was an SMS submission, it might "
            "still have been queued; do not blindly retry."
        ) from exc
    if response.returncode != 0:
        # Avoid including the API token in error output.
        detail = (response.stdout or response.stderr).replace(api, "[REDACTED]")
        raise SMSGatewayError(
            f"Gateway request failed (curl exit {response.returncode}): "
            f"{detail[:400]}. If sending timed out, check before retrying."
        )
    try:
        result = json.loads(response.stdout)
    except ValueError as exc:
        raise SMSGatewayError("Gateway returned invalid JSON") from exc
    if not isinstance(result, dict):
        raise SMSGatewayError("Gateway returned an unexpected response")
    return result


def SEND_SMS(*, phone, message, msg_type="notification", api=None,
             wait=True, wait_timeout=75, poll_interval=3,
             base_url=DEFAULT_BASE_URL):
    """Queue an SMS. api is the Cloudflare CLIENT_API_KEY (required).

    Returns {job_id, status, msg_type}, optionally timed_out=True.
    'submitted' means the modem accepted it, not confirmed delivery.
    msg_type is local metadata; the existing Worker does not store it.
    """
    if not isinstance(api, str) or not api.strip():
        raise SMSGatewayError("Missing API key: pass api=YOUR_CLIENT_API_KEY")
    if not isinstance(phone, str) or not PHONE_RE.fullmatch(phone):
        raise ValueError("phone must be E.164, for example +919876543210")
    if not isinstance(message, str) or not (1 <= len(message) <= 140) or not all(
        32 <= ord(char) <= 126 for char in message
    ):
        raise ValueError("message must be 1-140 printable ASCII characters")
    if msg_type not in VALID_TYPES:
        raise ValueError("msg_type must be otp, notification, or alert")
    if not isinstance(wait, bool):
        raise ValueError("wait must be True or False")
    if wait and (not isinstance(wait_timeout, (int, float)) or wait_timeout <= 0
                 or not isinstance(poll_interval, (int, float)) or poll_interval <= 0):
        raise ValueError("wait_timeout and poll_interval must be positive")
    if not isinstance(base_url, str) or not base_url.startswith("https://"):
        raise ValueError("base_url must be an HTTPS URL")
    base_url = base_url.rstrip("/")
    queued = _request("POST", base_url + "/sms/send", api,
                      {"phone": phone, "message": message})
    job_id = queued.get("job_id")
    if queued.get("success") is not True or not isinstance(job_id, str):
        raise SMSGatewayError("Gateway did not confirm job creation")
    result = {"job_id": job_id, "status": queued.get("status", "queued"),
              "msg_type": msg_type}
    if not wait:
        return result
    deadline = time.monotonic() + wait_timeout
    while True:
        status = _request("GET", base_url + "/sms/status?id=" + quote(job_id, safe=""), api)
        result["status"] = status.get("status", "unknown")
        if result["status"] in {"submitted", "failed", "unknown"}:
            return result
        if time.monotonic() >= deadline:
            result["timed_out"] = True
            return result
        time.sleep(min(poll_interval, max(0, deadline - time.monotonic())))
