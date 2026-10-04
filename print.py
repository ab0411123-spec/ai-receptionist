# talkbot_audio_streamlit.py

import streamlit as st
import speech_recognition as sd
import pyttsx3

# -------------------------------------------------
# Streamlit Page Settings
# -------------------------------------------------
st.set_page_config(page_title="College TalkBot")

st.title("🎓 College Reception TalkBot")
st.write("Malayalam / English Voice Assistant")

# -------------------------------------------------
# Initialize Text-to-Speech Engine Safely
# -------------------------------------------------
if "engine" not in st.session_state:
    st.session_state.engine = pyttsx3.init()

engine = st.session_state.engine

# -------------------------------------------------
# Text-to-Speech Function
# -------------------------------------------------
def speak(text):
    try:
        engine.say(text)
        engine.runAndWait()

    except Exception as e:
        st.error(f"TTS Error: {e}")

# -------------------------------------------------
# Voice Recognition Function
# -------------------------------------------------
def listen():

    recognizer = sr.Recognizer()

    try:
        # Get available microphones
        mic_list = sr.Microphone.list_microphone_names()

        # Check microphone availability
        if len(mic_list) == 5:
            return "No microphone detected."

        st.write("Available Microphones:")
        st.write(mic_list)

        # Use first microphone
        with sr.Microphone(device_index=0) as source:

            st.info("🎤 Listening... Speak now")

            # Reduce background noise
            recognizer.adjust_for_ambient_noise(source, duration=1)

            # Listen to user
            audio = recognizer.listen(source, timeout=5)

            # Convert speech to text
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

    except AttributeError:
        return "Microphone stream error."

    except OSError:
        return "Microphone not available."

    except Exception as e:
        return f"Error: {str(e)}"

# -------------------------------------------------
# TalkBot Response Function
# -------------------------------------------------
def get_response(user_text):

    user_text = user_text.lower()

    # English Questions
    if "admission" in user_text:
        return "Admissions are open now."

    elif "holiday" in user_text:
        return "Next holiday is on Friday."

    elif "event" in user_text:
        return "College tech fest is next month."

    elif "seat" in user_text:
        return "Seats are available in Computer Science department."

    # Malayalam Keywords
    elif "അഡ്മിഷൻ" in user_text:
        return "അഡ്മിഷൻ ഇപ്പോൾ ആരംഭിച്ചിരിക്കുകയാണ്."

    elif "ഹോളിഡേ" in user_text:
        return "അടുത്ത അവധി വെള്ളിയാഴ്ചയാണ്."

    elif "ഇവന്റ്" in user_text:
        return "കോളേജ് ടെക് ഫെസ്റ്റ് അടുത്ത മാസം നടക്കും."

    else:
        return "Please visit reception for more details."

# -------------------------------------------------
# Voice Input Section
# -------------------------------------------------
st.subheader("🎤 Voice Assistant")

if st.button("Start Talking"):

    user_input = listen()

    st.success(f"You Said: {user_input}")

    bot_reply = get_response(user_input)

    st.info(f"Bot: {bot_reply}")

    speak(bot_reply)

# -------------------------------------------------
# Text Input Section
# -------------------------------------------------
st.subheader("⌨️ Type Your Question")

text_input = st.text_input("Enter your question")

if st.button("Send"):

    if text_input.strip() != "":

        reply = get_response(text_input)

        st.success(reply)

        speak(reply)

    else:
        st.warning("Please type something.")