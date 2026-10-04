"""College AI Receptionist — keywords + Gemini (language-aware)."""

import os

from google import genai

from speech import is_malayalam, resolve_lang

API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

_client = None

# Each entry: English reply, Malayalam reply
REPLIES = {
    "admission": (
        "Admissions are open now. You may collect the form from the reception counter.",
        "അഡ്മിഷൻ ഇപ്പോൾ ആരംഭിച്ചിരിക്കുകയാണ്. ഫോം റിസപ്ഷൻ കൗണ്ടറിൽ നിന്ന് ലഭിക്കും.",
    ),
    "adm": (
        "Admissions are open now. You may collect the form from the reception counter.",
        "അഡ്മിഷൻ ഇപ്പോൾ ആരംഭിച്ചിരിക്കുകയാണ്. ഫോം റിസപ്ഷൻ കൗണ്ടറിൽ നിന്ന് ലഭിക്കും.",
    ),
    "അഡ്മിഷൻ": (
        "Admissions are open now. You may collect the form from the reception counter.",
        "അഡ്മിഷൻ ഇപ്പോൾ ആരംഭിച്ചിരിക്കുകയാണ്. ഫോം റിസപ്ഷൻ കൗണ്ടറിൽ നിന്ന് ലഭിക്കും.",
    ),
    "holiday": (
        "The next holiday is on Friday. Classes will resume as scheduled afterward.",
        "അടുത്ത അവധി വെള്ളിയാഴ്ചയാണ്. അതിനുശേഷം ക്ലാസുകൾ പതിവുപോലെ നടക്കും.",
    ),
    "അവധി": (
        "The next holiday is on Friday. Classes will resume as scheduled afterward.",
        "അടുത്ത അവധി വെള്ളിയാഴ്ചയാണ്.",
    ),
    "event": (
        "Our college tech fest is planned for next month. Details will be on the notice board.",
        "കോളേജ് ടെക് ഫെസ്റ്റ് അടുത്ത മാസം നടക്കും. വിശദവിവരങ്ങൾ നോട്ടീസ് ബോർഡിൽ ലഭ്യമാകും.",
    ),
    "fest": (
        "Our college tech fest is planned for next month. Details will be on the notice board.",
        "കോളേജ് ടെക് ഫെസ്റ്റ് അടുത്ത മാസം നടക്കും. വിശദവിവരങ്ങൾ നോട്ടീസ് ബോർഡിൽ ലഭ്യമാകും.",
    ),
    "ഇവന്റ്": (
        "Our college tech fest is planned for next month. Details will be on the notice board.",
        "കോളേജ് ടെക് ഫെസ്റ്റ് അടുത്ത മാസം നടക്കും. വിശദവിവരങ്ങൾ നോട്ടീസ് ബോർഡിൽ ലഭ്യമാകും.",
    ),
    "seat": (
        "Seats are available in the Computer Science department. Please confirm with admissions.",
        "കമ്പ്യൂട്ടർ സയൻസ് വിഭാഗത്തിൽ സീറ്റുകൾ ലഭ്യമാണ്. അഡ്മിഷൻസുമായി സ്ഥിരീകരിക്കുക.",
    ),
    "cse": (
        "Welcome to the Computer Science department. How may I assist you today?",
        "കമ്പ്യൂട്ടർ സയൻസ് വിഭാഗത്തിലേക്ക് സ്വാഗതം. എങ്ങനെ സഹായിക്കാം?",
    ),
    "fee": (
        "For fee details, please contact the accounts section at the reception wing.",
        "ഫീസ് വിവരങ്ങൾക്ക് അക്കൗണ്ട്സ് വിഭാഗവുമായി ബന്ധപ്പെടുക.",
    ),
    "ഫീസ്": (
        "For fee details, please contact the accounts section at the reception wing.",
        "ഫീസ് വിവരങ്ങൾക്ക് അക്കൗണ്ട്സ് വിഭാഗവുമായി ബന്ധപ്പെടുക.",
    ),
    "hostel": (
        "Hostel facilities are available. Please inquire at the hostel office for allotment.",
        "ഹോസ്റ്റൽ സൗകര്യം ലഭ്യമാണ്. അലോട്ട്മെന്റിന് ഹോസ്റ്റൽ ഓഫീസുമായി ബന്ധപ്പെടുക.",
    ),
    "ഹോസ്റ്റൽ": (
        "Hostel facilities are available. Please inquire at the hostel office for allotment.",
        "ഹോസ്റ്റൽ സൗകര്യം ലഭ്യമാണ്. അലോട്ട്മെന്റിന് ഹോസ്റ്റൽ ഓഫീസുമായി ബന്ധപ്പെടുക.",
    ),
    "principal": (
        "To meet the principal, please register at the reception desk first.",
        "പ്രിൻസിപ്പലിനെ കാണാൻ ആദ്യം റിസപ്ഷൻ ഡെസ്കിൽ രജിസ്റ്റർ ചെയ്യുക.",
    ),
    "eee": (
        "Welcome to the EEE department. How may I assist you today?",
        "ഇഇഇ വിഭാഗത്തിലേക്ക് സ്വാഗതം. എങ്ങനെ സഹായിക്കാം?",
    ),
    "hello": (
        "Welcome to our college. I am Asha, your AI receptionist. How may I help you?",
        "കോളേജിലേക്ക് സ്വാഗതം. ഞാൻ ആശ, നിങ്ങളുടെ AI റിസപ്ഷനിസ്റ്റ്. എങ്ങനെ സഹായിക്കാം?",
    ),
    "hi": (
        "Welcome. I am Asha at the reception desk. How can I help you today?",
        "സ്വാഗതം. ഞാൻ ആശ, റിസപ്ഷൻ ഡെസ്കിൽ. ഇന്ന് എങ്ങനെ സഹായിക്കാം?",
    ),
    "namaste": (
        "Welcome. I am Asha, your AI receptionist. How may I help you?",
        "നമസ്കാരം. ഞാൻ ആശ, നിങ്ങളുടെ AI റിസപ്ഷനിസ്റ്റ്. എങ്ങനെ സഹായിക്കാം?",
    ),
}


def _get_client():
    global _client
    if _client is None:
        if not API_KEY:
            raise RuntimeError("GEMINI_API_KEY is not configured.")
        _client = genai.Client(api_key=API_KEY)
    return _client


def keyword_reply(text: str, lang: str):
    if not text:
        return None
    lower = text.lower()
    for key, (en, ml) in REPLIES.items():
        if key in lower or key in text:
            return ml if lang == "ml" else en
    return None


def gemini_reply(text: str, lang: str) -> str:
    lang_name = "Malayalam" if lang == "ml" else "English"
    prompt = (
        "You are Asha, a professional college front-desk AI receptionist. "
        "Speak warmly and naturally, like a helpful human receptionist "
        "(1-3 short spoken sentences, no markdown). "
        f"You MUST reply only in {lang_name}. "
        "Help with admissions, fees, hostel, holidays, events, departments, "
        "and meeting the principal. "
        "If unsure, politely ask them to visit the reception counter.\n\n"
        f"Visitor: {text}\nAsha:"
    )
    try:
        response = _get_client().models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        return str(response.text).strip()
    except Exception as e:
        if lang == "ml":
            return (
                "ഇപ്പോൾ അസിസ്റ്റന്റ് സേവനം ലഭ്യമല്ല. "
                f"ദയവായി റിസപ്ഷൻ കൗണ്ടർ സന്ദർശിക്കുക. ({e})"
            )
        return (
            "I am unable to reach the assistant service right now. "
            f"Please visit the reception counter. ({e})"
        )


def bot_reply(text: str, lang_preference: str = "auto"):
    """
    Returns (answer, lang) where lang is 'en' or 'ml'.
    """
    if not text:
        lang = resolve_lang("", lang_preference)
        if lang == "ml":
            return "ഞാൻ കേട്ടില്ല. ദയവായി വീണ്ടും ടൈപ്പ് ചെയ്യുക അല്ലെങ്കിൽ സംസാരിക്കുക.", lang
        return "I did not catch that. Please type or speak again.", lang

    lang = resolve_lang(text, lang_preference)
    answer = keyword_reply(text, lang)
    if answer:
        return answer, lang
    return gemini_reply(text, lang), lang
