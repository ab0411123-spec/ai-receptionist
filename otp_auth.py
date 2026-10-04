"""Local OTP authentication."""

import random
import re
import time

OTP_TTL_SEC = 300


def generate_otp(length: int = 6) -> str:
    return "".join(str(random.randint(0, 9)) for _ in range(length))


def normalize_phone(phone: str) -> str:
    digits = re.sub(r"\D", "", phone or "")
    if len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]
    return "91" + digits if len(digits) == 10 else digits


def is_valid_phone(phone: str) -> bool:
    digits = normalize_phone(phone)
    if len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]
    return len(digits) == 10 and digits[0] in "6789"


class OtpSession:
    def __init__(self, expiry_minutes: int = 5):
        self.expiry_minutes = expiry_minutes
        self.code = None
        self.phone = None
        self.expires_at = 0.0
        self.attempts = 0
        self.verification_id = ""

    def issue(self, phone: str) -> str:
        self.phone = normalize_phone(phone)
        self.code = generate_otp()
        self.verification_id = ""
        self.expires_at = time.time() + self.expiry_minutes * 60
        self.attempts = 0

        return self.code

    def verify(self, phone: str, otp: str) -> tuple:
        """Returns (ok: bool, message: str)."""
        if not self.code:
            return False, "Please request an OTP first."
        if time.time() > self.expires_at:
            return False, "OTP expired. Please request a new one."
        if normalize_phone(phone) != self.phone:
            return False, "Phone number does not match the OTP request."
        self.attempts += 1
        if self.attempts > 5:
            return False, "Too many attempts. Request a new OTP."

        if (otp or "").strip() != self.code:
            return False, "Incorrect OTP. Try again."
        # one-time use
        self.code = None
        return True, "Login successful."
