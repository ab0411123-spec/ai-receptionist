"""Simple OTP auth for reception login (demo-ready).

OTP is generated locally and shown in the app for testing.
"""

import random
import time

# OTP valid for 5 minutes
OTP_TTL_SEC = 300


def generate_otp(length: int = 6) -> str:
    return "".join(str(random.randint(0, 9)) for _ in range(length))


def normalize_phone(phone: str) -> str:
    digits = "".join(ch for ch in (phone or "") if ch.isdigit())
    if len(digits) == 10:
        return "91" + digits
    return digits


def is_valid_phone(phone: str) -> bool:
    digits = "".join(ch for ch in (phone or "") if ch.isdigit())
    return len(digits) in (10, 12) and (len(digits) != 12 or digits.startswith("91"))


class OtpSession:
    def __init__(self):
        self.code = None
        self.phone = None
        self.expires_at = 0.0
        self.attempts = 0

    def issue(self, phone: str) -> str:
        self.phone = normalize_phone(phone)
        self.code = generate_otp()
        self.expires_at = time.time() + OTP_TTL_SEC
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
