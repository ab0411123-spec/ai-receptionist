"""Natural Malayalam / English speech (neural TTS) + STT helpers."""

import asyncio
import os
import tempfile

# Human-like neural voices (Microsoft Edge TTS)
VOICE_EN = "en-IN-NeerjaNeural"  # Indian English, natural female
VOICE_ML = "ml-IN-SobhanaNeural"  # Malayalam, natural female


def is_malayalam(text: str) -> bool:
    return any("\u0d00" <= ch <= "\u0d7f" for ch in (text or ""))


def resolve_lang(text: str, preference: str) -> str:
    """preference: auto | en | ml  →  returns en | ml"""
    pref = (preference or "auto").lower()
    if pref in ("en", "english"):
        return "en"
    if pref in ("ml", "malayalam", "മലയാളം"):
        return "ml"
    # auto
    return "ml" if is_malayalam(text) else "en"


async def synthesize_speech(text: str, lang: str) -> bytes:
    """Return MP3 bytes with human-like neural voice. Falls back to gTTS."""
    if not text:
        return b""

    path = os.path.join(tempfile.gettempdir(), "asha_neural_reply.mp3")
    voice = VOICE_ML if lang == "ml" else VOICE_EN

    try:
        import edge_tts

        communicate = edge_tts.Communicate(text, voice=voice, rate="-5%")
        await communicate.save(path)
        with open(path, "rb") as f:
            data = f.read()
        if data:
            return data
    except Exception:
        pass

    # Fallback: gTTS
    from gtts import gTTS

    gtts_lang = "ml" if lang == "ml" else "en"
    await asyncio.to_thread(gTTS(text=text, lang=gtts_lang, slow=False).save, path)
    with open(path, "rb") as f:
        return f.read()


def transcribe_wav(path: str, lang_preference: str = "auto"):
    """Speech-to-text. Uses selected language first, then the other."""
    import speech_recognition as sr

    rec = sr.Recognizer()
    with sr.AudioFile(path) as source:
        audio = rec.record(source)

    pref = (lang_preference or "auto").lower()
    if pref in ("ml", "malayalam", "മലയാളം"):
        order = ("ml-IN", "en-IN")
    elif pref in ("en", "english"):
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
