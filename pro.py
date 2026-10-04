# talkbot_audio_streamlit.py

import streamlit as st
import speech_recognition as sr
import pyttsx3

# -------------------------------------------------
# Streamlit Page Settings
# -------------------------------------------------
st.set_page_config(page_title="College TalkBot")

st.title("🎓 College Reception TalkBot")
st.write("Malayalam / English Voice Assistant")

# -------------------------------------------------
# Initialize TTS
# -------------------------------------------------
if "engine" not in st.session_state:
    st.session_state.engine = pyttsx3.init()

engine = st.session_state.engine

# -------------------------------------------------
# Speak Function
# -------------------------------------------------
def speak(text):
    try:
        engine.say(text)
        engine.runAndWait()

    except Exception as e:
        st.error(f"TTS Error: {e}")

# -------------------------------------------------
# Listen Function
# -------------------------------------------------
def listen():

    recognizer = sr.Recognizer()

    try:

        mic_list = sr.Microphone.list_microphone_names()

        st.write("Available Microphones:")
        st.write(mic_list)

        # Correct microphone check
        if len(mic_list) == 0:
            return "No microphone detected."

        # Default microphone
        with sr.Microphone() as source:

            st.info("🎤 Listening... Speak now")

            recognizer.adjust_for_ambient_noise(
                source,
                duration=1
            )

            audio = recognizer.listen(
                source,
                timeout=5,
                phrase_time_limit=8
            )

            text = recognizer.recognize_google(
                audio,
                language="ml-IN"
            )

            return text

    except sr.WaitTimeoutError:
        return "Listening timeout."

    except sr.UnknownValueError:
        return "Sorry, I could not understand."

    except sr.RequestError:
        return "Internet connection needed."

    except OSError as e:
        return f"Microphone error: {e}"

    except Exception as e:
        return f"Error: {str(e)}"

# -------------------------------------------------
# Bot Response
# -------------------------------------------------
def get_response(user_text):

    user_text = user_text.lower()

    # English
    if "admission" in user_text:
        return "Admissions are open now."

    elif "holiday" in user_text:
        return "Next holiday is on Friday."

    elif "event" in user_text:
        return "College tech fest is next month."

    elif "seat" in user_text:
        return "Seats are available in Computer Science department."

    # Malayalam
    elif "അഡ്മിഷൻ" in user_text:
        return "അഡ്മിഷൻ ഇപ്പോൾ ആരംഭിച്ചിരിക്കുകയാണ്."

    elif "ഹോളിഡേ" in user_text:
        return "അടുത്ത അവധി വെള്ളിയാഴ്ചയാണ്."

    elif "ഇവന്റ്" in user_text:
        return "കോളേജ് ടെക് ഫെസ്റ്റ് അടുത്ത മാസം നടക്കും."

    else:
        return "Please visit reception for more details."

# -------------------------------------------------
# Voice Assistant
# -------------------------------------------------
st.subheader("🎤 Voice Assistant")

if st.button("Start Talking"):

    user_input = listen()

    st.success(f"You Said: {user_input}")

    bot_reply = get_response(user_input)

    st.info(f"Bot: {bot_reply}")

    speak(bot_reply)

# -------------------------------------------------
# Text Input
# -------------------------------------------------
st.subheader("⌨️ Type Your Question")

text_input = st.text_input("Enter your question")

if st.button("Send"):

    if text_input.strip():

        reply = get_response(text_input)

        st.success(reply)

        speak(reply)

    else:
        st.warning("Please type something.")