"""Copy and customize this example. Never commit your real API key."""
from sms_to_phone import SEND_SMS, SMSGatewayError

API = "PASTE_YOUR_CLIENT_API_KEY_HERE"
TARGET_PHONE = "+919876543210"
MESSAGE_TEXT = "Hello! This is a test message."
MESSAGE_TYPE = "notification"

try:
    result = SEND_SMS(
        phone=TARGET_PHONE,
        message=MESSAGE_TEXT,
        msg_type=MESSAGE_TYPE,
        api=API,
        wait=True,
    )
    print("Job ID:", result["job_id"])
    print("Status:", result["status"])
except (SMSGatewayError, ValueError) as error:
    print("Error:", error)
