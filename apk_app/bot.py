"""CodeAI college receptionist — English/Malayalam input, Malayalam replies only.

College profile can be edited by Admin and is saved to college_config.json.
"""

from __future__ import annotations

import json
import os
from typing import Optional

from google import genai

API_KEY = os.environ.get(
    "GEMINI_API_KEY",
    "AQ.Ab8RN6IUGhMgX6moVecBt7QBlRfhyVTUi_mrUNnWYwLODQBUGg",
)

# Admin can operate college settings for the whole APK
ADMIN_USER = os.environ.get("CODEAI_ADMIN_USER", "admin")
ADMIN_PASS = os.environ.get("CODEAI_ADMIN_PASS", "admin123")

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "college_config.json")

_client = None

DEFAULT_COLLEGE = {
    "name": "St. Mary's Polytechnic College, Palakkad",
    "name_ml": "സെന്റ് മേരീസ് പോളിടെക്നിക് കോളേജ്, പാലക്കാട്",
    "location": "Palakkad, Kerala, India",
    "location_ml": "പാലക്കാട്, കേരളം, ഇന്ത്യ",
    "principal": "Dr. R. Kumar",
    "principal_ml": "ഡോ. ആർ. കുമാർ",
    "phone": "0484-1234567",
    "email": "info@stmaryspoly.edu.in",
    "office_hours": "9:00 AM – 4:30 PM (Mon–Fri)",
    "office_hours_ml": "രാവിലെ 9:00 – വൈകുന്നേരം 4:30 (തിങ്കൾ–വെള്ളി)",
    "departments": (
        "Computer Science & Engineering (CSE)\n"
        "Electronics & Communication (ECE)\n"
        "Electrical & Electronics (EEE)\n"
        "Mechanical Engineering (ME)\n"
        "Civil Engineering (CE)"
    ),
    "departments_ml": (
        "കമ്പ്യൂട്ടർ സയൻസ് & എഞ്ചിനീയറിംഗ് (CSE)\n"
        "ഇലക്ട്രോണിക്സ് & കമ്മ്യൂണിക്കേഷൻ (ECE)\n"
        "ഇലക്ട്രിക്കൽ & ഇലക്ട്രോണിക്സ് (EEE)\n"
        "മെക്കാനിക്കൽ എഞ്ചിനീയറിംഗ് (ME)\n"
        "സിവിൽ എഞ്ചിനീയറിംഗ് (CE)"
    ),
    "admission_note_ml": "അഡ്മിഷൻ തുറന്നിരിക്കുന്നു. ഫോം റിസപ്ഷൻ കൗണ്ടറിൽ നിന്ന് ലഭിക്കും.",
    "fee_note_ml": "ഫീസ് വിവരങ്ങൾക്ക് അക്കൗണ്ട്സ് വിഭാഗവുമായി ബന്ധപ്പെടുക.",
    "hostel_note_ml": "ഹോസ്റ്റൽ സൗകര്യം ലഭ്യമാണ്. അലോട്ട്മെന്റിന് ഹോസ്റ്റൽ ഓഫീസുമായി ബന്ധപ്പെടുക.",
    "next_holiday_ml": "അടുത്ത അവധി വെള്ളിയാഴ്ചയാണ്.",
    "next_event_ml": "കോളേജ് ടെക് ഫെസ്റ്റ് അടുത്ത മാസം നടക്കും. വിശദവിവരങ്ങൾ നോട്ടീസ് ബോർഡിൽ.",
}

COLLEGE: dict = {}


def _dept_list(raw: str) -> list[str]:
    parts = [p.strip() for p in (raw or "").replace(",", "\n").splitlines()]
    return [p for p in parts if p]


def load_college() -> dict:
    data = dict(DEFAULT_COLLEGE)
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, encoding="utf-8") as f:
                saved = json.load(f)
            if isinstance(saved, dict):
                data.update({k: v for k, v in saved.items() if k in DEFAULT_COLLEGE})
        except (OSError, json.JSONDecodeError):
            pass
    COLLEGE.clear()
    COLLEGE.update(data)
    return COLLEGE


def save_college(updates: dict) -> dict:
    load_college()
    for key in DEFAULT_COLLEGE:
        if key in updates and updates[key] is not None:
            COLLEGE[key] = str(updates[key]).strip()
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(COLLEGE, f, ensure_ascii=False, indent=2)
    return COLLEGE


def verify_admin(username: str, password: str) -> bool:
    return (username or "").strip() == ADMIN_USER and (password or "") == ADMIN_PASS


def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=API_KEY)
    return _client


def _replies() -> dict:
    depts = " · ".join(_dept_list(COLLEGE.get("departments_ml", "")))
    return {
        "admission": COLLEGE["admission_note_ml"],
        "adm": COLLEGE["admission_note_ml"],
        "അഡ്മിഷൻ": COLLEGE["admission_note_ml"],
        "holiday": COLLEGE["next_holiday_ml"],
        "അവധി": COLLEGE["next_holiday_ml"],
        "event": COLLEGE["next_event_ml"],
        "fest": COLLEGE["next_event_ml"],
        "ഇവന്റ്": COLLEGE["next_event_ml"],
        "seat": "കമ്പ്യൂട്ടർ സയൻസ് വിഭാഗത്തിൽ സീറ്റുകൾ ലഭ്യമാണ്. അഡ്മിഷൻസുമായി സ്ഥിരീകരിക്കുക.",
        "cse": "കമ്പ്യൂട്ടർ സയൻസ് വിഭാഗത്തിലേക്ക് സ്വാഗതം. എങ്ങനെ സഹായിക്കാം?",
        "fee": COLLEGE["fee_note_ml"],
        "fees": COLLEGE["fee_note_ml"],
        "ഫീസ്": COLLEGE["fee_note_ml"],
        "hostel": COLLEGE["hostel_note_ml"],
        "ഹോസ്റ്റൽ": COLLEGE["hostel_note_ml"],
        "principal": (
            f"പ്രിൻസിപ്പൽ {COLLEGE['principal_ml']} ആണ്. "
            "കാണാൻ ആദ്യം റിസപ്ഷൻ ഡെസ്കിൽ രജിസ്റ്റർ ചെയ്യുക."
        ),
        "പ്രിൻസിപ്പൽ": (
            f"പ്രിൻസിപ്പൽ {COLLEGE['principal_ml']} ആണ്. "
            "കാണാൻ ആദ്യം റിസപ്ഷൻ ഡെസ്കിൽ രജിസ്റ്റർ ചെയ്യുക."
        ),
        "eee": "ഇഇഇ വിഭാഗത്തിലേക്ക് സ്വാഗതം. എങ്ങനെ സഹായിക്കാം?",
        "ece": "ഇലക്ട്രോണിക്സ് & കമ്മ്യൂണിക്കേഷൻ വിഭാഗത്തിലേക്ക് സ്വാഗതം. എങ്ങനെ സഹായിക്കാം?",
        "contact": (
            f"ഫോൺ: {COLLEGE['phone']}. ഇമെയിൽ: {COLLEGE['email']}. "
            f"സമയം: {COLLEGE['office_hours_ml']}."
        ),
        "phone": f"കോളേജ് ഫോൺ: {COLLEGE['phone']}",
        "department": f"വിഭാഗങ്ങൾ: {depts}",
        "വിഭാഗം": f"വിഭാഗങ്ങൾ: {depts}",
        "hello": (
            f"{COLLEGE['name_ml']}-ലേക്ക് സ്വാഗതം. ഞാൻ CodeAI, നിങ്ങളുടെ AI റിസപ്ഷനിസ്റ്റ്. "
            "എങ്ങനെ സഹായിക്കാം?"
        ),
        "hi": "സ്വാഗതം. ഞാൻ CodeAI, റിസപ്ഷൻ ഡെസ്കിൽ. ഇന്ന് എങ്ങനെ സഹായിക്കാം?",
        "namaste": "നമസ്കാരം. ഞാൻ CodeAI, നിങ്ങളുടെ AI റിസപ്ഷനിസ്റ്റ്. എങ്ങനെ സഹായിക്കാം?",
    }


def keyword_reply(text: str) -> Optional[str]:
    if not text:
        return None
    lower = text.lower()
    for key, answer_ml in _replies().items():
        if key in lower or key in text:
            return answer_ml
    return None


def gemini_reply(text: str, purpose: str = "college") -> str:
    purpose_hint = (
        "Focus on general greetings and navigation help."
        if purpose == "general"
        else (
            "Focus on college facts: admissions, fees, hostel, departments, "
            "principal, holidays, events, contact."
        )
    )
    dept_list = ", ".join(_dept_list(COLLEGE.get("departments_ml", "")))
    context = (
        f"College: {COLLEGE['name_ml']} ({COLLEGE.get('name', '')}). "
        f"Location: {COLLEGE['location_ml']}. "
        f"Principal: {COLLEGE['principal_ml']}. Phone: {COLLEGE['phone']}. "
        f"Email: {COLLEGE['email']}. Hours: {COLLEGE['office_hours_ml']}. "
        f"Departments: {dept_list}. "
        f"Admission: {COLLEGE['admission_note_ml']}. "
        f"Fee: {COLLEGE['fee_note_ml']}. Hostel: {COLLEGE['hostel_note_ml']}."
    )
    prompt = (
        "You are CodeAI, a professional college front-desk AI receptionist. "
        "The visitor may speak or type in English or Malayalam. "
        "Speak warmly (1-3 short spoken sentences, no markdown). "
        "You MUST reply only in Malayalam. "
        f"{purpose_hint} "
        "If unsure, politely ask them to visit the reception counter.\n"
        f"College info: {context}\n\n"
        f"Visitor: {text}\nCodeAI:"
    )
    try:
        response = _get_client().models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        return str(response.text).strip()
    except Exception as e:
        return (
            "ഇപ്പോൾ അസിസ്റ്റന്റ് സേവനം ലഭ്യമല്ല. "
            f"ദയവായി റിസപ്ഷൻ കൗണ്ടർ സന്ദർശിക്കുക. ({e})"
        )


def greeting(name: str) -> str:
    return (
        f"നമസ്കാരം {name}! {COLLEGE['name_ml']}-ലേക്ക് സ്വാഗതം. "
        "ഞാൻ CodeAI, നിങ്ങളുടെ മലയാളം AI റിസപ്ഷനിസ്റ്റ്. "
        "നിങ്ങൾക്ക് ഇംഗ്ലീഷിലോ മലയാളത്തിലോ ചോദിക്കാം; ഞാൻ മലയാളത്തിൽ മറുപടി പറയും. "
        "എങ്ങനെ സഹായിക്കാം?"
    )


def college_overview() -> str:
    depts = " · ".join(_dept_list(COLLEGE.get("departments_ml", "")))
    return (
        f"{COLLEGE['name_ml']}, {COLLEGE['location_ml']}. "
        f"പ്രിൻസിപ്പൽ: {COLLEGE['principal_ml']}. "
        f"ഫോൺ: {COLLEGE['phone']}. സമയം: {COLLEGE['office_hours_ml']}. "
        f"വിഭാഗങ്ങൾ: {depts}."
    )


def bot_reply(text: str, lang_preference: str = "ml", purpose: str = "college"):
    """
    Returns (answer_ml, 'ml').
    lang_preference is kept for call-site compatibility (input language only).
    Spoken/text replies are always Malayalam.
    """
    _ = lang_preference
    if not COLLEGE:
        load_college()
    if not text:
        return "ഞാൻ കേട്ടില്ല. ദയവായി വീണ്ടും ടൈപ്പ് ചെയ്യുക അല്ലെങ്കിൽ സംസാരിക്കുക.", "ml"

    answer = keyword_reply(text)
    if answer:
        return answer, "ml"
    return gemini_reply(text, purpose), "ml"


# Load saved / default college profile on import
load_college()
