import streamlit as st
from gtts import gTTS

tts = gTTS(text=reply, lang="ml")
tts.save("reply.mp3")
st.set_page_config(page_title="College TalkBot")

st.title("🎓 College Reception TalkBot")

user_question = st.text_input("Ask a question:")

if user_question:

    question = user_question.lower()

    if "admission" in question or "അഡ്മിഷൻ" in question:
        reply = "അഡ്മിഷൻ ഇപ്പോൾ തുറന്നിരിക്കുന്നു."

    elif "course" in question:
        reply = "We offer BCA, BSc, BCom and MBA programs."

    elif "fee" in question:
        reply = "Please contact the accounts office for fee details."

    else:
        reply = "Sorry, I do not know the answer."

    st.success(reply)