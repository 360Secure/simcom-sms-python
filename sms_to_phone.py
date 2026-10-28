"""Simple import compatibility: from sms_to_phone import SEND_SMS."""
from simcom_sms_gateway import SEND_SMS, SMSGatewayError

__all__ = ["SEND_SMS", "SMSGatewayError"]
