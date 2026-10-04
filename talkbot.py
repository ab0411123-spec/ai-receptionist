import streamlit as st
import speech_recognition as sr
from gtts import gTTS
from playsound import playsound
import tempfile
import threading
import os

# ------------------------------------------------
# PAGE SETTINGS
# ------------------------------------------------
st.set_page_config(
    page_title="College TalkBot",
    page_icon="🎓",
    layout="centered"
)

st.title("🎓 College Reception TalkBot")
st.write("മലയാളം വോയ്സ് അസിസ്റ്റന്റ്")

# ------------------------------------------------
# AUDIO OUTPUT (MALAYALAM)
# ------------------------------------------------
def tts_worker(text):
    try:
        tts = gTTS(
            text=text,
            lang="ml",
            slow=False
        )

        temp_file = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".mp3"
        )

        filename = temp_file.name

        tts.save(filename)

        playsound(filename)

        os.remove(filename)

    except Exception as e:
        st.error(f"ശബ്ദ പിശക്: {e}")


def speak(text):
    threading.Thread(
        target=tts_worker,
        args=(text,),
        daemon=True
    ).start()

# ------------------------------------------------
# VOICE INPUT
# ------------------------------------------------
def listen():

    recognizer = sr.Recognizer()

    try:

        with sr.Microphone() as source:

            st.info("🎤 സംസാരിക്കുക...")

            recognizer.adjust_for_ambient_noise(
                source,
                duration=1
            )

            audio = recognizer.listen(
                source,
                timeout=10,
                phrase_time_limit=10
            )

        try:
            return recognizer.recognize_google(
                audio,
                language="ml-IN"
            )

        except:
            return recognizer.recognize_google(
                audio,
                language="en-IN"
            )

    except Exception as e:

        st.error(f"മൈക്രോഫോൺ പിശക്: {e}")

        return None

# ------------------------------------------------
# BOT RESPONSES
# ------------------------------------------------
def get_response(user_text):

    if not user_text:
        return "ക്ഷമിക്കണം, എനിക്ക് കേൾക്കാനായില്ല."

    text = user_text.lower()

    if "admission" in text or "അഡ്മിഷൻ" in user_text:
        return "അഡ്മിഷൻ ഇപ്പോൾ ആരംഭിച്ചിരിക്കുകയാണ്."

    elif "fee" in text or "ഫീസ്" in user_text:
        return "ഫീസ് വിവരങ്ങൾക്ക് അക്കൗണ്ട്സ് വിഭാഗവുമായി ബന്ധപ്പെടുക."

    elif "hostel" in text or "ഹോസ്റ്റൽ" in user_text:
        return "ഹോസ്റ്റൽ സൗകര്യം ലഭ്യമാണ്."

    elif "holiday" in text or "അവധി" in user_text:
        return "അടുത്ത അവധി വെള്ളിയാഴ്ചയാണ്."

    elif "event" in text or "ഇവന്റ്" in user_text:
        return "കോളേജ് ടെക് ഫെസ്റ്റ് അടുത്ത മാസം നടക്കും."

    elif "seat" in text:
        return "കമ്പ്യൂട്ടർ സയൻസ് വിഭാഗത്തിൽ സീറ്റുകൾ ലഭ്യമാണ്."

    elif "cse" in text:
        return "കമ്പ്യൂട്ടർ സയൻസ് ആൻഡ് എഞ്ചിനീയറിംഗ് വിഭാഗത്തിലേക്ക് സ്വാഗതം."

    elif "eee" in text:
        return "ഇലക്ട്രിക്കൽ ആൻഡ് ഇലക്ട്രോണിക്സ് എഞ്ചിനീയറിംഗ് വിഭാഗത്തിലേക്ക് സ്വാഗതം."

    elif "principal" in text:
        return "പ്രിൻസിപ്പലിനെ കാണുന്നതിന് റിസപ്ഷനിൽ രജിസ്റ്റർ ചെയ്യുക."

    else:
        return "കൂടുതൽ വിവരങ്ങൾക്ക് റിസപ്ഷനുമായി ബന്ധപ്പെടുക."

# ------------------------------------------------
# VOICE ASSISTANT
# ------------------------------------------------
st.subheader("🎤 വോയ്സ് അസിസ്റ്റന്റ്")

if st.button("സംസാരിക്കുക"):

    user_input = listen()

    if user_input:

        st.success(f"നിങ്ങൾ പറഞ്ഞു: {user_input}")

        bot_reply = get_response(user_input)

        st.info(f"ബോട്ട്: {bot_reply}")

        speak(bot_reply)

    else:

        st.warning("സംസാരം കണ്ടെത്തിയില്ല.")

# ------------------------------------------------
# TEXT CHAT
# ------------------------------------------------
st.subheader("⌨️ ചോദ്യം ടൈപ്പ് ചെയ്യുക")

text_input = st.text_input("നിങ്ങളുടെ ചോദ്യം ഇവിടെ നൽകുക")

if st.button("അയയ്ക്കുക"):

    if text_input.strip():

        reply = get_response(text_input)

        st.success(reply)

        speak(reply)

    else:

        st.warning("ദയവായി ഒരു ചോദ്യം നൽകുക.")