# SIMCom SMS Gateway — Python Client

A lightweight Python client for a **personal ESP32 + SIMCom 4G SMS gateway** backed by a Cloudflare Worker. The ESP32 communicates over cellular; the laptop running Python needs internet access but no connection to the ESP32.

> **Important:** This repository contains only the Python client. It does **not** deploy the Worker, provision Cloudflare D1, or configure the ESP32. You need an already-running gateway and its **CLIENT_API_KEY**. The `api=` parameter is the *secret client API key*, not a public client ID. **Never commit a real API key to GitHub.**

## Install on macOS / Linux / Windows

Install Python 3.9+ and `curl` first (both are commonly available on macOS and Linux). `pip` does not install Python itself. On macOS with Homebrew, install Python with `brew install python` if necessary.

For a fresh project, create a virtual environment:

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install "git+https://github.com/360Secure/simcom-sms-python.git"
```

**Windows PowerShell** (Python, Git and curl must be installed)

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install "git+https://github.com/360Secure/simcom-sms-python.git"
```

Alternatively, download the repository ZIP and install from its extracted folder using `python -m pip install .`.

## Create your own sender.py

```bash
vi sender.py
```

```python
from sms_to_phone import SEND_SMS

API = "YOUR_PRIVATE_CLIENT_API_KEY"
TARGET_PHONE = "+919876543210"
MESSAGE_TEXT = "Hello! Your verification is 48291."
MESSAGE_TYPE = "otp"

result = SEND_SMS(
    phone=TARGET_PHONE,
    message=MESSAGE_TEXT,
    msg_type=MESSAGE_TYPE,
    api=API,
    wait=True,
)
print(result["status"])
```

Run with `python3 sender.py` on macOS/Linux or `python sender.py` on Windows.

If `api` is missing or empty, the function raises `SMSGatewayError` before sending any request. The key is sent in the `Authorization: Bearer` header over HTTPS.

**Recommended for real use:** instead of writing the secret directly into a file, use `API = os.environ["SMS_GATEWAY_CLIENT_KEY"]` after `import os`. Never upload a populated `sender.py` to a public repository.

## API

`SEND_SMS(phone=..., message=..., msg_type="notification", api=..., wait=True, wait_timeout=75, poll_interval=3)`

- `phone`: international E.164 number such as `+919876543210`.
- `message`: 1–140 printable ASCII characters (matches current Worker restrictions).
- `msg_type`: `otp`, `notification`, or `alert`. Currently **local metadata only**; the Worker does not store or enforce it.
- `api`: **required**, the Cloudflare Worker `CLIENT_API_KEY` secret.
- `wait=True`: check job status until `submitted`, `failed`, `unknown`, or timeout.
- Returns a dictionary containing `job_id`, `status`, and `msg_type` (possibly `timed_out`).

`submitted` means the modem/network accepted the SMS, **not** confirmed delivery. SMS messages may be filtered by carriers. A network timeout after sending a POST can leave the job outcome uncertain: do not automatically retry and risk duplicate messages.
