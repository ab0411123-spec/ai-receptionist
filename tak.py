# മലയാളം വോയ്സ് ആപ്പ് - Streamlit വേർഷൻ (Groq AI സഹിതം)
# ------------------------------------------------
# ഇൻസ്റ്റാൾ ചെയ്യേണ്ടത്:
#   pip install streamlit audio-recorder-streamlit SpeechRecognition gTTS pydub groq
#
# റൺ ചെയ്യേണ്ടത്:
#   streamlit run malayalam_voice_app_streamlit.py
#
# ശ്രദ്ധിക്കുക: pydub-ന് "ffmpeg" വേണം (audio convert ചെയ്യാൻ)
#   Windows: winget install ffmpeg
#   Mac:     brew install ffmpeg
#   Linux:   sudo apt install ffmpeg
#
# GROQ API KEY: https://console.groq.com/keys എന്നതിൽ നിന്ന് ഫ്രീ ആയി എടുക്കാം (കാർഡ് വേണ്ട)
# താഴെ GROQ_API_KEY = "" എന്നതിനുള്ളിൽ നിങ്ങളുടെ key പേസ്റ്റ് ചെയ്യുക
# ------------------------------------------------

import streamlit as st
from audio_recorder_streamlit import audio_recorder
import speech_recognition as sr
from gtts import gTTS
from pydub import AudioSegment
from groq import Groq
import io

# ⬇️⬇️ ഇവിടെ നിങ്ങളുടെ ഫ്രീ Groq API key പേസ്റ്റ് ചെയ്യുക ⬇️⬇️
GROQ_API_KEY = "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"

client = Groq(api_key=GROQ_API_KEY)

st.set_page_config(page_title="മലയാളം വോയ്സ് ആപ്പ്", page_icon="🗣️")
st.title("🗣️ മലയാളം വോയ്സ് ആപ്പ്")
st.write("മൈക്ക് ബട്ടൺ അമർത്തി മലയാളത്തിൽ സംസാരിക്കൂ")

recognizer = sr.Recognizer()


def marupadi_undakkuka(text):
    """Groq AI വച്ച് മലയാളത്തിൽ ബുദ്ധിപരമായ മറുപടി ഉണ്ടാക്കുന്നു"""
    try:
        chat_completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "നീ ഒരു സഹായി ആണ്. എപ്പോഴും മലയാളത്തിൽ മാത്രം, "
                        "ചെറുതും വ്യക്തവുമായ മറുപടി തരൂ. ഇംഗ്ലീഷ് വാക്കുകൾ "
                        "ഉപയോഗിക്കരുത്."
                    ),
                },
                {"role": "user", "content": text},
            ],
        )
        return chat_completion.choices[0].message.content.strip()
    except Exception as e:
        return f"ക്ഷമിക്കണം, AI-യിൽ നിന്ന് മറുപടി കിട്ടിയില്ല. കാരണം: {e}"


def webm_to_wav_bytes(webm_bytes):
    """audio_recorder തരുന്ന audio-യെ speech_recognition-ന് വേണ്ട wav ആക്കുന്നു"""
    audio_segment = AudioSegment.from_file(io.BytesIO(webm_bytes))
    wav_io = io.BytesIO()
    audio_segment.export(wav_io, format="wav")
    wav_io.seek(0)
    return wav_io


def text_to_speech_bytes(text):
    """മറുപടി മലയാളത്തിൽ mp3 ആയി ഉണ്ടാക്കുന്നു"""
    tts = gTTS(text=text, lang="ml")
    mp3_io = io.BytesIO()
    tts.write_to_fp(mp3_io)
    mp3_io.seek(0)
    return mp3_io


# --- മൈക്ക് റെക്കോർഡർ ---
audio_bytes = audio_recorder(
    text="സംസാരിക്കാൻ അമർത്തുക",
    recording_color="#e63946",
    neutral_color="#2a9d8f",
    icon_size="3x",
)

if audio_bytes:
    st.audio(audio_bytes, format="audio/wav")

    with st.spinner("കേട്ട് മനസ്സിലാക്കുന്നു..."):
        try:
            wav_io = webm_to_wav_bytes(audio_bytes)
            with sr.AudioFile(wav_io) as source:
                audio_data = recognizer.record(source)
            user_text = recognizer.recognize_google(audio_data, language="ml-IN")
            st.success(f"നിങ്ങൾ പറഞ്ഞത്: {user_text}")

            reply = marupadi_undakkuka(user_text)
            st.info(f"മറുപടി: {reply}")

            mp3_io = text_to_speech_bytes(reply)
            st.audio(mp3_io, format="audio/mp3", autoplay=True)

        except sr.UnknownValueError:
            st.error("ക്ഷമിക്കണം, മനസ്സിലായില്ല. വീണ്ടും ശ്രമിക്കൂ")
        except sr.RequestError:
            st.error("ഇന്റർനെറ്റ് കണക്ഷൻ ചെക്ക് ചെയ്യൂ")
            