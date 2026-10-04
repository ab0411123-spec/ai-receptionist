import streamlit as st
import speech_recognition as sr
from google import genai
from gtts import gTTS
import tempfile
import streamlit.components.v1 as components
import base64
API_KEY = "AQ.Ab8RN6IUGhMgX6moVecBt7QBlRfhyVTUi_mrUNnWYwLODQBUGg"

client = genai.Client(api_key=API_KEY)

st.set_page_config(page_title="Malayalam Voice Assistant")

st.title("🎙️ Malayalam Voice Assistant")
st.write("താഴെയുള്ള ബട്ടൺ അമർത്തി സംസാരിക്കുക.")
if st.button("🎤 സംസാരിക്കുക"):
    r = sr.Recognizer()

    with sr.Microphone() as source:
        st.write("🎤 കേൾക്കുന്നു...")
        r.adjust_for_ambient_noise(source, duration=1)
        audio = r.listen(source)

    try:
        text = r.recognize_google(audio, language="ml-IN")
        st.write("🧑 you:", text)

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=text
        )

        answer = response.text
        answer = str(answer)

        st.write("🤖 Jinto:", answer)

        tts = gTTS(text=answer, lang="ml")
        temp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        tts.save(temp.name)

        with open(temp.name, "rb") as f:
            audio_bytes = f.read()

        audio_base64 = base64.b64encode(audio_bytes).decode()

        components.html(f"""
        <audio autoplay>
            <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
        </audio>
        """, height=0)

    except Exception as e:
        st.error(e)
