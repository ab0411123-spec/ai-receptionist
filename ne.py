import requests
import random
import os

API_KEY = os.getenv("FAST2SMS_API_KEY")

def send_otp(phone_number):
    otp = random.randint(100000, 999999)

    url = "https://www.fast2sms.com/dev/bulkV2"

    payload = {
        "route": "otp",
        "variables_values": str(otp),
        "flash": 0,
        "numbers": phone_number
    }

    headers = {
        "authorization": API_KEY,
        "Content-Type": "application/json"
    }

    response = requests.post(
        url,
        json=payload,
        headers=headers
    )

    if response.status_code == 200:
        print("OTP sent successfully")
        return otp
    else:
        print("OTP sending failed")
        print(response.text)
        return None


# Example
phone = input("Enter phone number: ")

otp = send_otp(phone)

if otp:
    entered = input("Enter OTP: ")

    if entered == str(otp):
        print("Login successful!")
    else:
        print("Invalid OTP!")
        