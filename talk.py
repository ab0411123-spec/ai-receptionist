"""
College Reception TalkBot — Malayalam / English voice + text assistant
Combines keyword replies with Gemini AI (from spee.py).
"""

import base64
import os
import tempfile

import speech_recognition as sr
import streamlit as st
import streamlit.components.v1 as components
from google import genai
from gtts import gTTS

st.set_page_config(page_title="College TalkBot", page_icon="🎓", layout="centered")

# ---------------------------------------------------------------------------
# Gemini client
# ---------------------------------------------------------------------------
API_KEY = os.environ.get(
    "GEMINI_API_KEY",
    "AQ.Ab8RN6IUGhMgX6moVecBt7QBlRfhyVTUi_mrUNnWYwLODQBUGg",
)
client = genai.Client(api_key=API_KEY)

# ---------------------------------------------------------------------------
# Bot replies (college keywords)
# ---------------------------------------------------------------------------
REPLIES = {
    "admission": "Admissions are open now.",
    "adm": "Admissions are open now.",
    "അഡ്മിഷൻ": "അഡ്മിഷൻ ഇപ്പോൾ ആരംഭിച്ചിരിക്കുകയാണ്.",
    "holiday": "Next holiday is on Friday.",
    "അവധി": "അടുത്ത അവധി വെള്ളിയാഴ്ചയാണ്.",
    "event": "College tech fest is next month.",
    "fest": "College tech fest is next month.",
    "ഇവന്റ്": "കോളേജ് ടെക് ഫെസ്റ്റ് അടുത്ത മാസം നടക്കും.",
    "seat": "Seats are available in Computer Science.",
    "cse": "Welcome to Computer Science department.",
    "fee": "Contact accounts section for fee details.",
    "ഫീസ്": "ഫീസ് വിവരങ്ങൾക്ക് അക്കൗണ്ട്സ് വിഭാഗവുമായി ബന്ധപ്പെടുക.",
    "hostel": "Hostel facilities are available.",
    "ഹോസ്റ്റൽ": "ഹോസ്റ്റൽ സൗകര്യം ലഭ്യമാണ്.",
    "principal": "Register at reception to meet the principal.",
    "eee": "Welcome to EEE department.",
}


def keyword_reply(text):
    """Return a fixed college reply if a keyword matches, else None."""
    if not text:
        return None

    lower = text.lower()
    for key, answer in REPLIES.items():
        if key in lower or key in text:
            return answer
    return None


def gemini_reply(text):
    """Ask Gemini when no keyword matches."""
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=(
                "You are a helpful college reception assistant. "
                "Reply briefly in the same language as the user "
                "(Malayalam or English).\n\n"
                f"User: {text}"
            ),
        )
        return str(response.text).strip()
    except Exception as e:
        return f"Sorry, AI reply failed: {e}"


def bot_reply(text):
    if not text:
        return "Sorry, I could not hear you."

    answer = keyword_reply(text)
    if answer:
        return answer
    return gemini_reply(text)


# ---------------------------------------------------------------------------
# Microphone — safe open/close
# ---------------------------------------------------------------------------
class SafeMic:
    def __init__(self, index=None):
        self._mic = sr.Microphone() if index is None else sr.Microphone(device_index=index)

    def __enter__(self):
        return self._mic.__enter__()

    def __exit__(self, *args):
        stream = getattr(self._mic, "stream", None)
        if stream is None:
            self._cleanup()
            return False
        try:
            return self._mic.__exit__(*args)
        except (AttributeError, OSError):
            try:
                stream.stop_stream()
                stream.close()
            except Exception:
                pass
            self._cleanup()
            return False

    def _cleanup(self):
        audio = getattr(self._mic, "audio", None)
        if audio:
            try:
                audio.terminate()
            except Exception:
                pass


def get_microphones():
    """Build mic list safely (avoids Windows PyAudio -9996 errors)."""
    devices = {"Default microphone": None}

    try:
        for i, name in enumerate(sr.Microphone.list_microphone_names()):
            label = f"[{i}] {name}"
            if label not in devices:
                devices[label] = i
    except OSError:
        pass

    return devices


def pick_mic(devices):
    saved = st.session_state.get("mic_index")
    if saved in devices.values():
        for label, idx in devices.items():
            if idx == saved:
                return label, idx

    for label, idx in devices.items():
        if idx is None:
            continue
        n = label.lower()
        if any(w in n for w in ("microphone", "headset", "mic", "array")):
            if "stereo mix" not in n and "output" not in n:
                return label, idx

    label = next(iter(devices))
    return label, devices[label]


# ---------------------------------------------------------------------------
# Speech in / out
# ---------------------------------------------------------------------------
def is_malayalam(text):
    return any("\u0d00" <= ch <= "\u0d7f" for ch in text)


def speak(text):
    """Speak with gTTS (Malayalam or English) and autoplay in the browser."""
    try:
        lang = "ml" if is_malayalam(text) else "en"
        tts = gTTS(text=text, lang=lang)
        temp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        tts.save(temp.name)

        with open(temp.name, "rb") as f:
            audio_bytes = f.read()

        audio_base64 = base64.b64encode(audio_bytes).decode()
        components.html(
            f"""
            <audio autoplay>
                <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
            </audio>
            """,
            height=0,
        )
    except Exception as e:
        st.error(f"Speech error: {e}")


def listen(mic_index, mic_label):
    rec = sr.Recognizer()
    rec.dynamic_energy_threshold = False
    rec.energy_threshold = 400
    rec.pause_threshold = 1.0

    try:
        with SafeMic(mic_index) as source:
            st.info(f"🎤 Listening — {mic_label}")
            rec.adjust_for_ambient_noise(source, duration=1)
            audio = rec.listen(source, timeout=10, phrase_time_limit=10)

        for lang in ("ml-IN", "en-IN"):
            try:
                return rec.recognize_google(audio, language=lang)
            except sr.UnknownValueError:
                continue

        st.warning("Could not understand. Try again.")
        return None

    except sr.WaitTimeoutError:
        st.warning("No speech heard.")
        return None
    except sr.RequestError:
        st.error("Internet required for voice recognition.")
        return None
    except (OSError, AttributeError, AssertionError):
        st.error("Microphone failed. Pick another device in the sidebar.")
        return None
    except Exception as e:
        st.error(f"Error: {e}")
        return None


def test_mic(mic_index, mic_label):
    try:
        with SafeMic(mic_index) as source:
            sr.Recognizer().adjust_for_ambient_noise(source, duration=0.5)
        st.success(f"OK: {mic_label}")
    except Exception as e:
        st.error(f"Failed: {mic_label} — {e}")


def respond(user_text):
    st.success(f"You: {user_text}")
    answer = bot_reply(user_text)
    st.info(f"Bot: {answer}")
    speak(answer)


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
st.title("🎓 College Reception TalkBot")
st.caption("മലയാളം / English — keywords + Gemini AI")

mic_index = None
mic_label = "Default microphone"

with st.sidebar:
    st.header("🎙️ Microphone")

    if st.button("Refresh devices"):
        st.rerun()

    mics = get_microphones()
    labels = list(mics.keys())
    default_label, _ = pick_mic(mics)

    mic_label = st.selectbox(
        "Select microphone",
        labels,
        index=labels.index(default_label),
    )
    mic_index = mics[mic_label]
    st.session_state.mic_index = mic_index

    if st.button("Test microphone"):
        test_mic(mic_index, mic_label)

st.subheader("🎤 Voice")

if st.button("Start Talking", type="primary", use_container_width=True):
    heard = listen(mic_index, mic_label)
    if heard:
        respond(heard)

st.divider()
st.subheader("⌨️ Text")

with st.form("chat"):
    question = st.text_input("Your question", placeholder="admission, fee, hostel...")
    send = st.form_submit_button("Send", use_container_width=True)

    if send:
        if question.strip():
            respond(question.strip())
        else:
            st.warning("Type a question first.")

with st.expander("Sample questions"):
    st.markdown(
        "**English:** admission, fee, hostel, holiday, event, seat, principal, cse, eee  \n"
        "**Malayalam:** അഡ്മിഷൻ, ഫീസ്, ഹോസ്റ്റൽ, അവധി, ഇവന്റ്  \n"
        "Other questions are answered by Gemini AI."
    )
