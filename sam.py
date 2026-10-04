from __future__ import annotations

import base64
import json
import os
import re
import smtplib
import socket
import tempfile
import random
import threading
import time
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path
from typing import Optional
from urllib.parse import quote

import cv2
import streamlit as st
import streamlit.components.v1 as components


REMINDER_SMTP_SERVER = "smtp.example.com"
REMINDER_SMTP_PORT = 587
REMINDER_SENDER_EMAIL = "sender@example.com"
REMINDER_SENDER_PASSWORD = "your_smtp_password"
REMINDER_DELAY_SECONDS = 60


def _send_scheduled_reminder(recipient_email: str, subject: str, body: str) -> None:
    message = EmailMessage()
    message["Subject"] = f"Reminder: {subject}"
    message["From"] = REMINDER_SENDER_EMAIL
    message["To"] = recipient_email
    message.set_content(body)

    try:
        with smtplib.SMTP(REMINDER_SMTP_SERVER, REMINDER_SMTP_PORT, timeout=20) as server:
            server.starttls()
            server.login(REMINDER_SENDER_EMAIL, REMINDER_SENDER_PASSWORD)
            server.send_message(message)
    except (OSError, smtplib.SMTPException):
        return


def send_email_and_schedule_notification(
    recipient_email: str, subject: str, body: str
) -> bool:
    """Send an email now and schedule a follow-up reminder."""
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = REMINDER_SENDER_EMAIL
    message["To"] = recipient_email
    message.set_content(body)

    try:
        with smtplib.SMTP(REMINDER_SMTP_SERVER, REMINDER_SMTP_PORT, timeout=20) as server:
            server.starttls()
            server.login(REMINDER_SENDER_EMAIL, REMINDER_SENDER_PASSWORD)
            server.send_message(message)
    except (OSError, smtplib.SMTPException):
        return False

    reminder = threading.Timer(
        REMINDER_DELAY_SECONDS,
        _send_scheduled_reminder,
        args=(recipient_email, subject, body),
    )
    reminder.daemon = True
    reminder.start()
    return True


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
        self.code = None
        return True, "Login successful."


# Admin-only gallery of login security photos
ADMIN_USER = os.environ.get("AI_ADMIN_USER", "jinto")
ADMIN_PASS = os.environ.get("AI_ADMIN_PASS", "jinto123")
PHOTO_DIR = Path(__file__).resolve().parent / "security_photos"
_AUTO_CAM_DIR = Path(__file__).resolve().parent / "auto_cam"
_AUTO_CAM = (
    components.declare_component("auto_cam", path=str(_AUTO_CAM_DIR))
    if _AUTO_CAM_DIR.exists()
    else None
)

# ---------------------------------------------------------------------------
# College profile (edit these for your institution)
# ---------------------------------------------------------------------------
COLLEGE = {
    "name": "St.Mary's Polytechnic College, Palakkad",
    "name_ml": "സെന്റ് മേരീസ് പോളിടെക്നിക് കോളേജ്, പാലക്കാട്",
    "location": "Palakkad, Kerala, India",
    "location_ml": "പാലക്കാട്, കേരളം, ഇന്ത്യ",
    "principal": "Mrs.indhukala",
    "principal_ml": "മിസ്സ്.ഇന്ദുകല",
    "phone": "0484-1234567",
    "email": "",
    "website": "www.college.edu.in",
    "office_hours": "9:00 AM – 4:30 PM (Mon–Fri)",
    "office_hours_ml": "രാവിലെ 9:00 – വൈകുന്നേരം 4:30 (തിങ്കൾ–വെള്ളി)",
    "departments": [
        "Computer Engineering (CT)",
        "Automobile Engineering (AU)",
        "Electrical & Electronics Engineering (EEE)",
        "Mechanical Engineering (ME)",
        "Civil Engineering (CE)",
        "fire and safety engineering(FS)",
    ],
    "departments_ml": [
        "കമ്പ്യൂട്ടർ എഞ്ചിനീയറിംഗ് (CT)",
        "ഓട്ടോമൊബൈൽ എഞ്ചിനീയറിംഗ് (AU)",
        "ഇലക്ട്രിക്കൽ & ഇലക്ട്രോണിക്സ് എഞ്ചിനീയറിംഗ് (EEE)",
        "മെക്കാനിക്കൽ എഞ്ചിനീയറിംഗ് (ME)",
        "സിവിൽ എഞ്ചിനീയറിംഗ് (CE)",
    ],
    "admission_note": "Admissions are open. Forms are available at the reception desk.",
    "admission_note_ml": "പ്രവേശനം തുറന്നിരിക്കുന്നു, ലാറ്ററൽ എൻട്രിയും ലഭ്യമാണ്.",
    "hostel_note": "Hostel facilities are available for boys and girls. Please inquire at the hostel office.",
    "fee_note": "For fee information, please contact the accounts section.",
    "fee_note_ml": "ഫീസ് വിവരങ്ങൾക്ക് അക്കൗണ്ട്സ് വിഭാഗവുമായി ബന്ധപ്പെടുക.",
    "next_holiday": "Our next holiday is on Friday. Check the notice board for details.",
    "next_event": "Our college tech fest is coming next month. Check the notice board for more details.",
    "seat_details": "Seat availability varies by department. Contact the admission office for current availability.",
    "seat_details_ml": "സീറ്റ് ലഭ്യത വിഭാഗം അനുസരിച്ച് മാറാം. നിലവിലെ ലഭ്യതയ്ക്ക് അഡ്മിഷൻ ഓഫീസുമായി ബന്ധപ്പെടുക.",
    "eligibility_criteria": "Eligibility criteria are available from the admission office.",
    "eligibility_criteria_ml": "യോഗ്യതാ മാനദണ്ഡങ്ങൾ അഡ്മിഷൻ ഓഫീസിൽ നിന്ന് ലഭിക്കും.",
    "fee_structure": "Fee structure is available from the accounts section.",
    "fee_structure_ml": "ഫീസ് ഘടന അക്കൗണ്ട്സ് വിഭാഗത്തിൽ നിന്ന് ലഭിക്കും.",
    "hostel_note_ml": "ആൺകുട്ടികൾക്കു ഹോസ്റ്റൽ സൗകര്യം ലഭ്യമാണ്. ഹോസ്റ്റൽ ഓഫീസിൽ അന്വേഷിക്കുക.",
    "next_holiday_ml": "അടുത്ത അവധി വെള്ളിയാഴ്ചയാണ്.",
    "next_event_ml": "കോളേജ് ടെക് ഫെസ്റ്റ് അടുത്ത മാസം നടക്കും. വിശദവിവരങ്ങൾ നോട്ടീസ് ബോർഡിൽ പ്രദർശിപ്പിച്ചിട്ടുണ്ട് .",
}

ADMIN_SETTINGS_FILE = Path(__file__).resolve().parent / "admin_settings.json"


def load_admin_settings() -> None:
    defaults = COLLEGE.copy() 
    if not ADMIN_SETTINGS_FILE.exists():
        return
    try:
        saved = json.loads(ADMIN_SETTINGS_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return
    if not isinstance(saved, dict):
        return
    for key, value in saved.items():
        if key in COLLEGE and isinstance(value, type(COLLEGE[key])):
            COLLEGE[key] = value
    for key, value in defaults.items():
        COLLEGE.setdefault(key, value)


def save_admin_settings() -> None:
    ADMIN_SETTINGS_FILE.write_text(
        json.dumps(COLLEGE, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


load_admin_settings()


SMTP_HOST = os.environ.get("VISITOR_SMTP_HOST", "smtp.gmail.com").strip()
SMTP_PORT = int(os.environ.get("VISITOR_SMTP_PORT", "587"))
SMTP_USER = os.environ.get("VISITOR_SMTP_USER", "aitalkbot1@gmail.com").strip()
SMTP_PASSWORD = os.environ.get("VISITOR_SMTP_PASSWORD", "nhtw kuah rlbj ljsu").strip()
SMTP_FROM = os.environ.get("VISITOR_SMTP_FROM", "AI RECEPTIONIST").strip()

EMAIL_CONTACTS = {
    "Principal": os.environ.get("VISITOR_PRINCIPAL_EMAIL", "achuaswin3152@gmail.com").strip(),
    "Vice Principal": os.environ.get("VISITOR_VICE_PRINCIPAL_EMAIL", "nakshathrahhh@gmail.com").strip(),
    "Management": os.environ.get("VISITOR_MANAGEMENT_EMAIL", "ab0411123@gmail.com").strip(),
}

HOD_EMAIL_CONTACTS = {
    department: os.environ.get(
        f"VISITOR_HOD_{re.sub(r'[^A-Z0-9]+', '_', department.upper()).strip('_')}_EMAIL",
        "",
    ).strip()
    for department in COLLEGE["departments"]
}

# Keyword replies for both Malayalam and English
KEYWORD_REPLIES = {
    "ml": {
        "admission": COLLEGE["admission_note_ml"],
        "adm": COLLEGE["admission_note_ml"],
        "അഡ്മിഷൻ": COLLEGE["admission_note_ml"],
        "fee": COLLEGE["fee_note_ml"],
        "fees": COLLEGE["fee_note_ml"],
        "eligibility": COLLEGE["eligibility_criteria_ml"],
        "seat": COLLEGE["seat_details_ml"],
        "seats": COLLEGE["seat_details_ml"],
        "fee structure": COLLEGE["fee_structure_ml"],
        "ഫീസ്": COLLEGE["fee_note_ml"],
        "hostel": COLLEGE["hostel_note_ml"],
        "ഹോസ്റ്റൽ": COLLEGE["hostel_note_ml"],
        "holiday": COLLEGE["next_holiday_ml"],
        "അവധി": COLLEGE["next_holiday_ml"],
        "event": COLLEGE["next_event_ml"],
        "fest": COLLEGE["next_event_ml"],
        "ഇവന്റ്": COLLEGE["next_event_ml"],
        "principal": (
            f"പ്രിൻസിപ്പൽ {COLLEGE['principal_ml']} ആണ്. "
            "കാണാൻ റിസപ്ഷനിൽ രജിസ്റ്റർ ചെയ്യുക."
        ),
        "പ്രിൻസിപ്പൽ": (
            f"പ്രിൻസിപ്പൽ {COLLEGE['principal_ml']} ആണ്. "
            "കാണാൻ റിസപ്ഷനിൽ രജിസ്റ്റർ ചെയ്യുക."
        ),
        "contact": (
            f"ഫോൺ: {COLLEGE['phone']}. സമയം: {COLLEGE['office_hours_ml']}."
        ),
        "phone": f"കോളേജ് ഫോൺ: {COLLEGE['phone']}",
        "department": "വിഭാഗങ്ങൾ: " + ", ".join(COLLEGE["departments_ml"]),
        "വിഭാഗം": "വിഭാഗങ്ങൾ: " + ", ".join(COLLEGE["departments_ml"]),
        "cse": "കമ്പ്യൂട്ടർ  എഞ്ചിനീയറിംഗ് വിഭാഗത്തിലേക്ക് സ്വാഗതം. എങ്ങനെ സഹായിക്കാം?",
        "eee": "ഇലക്ട്രിക്കൽ & ഇലക്ട്രോണിക്സ് എഞ്ചിനീയറിംഗ് വിഭാഗത്തിലേക്ക് സ്വാഗതം. എങ്ങനെ സഹായിക്കാം?",
        "ece": "ഇലക്ട്രോണിക്സ് & കമ്മ്യൂണിക്കേഷൻ എഞ്ചിനീയറിംഗ് വിഭാഗത്തിലേക്ക് സ്വാഗതം. എങ്ങനെ സഹായിക്കാം?",
        "location": f"ഞങ്ങൾ {COLLEGE['location_ml']}യിലാണ് സ്ഥിതി ചെയ്യുന്നത്.",
        "സ്ഥലം": f"ഞങ്ങൾ {COLLEGE['location_ml']}യിലാണ് സ്ഥിതി ചെയ്യുന്നത്.",
    },
    "en": {
        "admission": "Admissions are open, latreal entry also available.",
        "adm": "Admissions are open, latreal entry also available.",
        "fee": "For fee information, please contact the accounts section.",
        "fees": "For fee information, please contact the accounts section.",
        "eligibility": COLLEGE["eligibility_criteria"],
        "seat": COLLEGE["seat_details"],
        "seats": COLLEGE["seat_details"],
        "fee structure": COLLEGE["fee_structure"],
        "hostel": "Hostel facilities are available for boys. Please inquire at the hostel office.",
        "holiday": "Our next holiday is on Friday. Check the notice board for details.",
        "event": "Our college tech fest is coming next month. Check the notice board for more details.",
        "principal": (
            f"Our principal is {COLLEGE['principal']}. "
            "Please register at the reception to meet the principal."
        ),
        "contact": (
            f"Phone: {COLLEGE['phone']}. Hours: {COLLEGE['office_hours']}."
        ),
        "phone": f"College phone: {COLLEGE['phone']}",
        "department": "Departments: " + ", ".join(COLLEGE["departments"]),
        "cse": "Welcome to the Computer engineering department. How can I help you?",
        "eee": "Welcome to the Electrical & Electronics engineering department. How can I help you?",
        "ece": "Welcome to the Automobile engineering department. How can I help you?",
        "location": f"We are located in {COLLEGE['location']}.",
    },
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def speak_for_language(text: str, lang: str = "ml") -> None:
    """Speak the given text in the selected language."""
    if not text:
        return
    try:
        path = os.path.join(tempfile.gettempdir(), "codeai_receptionist.mp3")
        data = b""
        voice = "ml-IN-SobhanaNeural" if lang == "ml" else "en-IN-NeerjaNeural"

        try:
            import asyncio
            import edge_tts

            async def _synth():
                await edge_tts.Communicate(text, voice=voice, rate="-5%").save(path)

            asyncio.run(_synth())
            with open(path, "rb") as f:
                data = f.read()
        except Exception:
            from gtts import gTTS

            gtts_lang = "ml" if lang == "ml" else "en"
            gTTS(text=text, lang=gtts_lang, slow=False).save(path)
            with open(path, "rb") as f:
                data = f.read()

        if not data:
            return
        b64 = base64.b64encode(data).decode()
        components.html(
            f"""
            <audio autoplay>
              <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
            """,
            height=0,
        )
        st.audio(data, format="audio/mp3")
    except Exception as e:
        st.warning(f"Speech unavailable: {e}")


def speak_malayalam(text: str) -> None:
    """Backward-compatible alias for Malayalam output."""
    speak_for_language(text, "ml")


def listen_speech(input_lang: str) -> Optional[str]:
    """
    Capture spoken input.
    input_lang: 'en' or 'ml' — tries preferred language first, then the other.
    """
    try:
        import speech_recognition as sr
    except ImportError:
        st.error("Install SpeechRecognition and PyAudio for voice input.")
        return None

    rec = sr.Recognizer()
    rec.dynamic_energy_threshold = False
    rec.energy_threshold = 400
    rec.pause_threshold = 1.0

    if input_lang == "en":
        order = ("en-IN", "en-US", "ml-IN")
    else:
        order = ("ml-IN", "en-IN", "en-US")

    try:
        with sr.Microphone() as source:
            st.info("🎤 Listening… speak now")
            rec.adjust_for_ambient_noise(source, duration=0.8)
            audio = rec.listen(source, timeout=10, phrase_time_limit=12)

        for code in order:
            try:
                return rec.recognize_google(audio, language=code)
            except sr.UnknownValueError:
                continue
        st.warning("Could not understand. Please try again.")
        return None
    except sr.WaitTimeoutError:
        st.warning("No speech heard.")
        return None
    except sr.RequestError:
        st.error("Internet required for speech recognition.")
        return None
    except Exception as e:
        st.error(f"Microphone error: {e}")
        return None


def keyword_reply(text: str, lang: str = "ml") -> Optional[str]:
    if not text:
        return None
    lower = (text or "").lower().strip()
    lang = "ml" if lang not in ("en", "ml") else lang
    mapping = KEYWORD_REPLIES.get(lang, {})
    for key, answer in mapping.items():
        if key.lower() in lower or key in text:
            return answer
    return None


def get_gemini_client():
    """Create a Gemini client from the configured environment key."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return None

    from google import genai

    return genai.Client(api_key=api_key)


def gemini_reply_for_lang(text: str, purpose: str, lang: str = "ml") -> str:
    lang_name = "Malayalam" if lang == "ml" else "English"
    purpose_hint = (
        "Act as a general-purpose assistant. Answer broad questions clearly and helpfully, ask a brief clarifying question when needed, and do not request or collect visitor login details, name, phone number, or account information unless the user provides them voluntarily. Stay conversational and concise."
        if purpose == "general"
        else (
            "Focus on college facts: admissions, fees, hostel, departments, "
            "principal, holidays, events, contact."
        )
    )
    prompt = (
        "You are AI, a helpful and warm assistant. "
        "The visitor may speak or type in English or Malayalam. "
        f"You MUST reply only in {lang_name} (1–3 short spoken sentences, no markdown). "
        f"{purpose_hint}\n"
        "If the user is in general-purpose mode, do not request visitor login details, name, phone number, or account information. "
        "Instead, answer the general question, ask one clarifying question if needed, and keep the conversation natural.\n"
        f"College info: {context}\n\n"
        f"Visitor: {text}\nAssistant:"
    )
    try:
        client = get_gemini_client()
        if client is None:
            return fallback
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        return str(response.text).strip()
    except Exception as e:
        if lang == "ml":
            return f"ഇപ്പോൾ AI സേവനം ലഭ്യമല്ല. റിസപ്ഷൻ കൗണ്ടർ സന്ദർശിക്കുക. ({e})"
        return f"The AI service is unavailable right now. Please contact the reception desk. ({e})"


def bot_reply(text: str, purpose: str, lang: str = "ml") -> str:
    """Returns a response in the selected language for display + speech."""
    lang = "ml" if lang not in ("en", "ml") else lang
    if not (text or "").strip():
        if lang == "ml":
            return "ദയവായി ഒരു ചോദ്യം ടൈപ്പ് ചെയ്യുക അല്ലെങ്കിൽ സംസാരിക്കുക."

            
        return "Please type or speak a question."

    hit = keyword_reply(text, lang)
    if hit:
        return hit
    return gemini_reply_for_lang(text, purpose, lang)


def greeting_for_lang(name: str, lang: str = "ml") -> str:
    if lang == "en":
        return (
            f"Hello {name}! Welcome. "
            "I am your AI assistant. "
            "How can I help you today?"
        )
    return (
        f"നമസ്കാരം {name}! സ്വാഗതം. "
        "ഞാൻ നിങ്ങളുടെ AI അസിസ്റ്റന്റാണ്. "
        "എങ്ങനെ സഹായിക്കാം?"
    )


def college_overview_for_lang(lang: str = "ml") -> str:
    if lang == "en":
        departments = " · ".join(COLLEGE["departments"])
        return (
            f"{COLLEGE['name']}, {COLLEGE['location']}. "
            f"Principal: {COLLEGE['principal']}. "
            f"Phone: {COLLEGE['phone']}. Hours: {COLLEGE['office_hours']}. "
            f"Departments: {departments}."
        )
    departments = " · ".join(COLLEGE["departments_ml"])
    return (
        f"{COLLEGE['name_ml']}, {COLLEGE['location_ml']}. "
        f"പ്രിൻസിപ്പൽ: {COLLEGE['principal_ml']}. "
        f"ഫോൺ: {COLLEGE['phone']}. സമയം: {COLLEGE['office_hours_ml']}. "
        f"വിഭാഗങ്ങൾ: {departments}."
    )


def append_and_speak(user_text: Optional[str], answer: str, lang: str = "ml") -> None:
    if user_text is not None:
        st.session_state.messages.append({"role": "user", "content": user_text})
    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.session_state.pending_speak = (answer, lang)


def _safe_token(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_-]+", "_", (value or "").strip())
    return cleaned[:40] or "unknown"


def save_security_photo(image_bytes: bytes, name: str, phone: str) -> Path:
    """Store login photo for admin review only."""
    PHOTO_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = f"{stamp}_{_safe_token(phone)}_{_safe_token(name)}"
    photo_path = PHOTO_DIR / f"{stem}.jpg"
    meta_path = PHOTO_DIR / f"{stem}.json"
    photo_path.write_bytes(image_bytes)
    meta_path.write_text(
        json.dumps(
            {
                "name": name,
                "phone": phone,
                "captured_at": datetime.now().isoformat(timespec="seconds"),
                "photo_file": photo_path.name,
                
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return photo_path


def list_security_photos() -> list[dict]:
    if not PHOTO_DIR.exists():
        return []
    rows = []
    for meta_path in sorted(PHOTO_DIR.glob("*.json"), reverse=True):
        try:
            data = json.loads(meta_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        photo_name = data.get("photo_file") or meta_path.with_suffix(".jpg").name
        photo_path = PHOTO_DIR / photo_name
        if photo_path.exists():
            data["path"] = str(photo_path)
            rows.append(data)
    return rows


def verify_admin(username: str, password: str) -> bool:
    return (username or "").strip() == ADMIN_USER and (password or "") == ADMIN_PASS


VISITOR_REQUESTS_FILE = Path(__file__).resolve().parent / "visitor_requests.json"


def load_visitor_requests() -> list[dict]:
    if not VISITOR_REQUESTS_FILE.exists():
        return []
    try:
        data = json.loads(VISITOR_REQUESTS_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def save_visitor_requests(requests: list[dict]) -> None:
    VISITOR_REQUESTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    VISITOR_REQUESTS_FILE.write_text(
        json.dumps(requests, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _recipient_phone_for_request(request: dict) -> str:
    recipient_type = request.get("recipient_type", "").strip()
    if recipient_type == "HOD Departments":
        department = request.get("department_key", request.get("department", "")).strip()
        return HOD_PHONE_CONTACTS.get(department, "")
    return PHONE_CONTACTS.get(recipient_type, "")


def _recipient_emails_for_request(request: dict) -> list[str]:
    department = request.get("department_key", request.get("department", "")).strip()
    recipients = []
    if request.get("recipient_type", "").strip() == "HOD Departments":
        recipients.append(HOD_EMAIL_CONTACTS.get(department, ""))
    recipients.extend(EMAIL_CONTACTS.values())
    return list(dict.fromkeys(email for email in recipients if email))


def _missing_email_recipients(request: dict) -> list[str]:
    department = request.get("department_key", request.get("department", "")).strip()
    missing = []
    if request.get("recipient_type", "").strip() == "HOD Departments" and not HOD_EMAIL_CONTACTS.get(department, ""):
        missing.append(f"HOD ({department})")
    for role, email in EMAIL_CONTACTS.items():
        if not email:
            missing.append(role)
    return missing


def _missing_email_environment_variables(request: dict) -> list[str]:
    department = request.get("department_key", request.get("department", "")).strip()
    department_key = re.sub(r"[^A-Z0-9]+", "_", department.upper()).strip("_")
    missing = []
    if request.get("recipient_type", "").strip() == "HOD Departments" and not HOD_EMAIL_CONTACTS.get(department, ""):
        missing.append(f"VISITOR_HOD_{department_key}_EMAIL")
    for role, email in EMAIL_CONTACTS.items():
        if not email:
            role_key = re.sub(r"[^A-Z0-9]+", "_", role.upper()).strip("_")
            missing.append(f"VISITOR_{role_key}_EMAIL")
    return missing


def build_visit_request_message(request: dict) -> str:
    recipient_label = request.get("recipient_label") or request.get("recipient_type", "Recipient")
    visitor_phone = request.get("phone", "")
    request_id = request.get("id", "")
    base_url = (os.environ.get("APP_BASE_URL", "https://example.com") or "https://example.com").strip().rstrip("/")
    approval_link = f"{base_url}/visitor-approve?id={quote(request_id)}" if request_id else f"{base_url}/visitor-approve"
    return (
        f"Visitor Management Request\n"
        f"To: {recipient_label}\n"
        f"Visitor Name: {request.get('name', 'Unknown')}\n"
        f"Visitor Phone: {visitor_phone}\n"
        f"Reason for Visit: {request.get('reason', 'Not provided')}\n"
        f"Approval Link: {approval_link}\n\n"
        "Reply with APPROVE or DENY."
    )


def send_visit_request_email(request: dict, body: str) -> tuple[bool, str]:
    if not SMTP_HOST or not SMTP_FROM:
        return False, "Email is not configured. Set VISITOR_SMTP_HOST and VISITOR_SMTP_FROM."

    missing = _missing_email_recipients(request)
    if missing:
        return False, "Missing email configuration for: " + ", ".join(missing)

    recipients = _recipient_emails_for_request(request)
    message = EmailMessage()
    message["Subject"] = f"Visitor request: {request.get('name', 'Unknown')}"
    message["From"] = SMTP_FROM
    message["To"] = ", ".join(recipients)
    message.set_content(body)

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as server:
            server.starttls()
            if SMTP_USER and SMTP_PASSWORD:
                server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(message)
    except socket.gaierror as error:
        return (
            False,
            f"Email notification failed: could not resolve SMTP host '{SMTP_HOST}'. "
            "Check VISITOR_SMTP_HOST and DNS/network access. "
            f"Details: {error}",
        )
    except (OSError, smtplib.SMTPException) as error:
        return False, f"Email notification failed: {error}"
    return True, f"Email notification sent to {len(recipients)} recipients."


def save_request_notification(request: dict, body: str) -> tuple[bool, str]:
    request["notification_message"] = body
    return True, "Request saved for reception review."


def handle_visit_decision(request_id: str, approved: bool) -> tuple[bool, str]:
    requests = load_visitor_requests()
    request = next((item for item in requests if item.get("id") == request_id), None)
    if request is None:
        return False, "Request not found."

    request["status"] = "approved" if approved else "rejected"
    request["decision_at"] = datetime.now().isoformat(timespec="seconds")
    if approved:
        request["decision_note"] = "Approved by recipient"
    else:
        request["decision_note"] = "Rejected by recipient"

    decision_message = (
        f"Your visit request to {request.get('recipient_label', request.get('recipient_type', 'the requested office'))} has been approved. "
        "Please report to the reception desk for further assistance."
        if approved
        else (
            f"Your visit request to {request.get('recipient_label', request.get('recipient_type', 'the requested office'))} has been rejected. "
            "Please contact the reception desk for alternate arrangements."
        )
    )

    ok, detail = save_request_notification(request, decision_message)
    request["visitor_response_message"] = detail
    save_visitor_requests(requests)
    return ok, detail


def capture_with_streamlit_camera() -> Optional[bytes]:
    """
    Capture image using Streamlit's built-in camera_input widget.
    Works on both desktop and mobile browsers (uses device's camera).
    Returns bytes of the captured image, or None if cancelled.
    """
    st.markdown("### 📷 Capture Your Photo")
    st.info(
        "Use your device's camera to capture a photo for security verification. "
        "Click the camera button, take a clear photo, and submit."
    )
    
    picture = st.camera_input(
        "Take a picture",
        key="security_camera_input",
        disabled=st.session_state.get("photo_saved", False),
    )
    
    if picture is not None:
        # st.camera_input returns a BytesIO object
        image_bytes = picture.getvalue()
        return image_bytes if image_bytes else None
    
    return None


def auto_capture_webcam() -> Optional[bytes]:
    """
    Capture one frame from the local webcam using OpenCV (desktop only, no Take Photo button).
    Falls back to st.camera_input if OpenCV is unavailable.
    """
    try:
        import time

        import cv2
    except ImportError:
        return None

    cap = None
    try:
        # CAP_DSHOW is more reliable on Windows
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap.release()
            cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            return None
        for _ in range(8):
            cap.read()
            time.sleep(0.04)
        ok, frame = cap.read()
        if not ok or frame is None:
            return None
        ok, buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
        return buf.tobytes() if ok else None
    except Exception:
        return None
    finally:
        if cap is not None:
            cap.release()


def browser_auto_capture() -> Optional[str]:
    """
    Browser webcam auto-capture via custom component when available.
    Returns a data-URL string, an error JSON string, or None while waiting.
    OS/browser may still show a one-time camera permission dialog (cannot be skipped).
    """
    if _AUTO_CAM is None:
        return None
    return _AUTO_CAM(key="security_auto_cam", default=None)


def bytes_from_data_url(data_url: str) -> Optional[bytes]:
    if not data_url or not isinstance(data_url, str):
        return None
    if data_url.startswith("{") and "error" in data_url:
        return None
    if "," not in data_url:
        return None
    try:
        return base64.b64decode(data_url.split(",", 1)[1])
    except Exception:
        return None


def init_state() -> None:
    defaults = {
        "step": "login",  # login | security_photo | language | purpose | chat | admin
        "user": "",
        "phone": "",
        "otp_sent": False,
        "demo_otp": "",
        "input_lang": "ml",  # en | ml — for typing hints + speech recognition
        "purpose": "college",
        "messages": [],
        "pending_speak": None,
        "photo_saved": False,
        "photo_notice": False,
        "photo_opencv_tried": False,
        "camera_capture_method": None,  # "streamlit" | "opencv" | "browser"
        "is_admin": False,
        "login_tab": "Visitor",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
    if "otp_session" not in st.session_state:
        st.session_state.otp_session = OtpSession()
THEME_CSS = """
<style>
  :root {
    --gold: #e8ae35;
    --gold-light: #ffe28a;
    --gold-dark: #8f631c;
  }
  .stApp {
    background:
      radial-gradient(circle at 70% 50%, rgba(212, 151, 35, 0.10), transparent 32%),
      radial-gradient(circle at 20% 50%, rgba(255, 190, 50, 0.06), transparent 32%),
      #050505 !important;
    color: #f5f5f5 !important;
  }
  .stApp::before {
    content: "";
    position: fixed;
    inset: 0;
    pointer-events: none;
    opacity: 0.12;
    background-image:
      linear-gradient(90deg, transparent 98%, #b98020 98%),
      linear-gradient(0deg, transparent 98%, #b98020 98%);
    background-size: 100px 100px;
    mask-image: radial-gradient(circle, black, transparent 72%);
    z-index: 0;
  }
  html, body, [class*="css"], p, span, label, div, li,
  .stMarkdown, .stMarkdown p, .stMarkdown span,
  .stCaption, [data-testid="stCaptionContainer"],
  [data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] p,
  [data-testid="stText"], h1, h2, h3, h4, h5, h6 {
    color: #f3f3f3 !important;
    font-weight: 600 !important;
  }
  .stTitle, [data-testid="stHeading"] h1,
  [data-testid="stHeading"] h2, [data-testid="stHeading"] h3 {
    color: #e8b642 !important;
    font-weight: 800 !important;
  }
  [data-testid="stCaptionContainer"], .stCaption {
    color: #aaa !important;
  }
  .block-container {
    padding-top: 1.4rem !important;
    max-width: 1180px !important;
  }
  input, textarea, .stTextInput input, .stChatInput textarea,
  [data-baseweb="input"] input, [data-baseweb="textarea"] textarea {
    color: #ffffff !important;
    background: #101010 !important;
    font-weight: 600 !important;
    -webkit-text-fill-color: #ffffff !important;
  }
  [data-baseweb="input"], [data-baseweb="textarea"] {
    background: #101010 !important;
    border: 1px solid rgba(198, 145, 44, 0.45) !important;
    border-radius: 13px !important;
  }
  input::placeholder, textarea::placeholder {
    color: #777777 !important;
    font-weight: 500 !important;
    opacity: 1 !important;
  }
  .stButton > button, .stFormSubmitButton > button {
    color: #171006 !important;
    font-weight: 800 !important;
    border: none !important;
    border-radius: 13px !important;
    background: linear-gradient(90deg, #b97c1e, #f0b83f, #d39224) !important;
    box-shadow: 0 5px 20px rgba(221, 159, 35, 0.18) !important;
  }
  .stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 8px 30px rgba(238, 175, 45, 0.3) !important;
  }
  .stButton > button[kind="secondary"],
  .stButton > button[data-testid="stBaseButton-secondary"] {
    background: #111 !important;
    color: #e8b642 !important;
    border: 1px solid rgba(220, 163, 48, 0.45) !important;
  }
  [data-testid="stChatMessage"] {
    background: rgba(20, 20, 20, 0.92);
    border: 1px solid rgba(225, 169, 57, 0.28);
    border-radius: 16px;
  }
  [data-testid="stChatMessage"] p,
  [data-testid="stChatMessageContent"] p,
  [data-testid="stChatMessageContent"] {
    color: #f5f5f5 !important;
    font-weight: 600 !important;
  }
  .stAlert, .stAlert p, [data-testid="stAlert"] p {
    color: #f5f5f5 !important;
  }
  [data-testid="stRadio"] label,
  [data-testid="stRadio"] p {
    color: #dfbb67 !important;
  }
  .stExpander summary, .stExpander p {
    color: #e8b642 !important;
  }
  [data-testid="stChatInput"] {
    background: #101010 !important;
    border: 1px solid rgba(220, 163, 48, 0.45) !important;
    border-radius: 16px !important;
  }
  .talkbot-hero {
    display: flex;
    align-items: center;
    gap: 14px;
    margin-bottom: 8px;
  }
  .talkbot-logo {
    width: 56px;
    height: 56px;
    border: 3px solid #e8ae35;
    border-radius: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 26px;
    box-shadow: 0 0 15px rgba(239, 178, 53, 0.25);
  }
  .talkbot-name {
    font-size: 26px;
    letter-spacing: 1px;
    color: #fff6c7 !important;
    margin: 0;
  }
  .talkbot-tag {
    color: #ffe28a !important;
    font-size: 13px;
    letter-spacing: 1.2px;
    margin: 2px 0 0 0;
  }
  .talkbot-title {
    font-size: clamp(36px, 5vw, 58px);
    line-height: 0.95;
    margin: 10px 0 0 0;
    background: linear-gradient(180deg, #fff6c7, #e7b33e 45%, #9d6918);
    -webkit-background-clip: text;
    color: transparent !important;
    font-weight: 800 !important;
  }
  .talkbot-line {
    width: 72px;
    height: 4px;
    background: linear-gradient(90deg, #e8ae35, #fff1a7);
    margin: 16px 0 12px;
    box-shadow: 0 0 10px rgba(255, 193, 56, 0.35);
  }
  .talkbot-desc {
    color: #c2c2c2 !important;
    font-size: 16px;
    line-height: 1.5;
    font-weight: 500 !important;
    max-width: 420px;
  }
  .talkbot-feature {
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 10px 0;
    color: #d9b25a !important;
  }
  .talkbot-feature span {
    width: 36px;
    height: 36px;
    border: 1px solid #e8ae35;
    border-radius: 50%;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }
  .talkbot-card {
    border: 1px solid rgba(220, 163, 48, 0.55);
    border-radius: 28px;
    padding: 8px 4px 4px;
    background: linear-gradient(145deg, rgba(25,25,25,0.96), rgba(8,8,8,0.98));
    box-shadow: 0 0 40px rgba(228, 169, 48, 0.08);
  }
  .talkbot-secure {
    margin-top: 18px;
    padding: 14px 16px;
    border: 1px solid rgba(225, 169, 57, 0.35);
    border-radius: 16px;
    background: rgba(20, 20, 20, 0.6);
    color: #dcb55f !important;
    font-size: 14px;
  }
  .campus-map-launch {
    margin: 0 0 18px 0;
    padding: 14px 16px;
    border: 1px solid rgba(225, 169, 57, 0.45);
    border-radius: 18px;
    background: rgba(18, 18, 18, 0.8);
  }
  .campus-map-launch .title {
    margin: 0 0 8px 0;
    color: #f5d98d !important;
    font-size: 20px;
    font-weight: 800;
  }
  .mobile-navigation-frame {
    width: 360px;
    height: 640px;
    margin: 0 auto;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
    border-radius: 18px;
    border: 2px solid #cccccc;
    background: #000;
  }
  .mobile-navigation-frame img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
  }
  @media (max-width: 600px) {
    .mobile-navigation-frame {
      width: min(360px, 92vw);
      height: min(640px, 164vw);
    }
  }
</style>
"""


def render_brand_header(compact: bool = False) -> None:
    if compact:
        st.markdown(
            """
            <div class="talkbot-hero">
              <div class="talkbot-logo">🤖</div>
              <div>
                <p class="talkbot-name">TALKBOT</p>
                <p class="talkbot-tag">AI RECEPTIONIST</p>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return
    st.markdown(
        """
        <div class="talkbot-hero">
          <div class="talkbot-logo">🤖</div>
          <div>
            <p class="talkbot-name">TALKBOT</p>
            <p class="talkbot-tag">AI RECEPTIONIST</p>
          </div>
        </div>
        <p style="color:#f3f3f3;font-size:22px;font-weight:600;margin:18px 0 0;">Welcome to</p>
        <p class="talkbot-title">TALKBOT</p>
        <div class="talkbot-line"></div>
        <p class="talkbot-desc">
          Your intelligent AI receptionist that connects, assists
          and simplifies every interaction.
        </p>
        <div class="talkbot-feature"><span>⚡</span><div><b>Instant Response</b><br><small>Get quick answers</small></div></div>
        <div class="talkbot-feature"><span>♢</span><div><b>Secure &amp; Private</b><br><small>Your data is protected</small></div></div>
        <div class="talkbot-feature"><span>◉</span><div><b>Always Available</b><br><small>24/7 AI Assistance</small></div></div>
        <div class="talkbot-feature"><span>☵</span><div><b>Smart &amp; Friendly</b><br><small>Human-like interaction</small></div></div>
        <div class="talkbot-secure">🔒 Your data is secure and encrypted · We respect your privacy</div>
        """,
        unsafe_allow_html=True,
    )


def logout() -> None:
    for key in (
        "step",
        "user",
        "phone",
        "otp_sent",
        "demo_otp",
        "input_lang",
        "purpose",
        "messages",
        "pending_speak",
        "otp_session",
        "photo_saved",
        "photo_notice",
        "photo_opencv_tried",
        "camera_capture_method",
        "is_admin",
        "login_tab",
    ):
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()


# ---------------------------------------------------------------------------
# Screens
# ---------------------------------------------------------------------------
def screen_login() -> None:
    left, right = st.columns([1.05, 1], gap="large")
    with left:
        render_brand_header(compact=False)

    with right:
        st.markdown('<div class="talkbot-card">', unsafe_allow_html=True)
        st.markdown(
            """
            <div style="text-align:center;margin-bottom:8px;">
              <div class="talkbot-logo" style="margin:0 auto 10px;">🤖</div>
              <h2 style="color:#e8b642 !important;text-align:center;margin:0;">Login to your account</h2>
              <p style="color:#aaa !important;text-align:center;font-weight:500 !important;">Enter your details to continue</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        tab = st.radio(
            "Login as",
            options=["Visitor", "Admin"],
            horizontal=True,
            key="login_tab_radio",
            index=0 if st.session_state.login_tab != "Admin" else 1,
        )
        st.session_state.login_tab = tab

        if tab == "Admin":
            st.caption("Admin · view login security photos")
            admin_user = st.text_input("Username", key="admin_user")
            admin_pass = st.text_input("Password", type="password", key="admin_pass")
            if st.button("Admin sign in", type="primary", use_container_width=True):
                if verify_admin(admin_user, admin_pass):
                    st.session_state.is_admin = True
                    st.session_state.step = "admin"
                    st.rerun()
                else:
                    st.error("Invalid admin username or password.")
            st.caption("Default: admin / pass123")
            st.markdown("</div>", unsafe_allow_html=True)
            return

        name = st.text_input("Full Name", placeholder="Enter your name", key="login_name")
        phone = st.text_input(
            "Mobile Number  ·  +91",
            placeholder="Enter mobile number",
            max_chars=10,
            key="login_phone",
        )

        send = st.button("Send OTP  ➤", type="primary", use_container_width=True)
        if send:
            name_v = (name or "").strip()
            phone_v = (phone or "").strip()
            if not name_v:
                st.error("Please enter your name.")
            elif not is_valid_phone(phone_v):
                st.error("Please enter a valid 10-digit mobile number.")
            else:
                code = st.session_state.otp_session.issue(phone_v)
                st.session_state.user = name_v
                st.session_state.phone = phone_v
                st.session_state.demo_otp = code
                st.session_state.otp_sent = True
                st.toast(f"Demo OTP: {code}", icon="🔐")

        if st.session_state.otp_sent:
            st.caption("Enter the OTP sent to your mobile number.")
            otp = st.text_input(
                "Enter OTP",
                placeholder="6-digit code",
                max_chars=6,
                key="login_otp",
            )
            verify = st.button("→  Verify & Login", use_container_width=True)

            if verify:
                phone_v = (phone or st.session_state.phone or "").strip()
                name_v = (name or st.session_state.user or "").strip()
                ok, msg = st.session_state.otp_session.verify(phone_v, otp or "")
                if not ok:
                    st.error(msg)
                else:
                    st.session_state.user = name_v
                    st.session_state.phone = phone_v
                    st.session_state.photo_saved = False
                    st.session_state.photo_notice = False
                    st.session_state.photo_opencv_tried = False
                    st.session_state.step = "security_photo"
                    st.rerun()

        st.caption("🔒 By continuing, you agree to our Terms & Privacy Policy")
        st.markdown("</div>", unsafe_allow_html=True)


def screen_security_photo() -> None:
    """Capture security photo using best available method (Streamlit camera preferred)."""
    if st.session_state.photo_notice:
        st.success("✅ Your photo is captured for security purposes.")
        if st.button("Continue to next step", type="primary", use_container_width=True):
            st.session_state.step = "language"
            st.rerun()
        return

    st.markdown("### 🔐 Security Verification")
    st.info(
        "A photo will be captured for security and verification purposes. "
        "You can use your device's camera (mobile or desktop). Your data is secure and encrypted."
    )

    # Primary method: Streamlit camera_input (works on all devices)
    image_bytes = capture_with_streamlit_camera()
    if image_bytes:
        save_security_photo(
            image_bytes, st.session_state.user, st.session_state.phone
        )
        st.session_state.photo_saved = True
        st.session_state.camera_capture_method = "streamlit"
        st.session_state.photo_notice = True
        st.rerun()
        return

    # Fallback: OpenCV for auto-capture (desktop only, if Streamlit camera not used)
    if not st.session_state.photo_saved and not st.session_state.photo_opencv_tried:
        st.session_state.photo_opencv_tried = True
        opencv_bytes = auto_capture_webcam()
        if opencv_bytes:
            save_security_photo(
                opencv_bytes, st.session_state.user, st.session_state.phone
            )
            st.session_state.photo_saved = True
            st.session_state.camera_capture_method = "opencv"
            st.session_state.photo_notice = True
            st.rerun()
            return

    # Fallback: Browser auto-capture component
    if not st.session_state.photo_saved and st.session_state.photo_opencv_tried:
        result = browser_auto_capture()
        if result:
            image_bytes = bytes_from_data_url(result)
            if image_bytes:
                save_security_photo(
                    image_bytes, st.session_state.user, st.session_state.phone
                )
                st.session_state.photo_saved = True
                st.session_state.camera_capture_method = "browser"
                st.session_state.photo_notice = True
                st.rerun()
                return
            elif isinstance(result, str) and "error" in result:
                st.session_state.photo_cam_error = result

    if st.session_state.get("photo_cam_error"):
        st.warning("⚠️ Camera unavailable. Check privacy settings and try again.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Retry capture", type="primary", use_container_width=True):
                st.session_state.photo_cam_error = ""
                st.session_state.photo_saved = False
                st.session_state.photo_opencv_tried = False
                st.rerun()
        with col2:
            if st.button("Continue without photo", use_container_width=True):
                st.session_state.step = "language"
                st.rerun()
    else:
        if st.button("Skip photo capture", use_container_width=True):
            st.session_state.step = "language"
            st.rerun()


def screen_admin() -> None:
    if not st.session_state.is_admin:
        st.session_state.step = "login"
        st.rerun()
        return

    top = st.columns([3, 1])
    with top[0]:
        st.markdown("### Admin · Login security photos")
        st.caption("Only admin can view these photos")
    with top[1]:
        if st.button("Logout", use_container_width=True):
            logout()

    st.markdown("### Admin Settings")
    st.caption("Edit the information used by the chatbot. Changes are saved locally and used immediately.")
    with st.form("admin_settings_form"):
        st.markdown("#### College information")
        name = st.text_input("College name", value=COLLEGE["name"])
        name_ml = st.text_input("College name (Malayalam)", value=COLLEGE["name_ml"])
        location = st.text_input("Location", value=COLLEGE["location"])
        location_ml = st.text_input("Location (Malayalam)", value=COLLEGE["location_ml"])
        principal = st.text_input("Principal", value=COLLEGE["principal"])
        principal_ml = st.text_input("Principal (Malayalam)", value=COLLEGE["principal_ml"])
        phone = st.text_input("College phone", value=COLLEGE["phone"])
        website = st.text_input("Website", value=COLLEGE["website"])
        office_hours = st.text_input("Office hours", value=COLLEGE["office_hours"])
        office_hours_ml = st.text_input("Office hours (Malayalam)", value=COLLEGE["office_hours_ml"])

        st.markdown("#### Departments and admissions")
        departments = st.text_area(
            "Departments (one per line)",
            value="\n".join(COLLEGE["departments"]),
            height=120,
        )
        departments_ml = st.text_area(
            "Departments (Malayalam, one per line)",
            value="\n".join(COLLEGE["departments_ml"]),
            height=120,
        )
        admission_note = st.text_area("Admission information", value=COLLEGE["admission_note"], height=80)
        admission_note_ml = st.text_area("Admission information (Malayalam)", value=COLLEGE["admission_note_ml"], height=80)
        eligibility_criteria = st.text_area("Eligibility criteria", value=COLLEGE["eligibility_criteria"], height=100)
        eligibility_criteria_ml = st.text_area("Eligibility criteria (Malayalam)", value=COLLEGE["eligibility_criteria_ml"], height=100)
        seat_details = st.text_area("Seat details", value=COLLEGE["seat_details"], height=100)
        seat_details_ml = st.text_area("Seat details (Malayalam)", value=COLLEGE["seat_details_ml"], height=100)

        st.markdown("#### Fees and other chatbot content")
        fee_note = st.text_area("Fee information", value=COLLEGE["fee_note"], height=80)
        fee_note_ml = st.text_area("Fee information (Malayalam)", value=COLLEGE["fee_note_ml"], height=80)
        fee_structure = st.text_area("Fee structure", value=COLLEGE["fee_structure"], height=100)
        fee_structure_ml = st.text_area("Fee structure (Malayalam)", value=COLLEGE["fee_structure_ml"], height=100)
        hostel_note = st.text_area("Hostel information", value=COLLEGE["hostel_note"], height=80)
        hostel_note_ml = st.text_area("Hostel information (Malayalam)", value=COLLEGE["hostel_note_ml"], height=80)
        next_holiday = st.text_area("Next holiday", value=COLLEGE["next_holiday"], height=60)
        next_holiday_ml = st.text_area("Next holiday (Malayalam)", value=COLLEGE["next_holiday_ml"], height=60)
        next_event = st.text_area("Next event", value=COLLEGE["next_event"], height=60)
        next_event_ml = st.text_area("Next event (Malayalam)", value=COLLEGE["next_event_ml"], height=60)
        save_settings = st.form_submit_button("Save Admin Settings", type="primary", use_container_width=True)

    if save_settings:
        updated_values = {
            "name": name.strip(),
            "name_ml": name_ml.strip(),
            "location": location.strip(),
            "location_ml": location_ml.strip(),
            "principal": principal.strip(),
            "principal_ml": principal_ml.strip(),
            "phone": phone.strip(),
            "website": website.strip(),
            "office_hours": office_hours.strip(),
            "office_hours_ml": office_hours_ml.strip(),
            "departments": [item.strip() for item in departments.splitlines() if item.strip()],
            "departments_ml": [item.strip() for item in departments_ml.splitlines() if item.strip()],
            "admission_note": admission_note.strip(),
            "admission_note_ml": admission_note_ml.strip(),
            "eligibility_criteria": eligibility_criteria.strip(),
            "eligibility_criteria_ml": eligibility_criteria_ml.strip(),
            "seat_details": seat_details.strip(),
            "seat_details_ml": seat_details_ml.strip(),
            "fee_note": fee_note.strip(),
            "fee_note_ml": fee_note_ml.strip(),
            "fee_structure": fee_structure.strip(),
            "fee_structure_ml": fee_structure_ml.strip(),
            "hostel_note": hostel_note.strip(),
            "hostel_note_ml": hostel_note_ml.strip(),
            "next_holiday_ml": next_holiday_ml.strip(),
            "next_holiday": next_holiday.strip(),
            "next_event": next_event.strip(),
            "next_event_ml": next_event_ml.strip(),
        }
        if not updated_values["departments"]:
            st.error("Add at least one department before saving.")
        else:
            COLLEGE.update(updated_values)
            KEYWORD_REPLIES["en"].update(
                {
                    "admission": COLLEGE["admission_note"],
                    "adm": COLLEGE["admission_note"],
                    "fee": f"{COLLEGE['fee_note']} {COLLEGE['fee_structure']}",
                    "fees": f"{COLLEGE['fee_note']} {COLLEGE['fee_structure']}",
                    "hostel": COLLEGE["hostel_note"],
                    "holiday": COLLEGE["next_holiday"],
                    "event": COLLEGE["next_event"],
                    "eligibility": COLLEGE["eligibility_criteria"],
                    "seat": COLLEGE["seat_details"],
                    "seats": COLLEGE["seat_details"],
                    "fee structure": COLLEGE["fee_structure"],
                    "department": "Departments: " + ", ".join(COLLEGE["departments"]),
                    "location": f"We are located in {COLLEGE['location']}.",
                    "principal": f"Our principal is {COLLEGE['principal']}. Please register at the reception to meet the principal.",
                    "contact": f"Phone: {COLLEGE['phone']}. Hours: {COLLEGE['office_hours']}.",
                    "phone": f"College phone: {COLLEGE['phone']}",
                }
            )
            KEYWORD_REPLIES["ml"].update(
                {
                    "admission": COLLEGE["admission_note_ml"],
                    "adm": COLLEGE["admission_note_ml"],
                    "അഡ്മിഷൻ": COLLEGE["admission_note_ml"],
                    "fee": f"{COLLEGE['fee_note_ml']} {COLLEGE['fee_structure_ml']}",
                    "fees": f"{COLLEGE['fee_note_ml']} {COLLEGE['fee_structure_ml']}",
                    "ഫീസ്": COLLEGE["fee_note_ml"],
                    "hostel": COLLEGE["hostel_note_ml"],
                    "ഹോസ്റ്റൽ": COLLEGE["hostel_note_ml"],
                    "അവധി": COLLEGE["next_holiday_ml"],
                    "ഇവന്റ്": COLLEGE["next_event_ml"],
                    "eligibility": COLLEGE["eligibility_criteria_ml"],
                    "seat": COLLEGE["seat_details_ml"],
                    "seats": COLLEGE["seat_details_ml"],
                    "fee structure": COLLEGE["fee_structure_ml"],
                    "department": "വിഭാഗങ്ങൾ: " + ", ".join(COLLEGE["departments_ml"]),
                    "വിഭാഗം": "വിഭാഗങ്ങൾ: " + ", ".join(COLLEGE["departments_ml"]),
                    "location": f"ഞങ്ങൾ {COLLEGE['location_ml']}യിലാണ് സ്ഥിതി ചെയ്യുന്നത്.",
                    "സ്ഥലം": f"ഞങ്ങൾ {COLLEGE['location_ml']}യിലാണ് സ്ഥിതി ചെയ്യുന്നത്.",
                    "principal": f"പ്രിൻസിപ്പൽ {COLLEGE['principal_ml']} ആണ്. കാണാൻ റിസപ്ഷനിൽ രജിസ്റ്റർ ചെയ്യുക.",
                    "പ്രിൻസിപ്പൽ": f"പ്രിൻസിപ്പൽ {COLLEGE['principal_ml']} ആണ്. കാണാൻ റിസപ്ഷനിൽ രജിസ്റ്റർ ചെയ്യുക.",
                    "contact": f"ഫോൺ: {COLLEGE['phone']}. സമയം: {COLLEGE['office_hours_ml']}.",
                    "phone": f"കോളേജ് ഫോൺ: {COLLEGE['phone']}",
                }
            )
            save_admin_settings()
            st.success("Admin settings saved. The chatbot will use the updated information now.")

    st.markdown("### Visitor management requests")
    visitor_requests = load_visitor_requests()
    if visitor_requests:
        for request in visitor_requests:
            status = request.get("status", "pending").title()
            request_label = request.get("recipient_label") or request.get("recipient_type", "Recipient")
            with st.expander(
                f"{request.get('name', 'Visitor')} · {request.get('phone', '')} · {request_label} · {status}",
                expanded=False,
            ):
                st.write(f"**Recipient:** {request_label}")
                st.write(f"**Reason for visit:** {request.get('reason', 'Not provided')}")
                st.write(f"**Requested at:** {request.get('created_at', '')}")
                st.write(f"**Status:** {status}")
                if request.get("visitor_response_message"):
                    st.write(f"**Visitor response status:** {request.get('visitor_response_message')}")

                if request.get("status", "pending") == "pending":
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("Approve", key=f"approve_{request.get('id')}", use_container_width=True):
                            ok, detail = handle_visit_decision(request.get("id"), True)
                            st.success(detail if ok else detail)
                            st.rerun()
                    with c2:
                        if st.button("Deny", key=f"deny_{request.get('id')}", use_container_width=True):
                            ok, detail = handle_visit_decision(request.get("id"), False)
                            st.warning(detail if ok else detail)
                            st.rerun()
    else:
        st.info("No visitor management requests yet.")

    rows = list_security_photos()
    if not rows:
        st.info("No security photos yet.")
        return

    st.write(f"**{len(rows)}** photo(s)")
    for row in rows:
        with st.expander(
            f"{row.get('captured_at', '')} · {row.get('name', '')} · {row.get('phone', '')}",
            expanded=False,
        ):
            st.image(row["path"], use_container_width=True)
            st.json(
                {
                    "name": row.get("name"),
                    "phone": row.get("phone"),
                    "captured_at": row.get("captured_at"),
                    "photo_file": row.get("photo_file"),
                }
            )


CAMPUS_MAP_BASE_DIR = Path(__file__).resolve().parent / "campus_map"
CAMPUS_MAP_VIDEOS_DIR = CAMPUS_MAP_BASE_DIR / "videos"
CAMPUS_MAP_FRAMES_DIR = CAMPUS_MAP_BASE_DIR / "frames"
CAMPUS_MAP_FRAME_INTERVAL = 5.0
CAMPUS_MAP_JPEG_QUALITY = 85

CAMPUS_MAP_ROUTES = {
    "Reception → Office": {
        "video": CAMPUS_MAP_VIDEOS_DIR / "reception_to_office.mp4",
        "frames": CAMPUS_MAP_FRAMES_DIR / "reception_to_office",
        "destination": "College Office",
        "icon": "🏢",
    },
    "Reception → Principal": {
        "video": CAMPUS_MAP_VIDEOS_DIR / "reception_to_principal.mp4",
        "frames": CAMPUS_MAP_FRAMES_DIR / "reception_to_principal",
        "destination": "Principal Office",
        "icon": "👨‍💼",
    },
}


def campus_map_get_existing_frames(frame_folder: Path) -> list[Path]:
    if not frame_folder.exists():
        return []
    frames = list(frame_folder.glob("frame_*.jpg"))
    frames.sort(key=lambda path: int(path.stem.split("_")[-1]))
    return frames


def campus_map_extract_frames(video_path: Path, output_folder: Path, interval_seconds: float = CAMPUS_MAP_FRAME_INTERVAL) -> list[Path]:
    output_folder.mkdir(parents=True, exist_ok=True)
    if not video_path.exists():
        raise FileNotFoundError(f"Video not found:\n{video_path}")

    for old_frame in output_folder.glob("frame_*.jpg"):
        try:
            old_frame.unlink()
        except Exception:
            pass

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video:\n{video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if fps and fps > 0:
        pass
    if fps <= 0:
        fps = 30
    frame_step = max(1, int(round(fps * interval_seconds)))

    frame_paths: list[Path] = []
    frame_number = 0
    saved_number = 1
    progress = st.progress(0, text="Preparing campus map...")

    while True:
        success, frame = cap.read()
        if not success:
            break
        if frame_number % frame_step == 0:
            output_path = output_folder / f"frame_{saved_number:04d}.jpg"
            success_write = cv2.imwrite(str(output_path), frame, [cv2.IMWRITE_JPEG_QUALITY, CAMPUS_MAP_JPEG_QUALITY])
            if success_write:
                frame_paths.append(output_path)
                saved_number += 1
        if total_frames > 0:
            progress.progress(min(frame_number / total_frames, 1.0), text=f"Extracting frames... {frame_number:,} / {total_frames:,}")
        frame_number += 1

    cap.release()
    progress.progress(1.0, text="Frame extraction completed.")
    time.sleep(0.3)
    progress.empty()
    return frame_paths


def campus_map_prepare_route_frames(route_name: str) -> list[Path]:
    route = CAMPUS_MAP_ROUTES[route_name]
    video_path = route["video"]
    frame_folder = route["frames"]

    if not video_path.exists():
        st.error(f"Video file was not found:\n`{video_path}`\nPlease place the MP4 file in the campus_map/videos folder.")
        return []

    existing_frames = campus_map_get_existing_frames(frame_folder)
    if existing_frames:
        return existing_frames

    st.info(f"Preparing navigation frames from `{video_path.name}`...")
    try:
        return campus_map_extract_frames(video_path, frame_folder, CAMPUS_MAP_FRAME_INTERVAL)
    except Exception as error:
        st.error(f"Frame extraction failed:\n\n{error}")
        return []


def screen_campus_map() -> None:
    st.markdown("### 🗺️ Campus Navigation")
    st.caption("Find your way from the reception to your destination.")

    if "campus_map_route_name" not in st.session_state:
        st.session_state.campus_map_route_name = "Reception → Office"
    if "campus_map_current_frame" not in st.session_state:
        st.session_state.campus_map_current_frame = 0
    if "campus_map_frames" not in st.session_state:
        st.session_state.campus_map_frames = []

    route_options = list(CAMPUS_MAP_ROUTES.keys())
    selected_route = st.selectbox("Select destination", route_options, index=route_options.index(st.session_state.campus_map_route_name), key="campus_map_route_selector")

    if st.session_state.campus_map_route_name != selected_route:
        st.session_state.campus_map_route_name = selected_route
        st.session_state.campus_map_current_frame = 0
        st.session_state.campus_map_frames = []

    route = CAMPUS_MAP_ROUTES[selected_route]
    video_path = route["video"]
    frame_folder = route["frames"]
    destination = route["destination"]
    icon = route["icon"]

    st.markdown(
        f"""
        <div class="campus-map-launch">
            <div class="title">{icon} {selected_route}</div>
            <div><b>From:</b> Reception</div>
            <div><b>To:</b> {destination}</div>
            <div><b>Navigation video:</b> {video_path.name}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not video_path.exists():
        st.error(f"❌ Video not found. Expected location: `{video_path}`")
        if st.button("← Back to purpose page", use_container_width=True):
            st.session_state.step = "purpose"
            st.rerun()
        return

    if not st.session_state.campus_map_frames:
        st.session_state.campus_map_frames = campus_map_prepare_route_frames(selected_route)

    frames = st.session_state.campus_map_frames
    if not frames:
        st.error("No navigation frames are available.")
        if st.button("← Back to purpose page", use_container_width=True):
            st.session_state.step = "purpose"
            st.rerun()
        return

    if st.session_state.campus_map_current_frame < 0:
        st.session_state.campus_map_current_frame = 0
    if st.session_state.campus_map_current_frame >= len(frames):
        st.session_state.campus_map_current_frame = len(frames) - 1

    current_index = st.session_state.campus_map_current_frame
    current_frame_path = frames[current_index]

    st.progress((current_index + 1) / len(frames), text=f"Navigation Step {current_index + 1} of {len(frames)}")
    st.markdown('<div style="text-align:center; font-size:21px; font-weight:700; padding:12px;">🚶 Follow this path</div>', unsafe_allow_html=True)

    with open(current_frame_path, "rb") as image_file:
        image_base64 = base64.b64encode(image_file.read()).decode("utf-8")

    st.markdown(
        f"""
        <div class="mobile-navigation-frame">
            <img src="data:image/jpeg;base64,{image_base64}" alt="Navigation frame" />
        </div>
        <div style="text-align:center; margin-top:10px; font-size:16px;">
            {selected_route} • Step {current_index + 1}
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("⬅️ Previous", use_container_width=True, disabled=current_index == 0):
            st.session_state.campus_map_current_frame -= 1
            st.rerun()
    with col2:
        if st.button("🔄 Restart", use_container_width=True):
            st.session_state.campus_map_current_frame = 0
            st.rerun()
    with col3:
        if st.button("Next ➡️", use_container_width=True, disabled=current_index >= len(frames) - 1):
            st.session_state.campus_map_current_frame += 1
            st.rerun()

    if current_index == len(frames) - 1:
        st.success(f"🎯 You have reached {destination}.")

    st.divider()
    st.subheader("🧭 Route Details")
    st.write("**Starting point:** Reception")
    st.write(f"**Destination:** {destination}")
    st.write(f"**Navigation frames:** {len(frames)}")

    if st.button("← Back to visit purpose", use_container_width=True):
        st.session_state.step = "purpose"
        st.rerun()


def screen_language() -> None:
    st.markdown("### Select input language / ഇൻപുട്ട് ഭാഷ")
    st.caption(f"Signed in as **{st.session_state.user}**")
    st.info(
        "Choose the language you will speak or type in. "
        "Replies and spoken audio will match your selection."
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button(
            "English",
            type="primary",
            use_container_width=True,
        ):
            st.session_state.input_lang = "en"
            st.session_state.step = "purpose"
            st.rerun()

    with col2:
        if st.button(
            "മലയാളം (Malayalam)",
            type="primary",
            use_container_width=True,
        ):
            st.session_state.input_lang = "ml"
            st.session_state.step = "purpose"
            st.rerun()

    if st.button("Back", use_container_width=True):
        st.session_state.step = "login"
        st.rerun()


def screen_purpose() -> None:
    input_lang = st.session_state.input_lang

    if input_lang == "ml":
        st.markdown("### സന്ദർശനത്തിന്റെ ഉദ്ദേശ്യം")
        st.caption("നിങ്ങളുടെ സന്ദർശനത്തിന്റെ ഉദ്ദേശ്യം തിരഞ്ഞെടുക്കുക. ആവശ്യമുണ്ടെങ്കിൽ അറിയിപ്പ് വാട്ട്സ്ആപ്പിലേയ്ക്ക് അയക്കും.")
        college_label = "കോളേജ് വിവരങ്ങൾ"
        visitor_management_label = "സന്ദർശകരുടെ മാനേജ്മെന്റ്"
        back_label = "പുറകോട്ട്"
        name_label = " സന്ദർശകരുടെ പേര്"
        phone_label = "ഫോൺ നമ്പർ"
        reason_label = "സന്ദർശനത്തിന്റെ കാരണം"
        send_label = "അയയ്ക്കുക"
        management_label = "മാനേജ്മെന്റ്"
        principal_label = "പ്രിൻസിപ്പൽ"
        vice_principal_label = "വൈസ് പ്രിൻസിപ്പൽ"
        hod_label = "HOD"
        department_label = "വിഭാഗം"
        form_title = "വിവരങ്ങൾ നൽകുക"
        request_success = "നിങ്ങളുടെ അഭ്യർത്ഥന വിജയകരമായി ."
        request_failure = "അഭ്യർത്ഥന അയക്കാൻ കഴിഞ്ഞില്ല."
    else:
        st.markdown("### Purpose of Visitors")
        st.caption("Choose the purpose of your visit and fill in the required details.")
        college_label = "College Information"
        visitor_management_label = "Visitor Management"
        back_label = "Back"
        name_label = "Visitor Name"
        phone_label = "Phone Number"
        reason_label = "Reason for Visit"
        send_label = "Send Request"
        management_label = "Management"
        principal_label = "Principal"
        vice_principal_label = "Vice Principal"
        hod_label = "HOD"
        department_label = "Department"
        form_title = "Visitor Details"
        request_success = "Your request was sent successfully."
        request_failure = "The request could not be sent."

    st.markdown(
        """
        <div class="campus-map-launch">
            <div class="title">🗺️ Campus map</div>
            <div>Open the campus navigation guide to view the reception-to-destination route.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    launch_col, _ = st.columns([1, 3])
    with launch_col:
        if st.button("🗺️ Open Campus Map", type="primary", use_container_width=True, key="campus_map_launch_button"):
            st.session_state.step = "campus_map"
            st.rerun()

    col1, col2 = st.columns(2)

    with col1:
        if st.button(college_label, type="primary", use_container_width=True):
            st.session_state.purpose_choice = "college"
            st.session_state.purpose = "college"
            st.session_state.messages = []
            greet = greeting_for_lang(st.session_state.user, input_lang)
            greet = f"{greet}\n\n{college_overview_for_lang(input_lang)}"
            st.session_state.messages.append({"role": "assistant", "content": greet})
            st.session_state.pending_speak = (greet, input_lang)
            st.session_state.step = "chat"
            st.rerun()

    with col2:
        if st.button(visitor_management_label, type="primary", use_container_width=True):
            st.session_state.purpose_choice = "visitor_management"
            st.session_state.purpose = "visitor_management"
            st.rerun()

    if st.session_state.get("purpose_choice") == "visitor_management":
        st.markdown(f"### {form_title}")
        role = st.radio(
            "Select role" if input_lang == "en" else "റോൾ തിരഞ്ഞെടുക്കുക",
            options=[management_label, principal_label, vice_principal_label, hod_label],
            horizontal=True,
            key="visitor_management_role",
        )

        selected_department = ""
        selected_department_key = ""
        if role == management_label:
            recipient_type = "Management"
            recipient_label = management_label
        elif role == principal_label:
            recipient_type = "Principal"
            recipient_label = principal_label
        elif role == vice_principal_label:
            recipient_type = "Vice Principal"
            recipient_label = vice_principal_label
        else:
            recipient_type = "HOD Departments"
            recipient_label = hod_label

        if role == hod_label:
            selected_department_key = st.selectbox(
                department_label,
                options=COLLEGE["departments"],
                index=0,
                format_func=(
                    lambda department: COLLEGE["departments_ml"][COLLEGE["departments"].index(department)]
                    if input_lang == "ml" and len(COLLEGE["departments_ml"]) == len(COLLEGE["departments"])
                    else department
                ),
                key="visitor_management_department_key",
            )
            selected_department = selected_department_key
            if input_lang == "ml" and len(COLLEGE["departments_ml"]) == len(COLLEGE["departments"]):
                selected_department = COLLEGE["departments_ml"][COLLEGE["departments"].index(selected_department_key)]
        if role == hod_label:
            recipient_label = f"HOD - {selected_department}"

        with st.form("visitor_management_request"):
            name_input = st.text_input(name_label, value=(st.session_state.user or ""), key="vm_name")
            phone_input = st.text_input(phone_label, value=(st.session_state.phone or ""), key="vm_phone", max_chars=10)

            reason_input = st.text_area(reason_label, placeholder=("Enter the reason for visit" if input_lang == "en" else "സന്ദർശനത്തിന്റെ കാരണം നൽകുക"), key="vm_reason", height=130)

            submitted = st.form_submit_button(send_label, type="primary", use_container_width=True)
            if submitted:
                name_v = (name_input or "").strip()
                phone_v = (phone_input or "").strip()
                reason_v = (reason_input or "").strip()
                if not name_v:
                    st.error("Please enter your name." if input_lang == "en" else "സന്ദർശകന്റെ പേര് നൽകണം.")
                elif not is_valid_phone(phone_v):
                    st.error("Please enter a valid 10-digit mobile number." if input_lang == "en" else "ദയവായി 10 അക്കമുള്ള മൊബൈൽ നമ്പർ നൽകുക.")
                elif not reason_v:
                    st.error("Please enter a reason for your visit." if input_lang == "en" else "സന്ദർശനത്തിന്റെ കാരണം നൽകണം.")
                elif _missing_email_recipients(
                    {
                        "recipient_type": recipient_type,
                        "department_key": selected_department_key,
                    }
                ):
                    missing_variables = _missing_email_environment_variables(
                        {
                            "recipient_type": recipient_type,
                            "department_key": selected_department_key,
                        }
                    )
                    st.error(
                        "Email is not configured for all recipients. Set these environment variables: "
                        + ", ".join(missing_variables)
                    )
                else:
                    sending_status = st.empty()
                    sending_status.info("Sending Request...")
                    request = {
                        "id": f"visit_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
                        "name": name_v,
                        "phone": phone_v,
                        "recipient_type": recipient_type,
                        "recipient_label": recipient_label,
                        "department": selected_department,
                        "department_key": selected_department_key,
                        "reason": reason_v,
                        "created_at": datetime.now().isoformat(timespec="seconds"),
                        "status": "pending",
                    }
                    requests = load_visitor_requests()
                    requests.insert(0, request)
                    save_visitor_requests(requests)

                    message = build_visit_request_message(request)
                    email_ok, detail = send_visit_request_email(request, message)
                    request["email_status"] = detail
                    save_ok, save_detail = save_request_notification(request, message)
                    ok = email_ok and save_ok
                    if email_ok and not save_ok:
                        detail = save_detail
                    save_visitor_requests(requests)
                    sending_status.empty()

                    if ok:
                        st.session_state.purpose_choice = ""
                        st.session_state.purpose = ""
                        st.session_state.step = "purpose"
                        st.success(request_success)
                        st.rerun()
                    else:
                        st.warning(detail)

    if st.button(back_label, use_container_width=True):
        st.session_state.purpose_choice = ""
        st.session_state.purpose = ""
        st.session_state.step = "language"
        st.rerun()


def screen_visit_request() -> None:
    """Redirect the retired request screen to the phone-based request flow."""
    st.session_state.step = "purpose"
    st.rerun()


def screen_chat() -> None:
    input_lang = st.session_state.input_lang
    purpose = st.session_state.purpose

    top = st.columns([3, 1])
    with top[0]:
        college_name = COLLEGE['name_ml'] if input_lang == "ml" else COLLEGE['name']
        st.markdown(f"### {college_name}")
        in_label = "മലയാളം ഇൻപുട്ട്" if input_lang == "ml" else "English input"
        purpose_label = (
            "കോളേജ് വിവരങ്ങൾ" if purpose == "college" else "പൊതുവായ ച�ദ്യങ്ങൾ"
        ) if input_lang == "ml" else (
            "College information" if purpose == "college" else "General questions"
        )
        out_label = "🔊 മലയാളം ഔട്ട്പുട്ട്" if input_lang == "ml" else "🔊 English output"
        st.caption(f"{st.session_state.user} · {in_label} · {purpose_label} · {out_label}")
    with top[1]:
        if st.button("Logout", use_container_width=True):
            logout()

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if st.session_state.pending_speak:
        text, speak_lang = st.session_state.pending_speak if isinstance(st.session_state.pending_speak, tuple) else (st.session_state.pending_speak, input_lang)
        st.session_state.pending_speak = None
        speak_for_language(text, speak_lang)

    # Spoken input (English or Malayalam)
    st.subheader("🎤 Speak")
    mic_label = (
        "Speak in Malayalam"
        if input_lang == "ml"
        else "Speak in English"
    )
    if st.button(mic_label, type="primary", use_container_width=True):
        heard = listen_speech(input_lang)
        if heard:
            answer = bot_reply(heard, purpose, input_lang)
            append_and_speak(heard, answer, input_lang)
            st.rerun()

    # Text input
    placeholder = (
        "മലയാളത്തിൽ ചോദ്യം ടൈപ്പ് ചെയ്യുക… (ഉദാ: അഡ്മിഷൻ, ഫീസ്)"
        if input_lang == "ml"
        else "Type in English… (e.g. admission, fees, hostel)"
    )
    user_text = st.chat_input(placeholder)
    if user_text:
        answer = bot_reply(user_text, purpose, input_lang)
        append_and_speak(user_text, answer, input_lang)
        st.rerun()

    with st.expander("Quick topics / സംശയങ്ങൾ"):
        samples = (
            ["അഡ്മിഷൻ", "ഫീസ്", "ഹോസ്റ്റൽ", "അവധി", "പ്രിൻസിപ്പൽ", "വിഭാഗം"]
            if input_lang == "ml"
            else ["admission", "fees", "hostel", "holiday", "principal", "department"]
        )
        cols = st.columns(min(4, len(samples)))
        for i, sample in enumerate(samples):
            if cols[i % len(cols)].button(sample, key=f"q_{sample}"):
                answer = bot_reply(sample, purpose, input_lang)
                append_and_speak(sample, answer, input_lang)
                st.rerun()

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Change purpose", use_container_width=True):
            st.session_state.step = "purpose"
            st.rerun()
    with c2:
        if st.button("Change language", use_container_width=True):
            st.session_state.step = "language"
            st.rerun()


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
def main() -> None:
    st.set_page_config(
        page_title="TALKBOT - AI Receptionist",
        page_icon="🤖",
        layout="wide",
    )
    init_state()
    st.markdown(THEME_CSS, unsafe_allow_html=True)

    step = st.session_state.step
    if step != "login":
        render_brand_header(compact=True)
        st.caption("Input: English / Malayalam · Spoken replies match the selected language")

    if step == "login":
        screen_login()
    elif step == "security_photo":
        screen_security_photo()
    elif step == "admin":
        screen_admin()
    elif step == "language":
        screen_language()
    elif step == "purpose":
        screen_purpose()
    elif step == "campus_map":
        screen_campus_map()
    elif step == "visit_request":
        screen_visit_request()
    else:
        screen_chat()


if __name__ == "__main__":
    main()
