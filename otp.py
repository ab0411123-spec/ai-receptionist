import streamlit as st
import random

# ----------------------------
# Session State
# ----------------------------
if "otp" not in st.session_state:
    st.session_state.otp = ""

st.title("📱 Phone OTP Verification")

phone = st.text_input(
    "Enter Phone Number",
    placeholder=""
)

# ----------------------------
# Send OTP
# ----------------------------
if st.button("Send OTP"):

    if phone == "":
        st.error("Please enter a phone number.")

    else:
        otp = str(random.randint(100000, 999999))
        st.session_state.otp = otp

        st.success(f"Demo OTP: {otp}")

# ----------------------------
# Verify OTP
# ----------------------------
entered_otp = st.text_input("Enter OTP")

if st.button("Verify OTP"):

    if entered_otp == st.session_state.otp:
        st.success("✅ Phone Verified Successfully")
        st.balloons()
    else:
        st.error("❌ Invalid OTP")
        