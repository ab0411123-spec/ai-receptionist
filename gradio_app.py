import base64
import json
import os
import re
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import gradio as gr

try:
    from otp_auth import OtpSession, is_valid_phone
except Exception:  # pragma: no cover
    class OtpSession:
        def __init__(self):
            self.codes = {}

        def issue(self, phone: str) -> str:
            code = "123456"
            self.codes[phone] = code
            return code

        def verify(self, phone: str, otp: str):
            expected = self.codes.get(phone, "")
            return (otp == expected, "Verified successfully." if otp == expected else "Invalid OTP.")

    def is_valid_phone(value: str) -> bool:
        return bool(re.fullmatch(r"\d{10}", (value or "").strip()))


DEFAULT_GEMINI_API_KEY = "AQ.Ab8RN6LhtQdLQRdAx2NnCWq7MWz0hl682Pl5bbvhCEYtVboDfw"
os.environ.setdefault("GEMINI_API_KEY", DEFAULT_GEMINI_API_KEY)

PHOTO_DIR = Path(__file__).resolve().parent / "security_photos"

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
    "admission_note": "Admissions are open. Forms are available at the reception desk.",
    "hostel_note": "Hostel facilities are available for boys and girls. Please inquire at the hostel office.",
    "next_holiday": "Our next holiday is on Friday. Check the notice board for details.",
    "next_event": "Our college tech fest is coming next month. Check the notice board for more details.",
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
    "admission_note_ml": "അഡ്മിഷൻ തുറന്നിരിക്കുന്നു. ഫോം റിസപ്ഷൻ കൗണ്ടറിൽ നിന്ന് ലഭിക്കും.",
    "fee_note": "For fee information, please contact the accounts section.",
    "fee_note_ml": "ഫീസ് വിവരങ്ങൾക്ക് അക്കൗണ്ട്സ് വിഭാഗവുമായി ബന്ധപ്പെടുക.",
    "seat_details": "Seat availability varies by department. Contact the admission office for current availability.",
    "seat_details_ml": "സീറ്റ് ലഭ്യത വിഭാഗം അനുസരിച്ച് മാറാം. നിലവിലെ ലഭ്യതയ്ക്ക് അഡ്മിഷൻ ഓഫീസുമായി ബന്ധപ്പെടുക.",
    "eligibility_criteria": "Eligibility criteria are available from the admission office.",
    "eligibility_criteria_ml": "യോഗ്യതാ മാനദണ്ഡങ്ങൾ അഡ്മിഷൻ ഓഫീസിൽ നിന്ന് ലഭിക്കും.",
    "fee_structure": "Fee structure is available from the accounts section.",
    "fee_structure_ml": "ഫീസ് ഘടന അക്കൗണ്ട്സ് വിഭാഗത്തിൽ നിന്ന് ലഭിക്കും.",
    "hostel_note_ml": "ആൺകുട്ടികൾക്കും പെൺകുട്ടികൾക്കും ഹോസ്റ്റൽ സൗകര്യം ലഭ്യമാണ്. ഹോസ്റ്റൽ ഓഫീസിൽ അന്വേഷിക്കുക.",
    "next_holiday_ml": "അടുത്ത അവധി വെള്ളിയാഴ്ചയാണ്.",
    "next_event_ml": "കോളേജ് ടെക് ഫെസ്റ്റ് അടുത്ത മാസം നടക്കും. വിശദവിവരങ്ങൾ നോട്ടീസ് ബോർഡിൽ.",
}

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
        "principal": f"പ്രിൻസിപ്പൽ {COLLEGE['principal_ml']} ആണ്. കാണാൻ റിസപ്ഷനിൽ രജിസ്റ്റർ ചെയ്യുക.",
        "പ്രിൻസിപ്പൽ": f"പ്രിൻസിപ്പൽ {COLLEGE['principal_ml']} ആണ്. കാണാൻ റിസപ്ഷനിൽ രജിസ്റ്റർ ചെയ്യുക.",
        "contact": f"ഫോൺ: {COLLEGE['phone']}. സമയം: {COLLEGE['office_hours_ml']}.",
        "phone": f"കോളേജ് ഫോൺ: {COLLEGE['phone']}",
        "department": "വിഭാഗങ്ങൾ: " + ", ".join(COLLEGE["departments_ml"]),
        "വിഭാഗം": "വിഭാഗങ്ങൾ: " + ", ".join(COLLEGE["departments_ml"]),
        "location": f"ഞങ്ങൾ {COLLEGE['location_ml']}യിലാണ് സ്ഥിതി ചെയ്യുന്നത്.",
        "സ്ഥലം": f"ഞങ്ങൾ {COLLEGE['location_ml']}യിലാണ് സ്ഥിതി ചെയ്യുന്നത്.",
    },
    "en": {
        "admission": "Admissions are open. Forms are available at the reception desk.",
        "adm": "Admissions are open. Forms are available at the reception desk.",
        "fee": "For fee information, please contact the accounts section.",
        "fees": "For fee information, please contact the accounts section.",
        "eligibility": COLLEGE["eligibility_criteria"],
        "seat": COLLEGE["seat_details"],
        "seats": COLLEGE["seat_details"],
        "fee structure": COLLEGE["fee_structure"],
        "hostel": "Hostel facilities are available for both boys and girls. Please inquire at the hostel office.",
        "holiday": "Our next holiday is on Friday. Check the notice board for details.",
        "event": "Our college tech fest is coming next month. Check the notice board for more details.",
        "principal": f"Our principal is {COLLEGE['principal']}. Please register at the reception to meet the principal.",
        "contact": f"Phone: {COLLEGE['phone']}. Hours: {COLLEGE['office_hours']}.",
        "phone": f"College phone: {COLLEGE['phone']}",
        "department": "Departments: " + ", ".join(COLLEGE["departments"]),
        "location": f"We are located in {COLLEGE['location']}.",
    },
}


def greeting_for_lang(name: str, lang: str = "ml") -> str:
    if lang == "en":
        return (
            f"Hello {name}! Welcome to {COLLEGE['name']}. "
            "I am AI, your English AI receptionist. "
            "You can speak or type in English, and I will reply in English. "
            "How can I help you today?"
        )
    return (
        f"നമസ്കാരം {name}! {COLLEGE['name_ml']}-ലേക്ക് സ്വാഗതം. "
        "ഞാൻ AI, നിങ്ങളുടെ മലയാളം AI റിസപ്ഷനിസ്റ്റ്. "
        "നിങ്ങൾ മലയാളത്തിൽ സംസാരിക്കുകയോ ടൈപ്പ് ചെയ്യുകയോ ചെയ്യാം, ഞാൻ മലയാളത്തിൽ മറുപടി പറയും. "
        "എങ്ങനെ സഹായിക്കാം?"
    )


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


def gemini_reply_for_lang(text: str, purpose: str, lang: str = "ml") -> str:
    lang_name = "Malayalam" if lang == "ml" else "English"
    purpose_hint = (
        "Act as a general-purpose assistant. Answer broad questions clearly and helpfully, ask a brief clarifying question when needed, and do not request or collect visitor login details, name, phone number, or account information unless the user provides them voluntarily. Stay conversational and concise."
        if purpose == "general"
        else "Focus on college facts: admissions, fees, hostel, departments, principal, holidays, events, contact."
    )

    dept_list = ", ".join(COLLEGE["departments_ml"] if lang == "ml" else COLLEGE["departments"])
    email_text = f" Email: {COLLEGE['email']}." if COLLEGE.get("email") else ""
    context = (
        f"College: {COLLEGE['name_ml' if lang == 'ml' else 'name']}. "
        f"Location: {COLLEGE['location_ml' if lang == 'ml' else 'location']}. "
        f"Principal: {COLLEGE['principal_ml' if lang == 'ml' else 'principal']}. "
        f"Phone: {COLLEGE['phone']}.{email_text} "
        f"Hours: {COLLEGE['office_hours_ml' if lang == 'ml' else 'office_hours']}. "
        f"Departments: {dept_list}. "
        f"Admission: {COLLEGE['admission_note_ml' if lang == 'ml' else 'admission_note']} "
        f"Eligibility: {COLLEGE['eligibility_criteria_ml' if lang == 'ml' else 'eligibility_criteria']} "
        f"Seats: {COLLEGE['seat_details_ml' if lang == 'ml' else 'seat_details']} "
        f"Fee information: {COLLEGE['fee_note_ml' if lang == 'ml' else 'fee_note']} "
        f"Fee structure: {COLLEGE['fee_structure_ml' if lang == 'ml' else 'fee_structure']} "
        f"Hostel: {COLLEGE['hostel_note_ml' if lang == 'ml' else 'hostel_note']}"
    )

    fallback = (
        "എനിക്ക് ആ വിവരം കൃത്യമായി അറിയില്ല. ദയവായി റിസപ്ഷൻ കൗണ്ടർ സന്ദർശിക്കുക അല്ലെങ്കിൽ അഡ്മിഷൻ / ഫീസ് / ഹോസ്റ്റൽ പോലുള്ള വിഷയങ്ങൾ ചോദിക്കുക."
        if lang == "ml"
        else "I am not fully sure about that. Please visit the reception desk or ask about admission, fees, hostel, principal, or departments."
    )

    prompt = (
        "You are AI, a helpful and warm assistant. "
        "The visitor may speak or type in English or Malayalam. "
        f"You MUST reply only in {lang_name} (1–3 short spoken sentences, no markdown). "
        f"{purpose_hint}\n"
        "If the user is in general-purpose mode, do not request visitor login details, OTP, name, phone number, or account information. "
        "Instead, answer the general question, ask one clarifying question if needed, and keep the conversation natural.\n"
        f"College info: {context}\n\nVisitor: {text}\nAssistant:"
    )

    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        return fallback

    try:
        from google import genai

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        return str(response.text).strip()
    except Exception:
        return fallback


def bot_reply(text: str, purpose: str, lang: str = "ml") -> str:
    lang = "ml" if lang not in ("en", "ml") else lang
    if not (text or "").strip():
        return "ദയവായി ഒരു ചോദ്യം ടൈപ്പ് ചെയ്യുക അല്ലെങ്കിൽ സംസാരിക്കുക." if lang == "ml" else "Please type or speak a question."
    hit = keyword_reply(text, lang)
    if hit:
        return hit
    return gemini_reply_for_lang(text, purpose, lang)


def build_local_context() -> str:
    return (
        "You are a restricted college information assistant. "
        "You may answer only from the local college context below. "
        "Do not use any external tools, internet access, or API calls. "
        "Do not invent information. If the requested information is not in the context, say that it is not available in the local college information.\n\n"
        f"College name: {COLLEGE['name']} ({COLLEGE['name_ml']})\n"
        f"Location: {COLLEGE['location']} ({COLLEGE['location_ml']})\n"
        f"Principal: {COLLEGE['principal']} ({COLLEGE['principal_ml']})\n"
        f"Phone: {COLLEGE['phone']}\n"
        f"Office hours: {COLLEGE['office_hours']} ({COLLEGE['office_hours_ml']})\n"
        f"Admission: {COLLEGE['admission_note']} / {COLLEGE['admission_note_ml']}\n"
        f"Fees: {COLLEGE['fee_note']} / {COLLEGE['fee_note_ml']}\n"
        f"Fee structure: {COLLEGE['fee_structure']} / {COLLEGE['fee_structure_ml']}\n"
        f"Eligibility: {COLLEGE['eligibility_criteria']} / {COLLEGE['eligibility_criteria_ml']}\n"
        f"Seat details: {COLLEGE['seat_details']} / {COLLEGE['seat_details_ml']}\n"
        f"Hostel: {COLLEGE['hostel_note']} / {COLLEGE['hostel_note_ml']}\n"
        f"Next holiday: {COLLEGE['next_holiday']} / {COLLEGE['next_holiday_ml']}\n"
        f"Next event: {COLLEGE['next_event']} / {COLLEGE['next_event_ml']}\n"
        f"Departments: {', '.join(COLLEGE['departments'])} / {', '.join(COLLEGE['departments_ml'])}"
    )


def local_context_reply(text: str, lang: str = "ml") -> str:
    cleaned = (text or "").strip()
    if not cleaned:
        return "ദയവായി ഒരു ചോദ്യം നൽകുക." if lang == "ml" else "Please provide a question."

    lower = cleaned.lower()
    lang = "ml" if lang not in ("en", "ml") else lang

    direct = keyword_reply(cleaned, lang)
    if direct:
        return direct

    context = build_local_context()
    local_fallback = (
        "This information is not available in the local college context provided to me. "
        "I can only answer using the college information stored in this app."
        if lang == "en"
        else "ഈ માહિતી 제가 ലഭ്യമാക്കിയ ലോക്കൽ കോളേജ് കൺടെക്സ്റ്റിൽ ഇല്ല. ഈ ആപ്പിൽ 저장ിച്ചിട്ടുള്ള കോളേജ് വിവരങ്ങൾ മാത്രം ഉപയോഗിച്ച് ഞാൻ മറുപടി നൽകും."
    )

    if any(word in lower for word in ["hi", "hello", "namaskaram", "good morning", "how are you"]):
        return (
            "Hello! I can answer only from the local college information available in this app."
            if lang == "en"
            else "നമസ്കാരം! ഈ ആപ്പിൽ ലഭ്യമുള്ള കോളേജ് വിവരങ്ങൾ മാത്രം ഉപയോഗിച്ച് ഞാൻ സഹായിക്കും."
        )

    if "contact" in lower or "phone" in lower or "hours" in lower:
        return f"Phone: {COLLEGE['phone']}. Office hours: {COLLEGE['office_hours']}" if lang == "en" else f"ഫോൺ: {COLLEGE['phone']}. സമയം: {COLLEGE['office_hours_ml']}"

    if "department" in lower or "course" in lower or "branches" in lower:
        dept_text = ", ".join(COLLEGE["departments"]) if lang == "en" else ", ".join(COLLEGE["departments_ml"])
        return dept_text

    if "principal" in lower:
        return f"Our principal is {COLLEGE['principal']}" if lang == "en" else f"പ്രിൻസിപ്പൽ {COLLEGE['principal_ml']} ആണ്."

    if "location" in lower or "where" in lower:
        return f"We are located in {COLLEGE['location']}" if lang == "en" else f"ഞങ്ങൾ {COLLEGE['location_ml']}യിൽ positioned ആണെന്ന്." 

    return local_fallback + "\n\nContext summary: " + context[:300]


def gemini_general_reply(text: str, lang: str = "en") -> str:
    if not text or not text.strip():
        return "Please type a question first."
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        return "Gemini API key is not configured."

    try:
        from google import genai

        client = genai.Client(api_key=api_key)
        system = (
            "You are a helpful general-purpose assistant. "
            "Answer user questions clearly and concisely. "
            "Use the current conversation context only and do not claim access to unavailable tools."
        )
        prompt = (
            f"Reply in {'English' if lang == 'en' else 'Malayalam'}. "
            f"System instructions: {system}\n\nUser: {text}"
        )
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        return str(response.text).strip()
    except Exception as exc:
        return f"Gemini is unavailable right now: {exc}"


def speak_for_language(text: str, lang: str = "ml") -> bytes:
    if not text:
        return b""
    try:
        import asyncio
        import edge_tts

        voice = "ml-IN-SobhanaNeural" if lang == "ml" else "en-IN-NeerjaNeural"
        path = os.path.join(tempfile.gettempdir(), f"talkbot_{lang}.mp3")

        async def _generate() -> None:
            await edge_tts.Communicate(text, voice=voice, rate="-5%").save(path)

        asyncio.run(_generate())
        with open(path, "rb") as f:
            return f.read()
    except Exception:
        try:
            from gtts import gTTS

            path = os.path.join(tempfile.gettempdir(), f"talkbot_{lang}_fallback.mp3")
            gTTS(text=text, lang="ml" if lang == "ml" else "en", slow=False).save(path)
            with open(path, "rb") as f:
                return f.read()
        except Exception:
            return b""


def _safe_token(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_-]+", "_", (value or "").strip())
    return cleaned[:40] or "unknown"


def save_security_photo(image: Any, name: str, phone: str) -> str:
    PHOTO_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = f"{stamp}_{_safe_token(phone)}_{_safe_token(name)}"
    path = PHOTO_DIR / f"{stem}.jpg"

    if hasattr(image, "read"):
        image_bytes = image.read()
    elif isinstance(image, str):
        if "," in image:
            image_bytes = base64.b64decode(image.split(",", 1)[1])
        else:
            image_bytes = b""
    else:
        image_bytes = b""

    if not image_bytes:
        return str(path)

    path.write_bytes(image_bytes)
    meta = PHOTO_DIR / f"{stem}.json"
    meta.write_text(json.dumps({"name": name, "phone": phone, "captured_at": datetime.now().isoformat(timespec="seconds")}, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(path)


DEFAULT_STATE = {
    "step": "login",
    "user": "",
    "phone": "",
    "otp_sent": False,
    "demo_otp": "",
    "input_lang": "ml",
    "purpose": "college",
    "messages": [],
    "photo_saved": False,
    "photo_path": "",
}


def make_state() -> Dict[str, Any]:
    return DEFAULT_STATE.copy()


def send_otp_click(name: str, phone: str, state: Dict[str, Any]):
    if not (name or "").strip():
        return state, "Please enter your name.", gr.update(visible=True)
    if not is_valid_phone(phone or ""):
        return state, "Please enter a valid 10-digit mobile number.", gr.update(visible=True)

    otp_session = OtpSession()
    code = otp_session.issue((phone or "").strip())
    state["user"] = (name or "").strip()
    state["phone"] = (phone or "").strip()
    state["otp_sent"] = True
    state["demo_otp"] = code
    msg = f"OTP sent to +91 {state['phone'][-10:]}. Demo OTP: **{code}**"
    return state, msg, gr.update(visible=True)


def verify_otp_click(name: str, phone: str, otp: str, state: Dict[str, Any]):
    if not state.get("otp_sent"):
        return state, "Please send OTP first.", gr.update(visible=True)

    otp_session = OtpSession()
    ok, detail = otp_session.verify((phone or state.get("phone") or "").strip(), (otp or "").strip())
    if not ok:
        return state, detail, gr.update(visible=True)

    state["user"] = (name or state.get("user") or "").strip()
    state["phone"] = (phone or state.get("phone") or "").strip()
    state["step"] = "security_photo"
    state["photo_saved"] = False
    state["photo_path"] = ""
    return state, "OTP verified. Please capture your security photo.", gr.update(visible=True)


def save_photo_click(photo: Any, state: Dict[str, Any]):
    if photo is None:
        return state, "No photo captured yet.", gr.update(visible=True)
    photo_path = save_security_photo(photo, state.get("user", "Visitor"), state.get("phone", ""))
    state["photo_saved"] = True
    state["photo_path"] = photo_path
    state["step"] = "language"
    return state, "Security photo saved successfully.", gr.update(visible=True)


def set_language(lang: str, state: Dict[str, Any]):
    state["input_lang"] = lang
    state["step"] = "purpose"
    return state, "Language selected.", gr.update(visible=True)


def set_purpose(choice: str, state: Dict[str, Any]):
    state["purpose"] = choice
    state["step"] = "chat"
    if choice == "college":
        greet = greeting_for_lang(state.get("user", "Visitor"), state.get("input_lang", "ml"))
        overview = (
            f"{COLLEGE['name_ml' if state['input_lang'] == 'ml' else 'name']}, {COLLEGE['location_ml' if state['input_lang'] == 'ml' else 'location']}. "
            f"Principal: {COLLEGE['principal_ml' if state['input_lang'] == 'ml' else 'principal']}. "
            f"Phone: {COLLEGE['phone']}. Hours: {COLLEGE['office_hours_ml' if state['input_lang'] == 'ml' else 'office_hours']}. "
            f"Departments: {' · '.join(COLLEGE['departments_ml'] if state['input_lang']=='ml' else COLLEGE['departments'])}."
        )
        state["messages"] = [{"role": "assistant", "content": greet + "\n\n" + overview}]
    else:
        state["messages"] = [{"role": "assistant", "content": greeting_for_lang(state.get("user", "Visitor"), state.get("input_lang", "ml"))}]
    return state, "", gr.update(visible=True)


def chat_submit(message: str, state: Dict[str, Any]):
    if not message or not message.strip():
        return state, "", None, "Please type a question first."
    answer = bot_reply(message.strip(), state.get("purpose", "college"), state.get("input_lang", "ml"))
    state["messages"] = state.get("messages", []) + [{"role": "user", "content": message.strip()}, {"role": "assistant", "content": answer}]
    return state, "", None, answer


def quick_topic_click(sample: str, state: Dict[str, Any]):
    answer = bot_reply(sample, state.get("purpose", "college"), state.get("input_lang", "ml"))
    state["messages"] = state.get("messages", []) + [{"role": "user", "content": sample}, {"role": "assistant", "content": answer}]
    return state, answer


def speak_now_click(state: Dict[str, Any]):
    last = state.get("messages", [])
    if not last:
        return state, b"", "No message to speak yet."
    text = last[-1].get("content", "")
    audio = speak_for_language(text, state.get("input_lang", "ml"))
    return state, audio, "Audio generated."


CSS = """
body { background: #0f172a; }
.gradio-container { max-width: 1200px !important; }
.panel { border: 1px solid rgba(255,255,255,0.08); border-radius: 18px; padding: 18px; background: rgba(15, 23, 42, 0.9); }
.hero { font-size: 2.3rem; font-weight: 800; color: #fbbf24; }
.sub { color: #cbd5e1; }
.warning { color: #f59e0b; font-weight: 600; }
"""


with gr.Blocks(css=CSS, title="TALKBOT Gradio Demo") as demo:
    state = gr.State(value=make_state())

    with gr.Tab("Gemini General Questions"):
        gr.Markdown("## Gemini General Assistant")
        gr.Markdown("This tab uses the Gemini API with standard system instructions for general questions.")
        gemini_input = gr.Textbox(label="Ask a question", placeholder="Type any general question here...")
        gemini_submit = gr.Button("Ask Gemini")
        gemini_output = gr.Textbox(label="Answer", lines=10)

        def run_gemini(question: str):
            if not question or not question.strip():
                return "Please type a question first."
            return gemini_general_reply(question, lang="en")

        gemini_submit.click(run_gemini, inputs=[gemini_input], outputs=[gemini_output])

    with gr.Tab("Local College Info Only"):
        gr.Markdown("## Restricted Local College Assistant")
        gr.Markdown("This tab never uses Gemini or any external API. It answers only from the local college context provided in the app.")
        local_input = gr.Textbox(label="Ask about college information", placeholder="Examples: admission, fee, hostel, principal, department")
        local_submit = gr.Button("Ask Local Context")
        local_output = gr.Textbox(label="Answer", lines=10)

        def run_local(question: str):
            return local_context_reply(question, lang="en")

        local_submit.click(run_local, inputs=[local_input], outputs=[local_output])

if __name__ == "__main__":
    demo.launch(debug=True)
