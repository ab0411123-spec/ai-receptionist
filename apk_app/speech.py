"""Speech helpers — EN/ML input STT, Malayalam-only TTS output."""

import asyncio
import os
import tempfile

VOICE_ML = "ml-IN-SobhanaNeural"


def is_malayalam(text: str) -> bool:
    return any("\u0d00" <= ch <= "\u0d7f" for ch in (text or ""))


def resolve_lang(text: str, preference: str) -> str:
    """Input language preference only. Output speech is always Malayalam."""
    pref = (preference or "ml").lower()
    if pref in ("en", "english"):
        return "en"
    if pref in ("ml", "malayalam", "മലയാളം"):
        return "ml"
    return "ml" if is_malayalam(text) else "en"


async def synthesize_speech(text: str, lang: str = "ml") -> bytes:
    """Always synthesize Malayalam speech (Edge TTS → gTTS)."""
    _ = lang  # callers may pass anything; output is forced to Malayalam
    if not text:
        return b""

    path = os.path.join(tempfile.gettempdir(), "codeai_neural_reply.mp3")

    try:
        import edge_tts

        communicate = edge_tts.Communicate(text, voice=VOICE_ML, rate="-5%")
        await communicate.save(path)
        with open(path, "rb") as f:
            data = f.read()
        if data:
            return data
    except Exception:
        pass

    from gtts import gTTS

    await asyncio.to_thread(gTTS(text=text, lang="ml", slow=False).save, path)
    with open(path, "rb") as f:
        return f.read()


def transcribe_wav(path: str, lang_preference: str = "ml"):
    """Speech-to-text for English or Malayalam input."""
    import speech_recognition as sr

    rec = sr.Recognizer()
    with sr.AudioFile(path) as source:
        audio = rec.record(source)

    pref = (lang_preference or "ml").lower()
    if pref in ("en", "english"):
        order = ("en-IN", "en-US", "ml-IN")
    else:
        order = ("ml-IN", "en-IN", "en-US")

    for code in order:
        try:
            return rec.recognize_google(audio, language=code)
        except sr.UnknownValueError:
            continue
        except sr.RequestError as e:
            raise RuntimeError(f"Speech service unavailable: {e}") from e
    return None
