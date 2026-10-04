"""
College AI Receptionist — step-by-step screens
1) OTP Login  →  2) Language  →  3) TalkBot
"""

import asyncio
import os
import tempfile

import flet as ft
import flet_audio as fta
from flet_audio_recorder import AudioEncoder, AudioRecorder, AudioRecorderConfiguration

from bot import bot_reply
from otp_auth import OtpSession, is_valid_phone
from speech import synthesize_speech, transcribe_wav

NAVY = "#0B1F3A"
TEAL = "#0F766E"
TEAL_SOFT = "#CCFBF1"
IVORY = "#F4F7FB"
SLATE = "#000000"
MUTED = "#000000"
BLACK = "#000000"

LANG_OPTIONS = {
    "Auto (detect)": "auto",
    "English": "en",
    "Malayalam (മലയാളം)": "ml",
}
LANG_LABELS = {"auto": "Auto detect", "en": "English", "ml": "Malayalam"}


def card(*controls, **kwargs):
    return ft.Container(
        content=ft.Column(list(controls), spacing=kwargs.pop("spacing", 12), tight=True),
        bgcolor=ft.Colors.WHITE,
        border_radius=16,
        padding=20,
        shadow=ft.BoxShadow(blur_radius=12, color="#14000000", offset=ft.Offset(0, 4)),
        **kwargs,
    )


async def main(page: ft.Page):
    page.title = "College AI Receptionist"
    page.bgcolor = IVORY
    page.padding = 0
    page.theme = ft.Theme(color_scheme_seed=TEAL)

    audio = fta.Audio()
    recorder = AudioRecorder(
        configuration=AudioRecorderConfiguration(encoder=AudioEncoder.WAV),
    )
    page.services.append(audio)
    page.services.append(recorder)

    state = {
        "recording": False,
        "lang": "auto",
        "name": "",
        "phone": "",
        "otp_sent": False,
    }
    otp_session = OtpSession()
    record_path = os.path.join(tempfile.gettempdir(), "asha_voice_input.wav")

    root = ft.Container(expand=True)

    # ------------------------------------------------------------------
    # Shared chat widgets (created once, shown on TalkBot screen)
    # ------------------------------------------------------------------
    chat = ft.ListView(expand=True, spacing=10, auto_scroll=True, padding=16)
    status = ft.Text("", size=12, color=BLACK)
    question = ft.TextField(
        hint_text="Type your question…",
        expand=True,
        border_radius=24,
        filled=True,
        bgcolor=ft.Colors.WHITE,
        color=BLACK,
        border_color=ft.Colors.TRANSPARENT,
        focused_border_color=TEAL,
        content_padding=16,
        text_size=15,
    )

    def add_bubble(who: str, text: str):
        is_user = who == "You"
        chat.controls.append(
            ft.Row(
                [
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Text(
                                    "You" if is_user else "Asha · Reception",
                                    size=11,
                                    weight=ft.FontWeight.W_600,
                                    color=BLACK,
                                ),
                                ft.Text(text, size=14, color=BLACK, selectable=True),
                            ],
                            spacing=4,
                            tight=True,
                        ),
                        bgcolor=ft.Colors.WHITE if is_user else TEAL_SOFT,
                        border_radius=16,
                        padding=14,
                        width=min(page.width * 0.82, 420) if page.width else 320,
                        shadow=ft.BoxShadow(
                            blur_radius=8,
                            color="#14000000",
                            offset=ft.Offset(0, 2),
                        ),
                    )
                ],
                alignment=ft.MainAxisAlignment.END if is_user else ft.MainAxisAlignment.START,
            )
        )

    async def speak(text: str, lang: str):
        try:
            if not text or "unable to reach" in text.lower() or "ലഭ്യമല്ല" in text:
                return
            status.value = "Speaking…"
            page.update()
            data = await synthesize_speech(text, lang)
            if not data:
                return
            audio.src = data
            page.update()
            await audio.play()
        except Exception as e:
            status.value = f"Voice reply unavailable: {e}"
            page.update()

    async def process(user_text: str):
        add_bubble("You", user_text)
        status.value = "Asha is responding…"
        page.update()
        answer, lang = await asyncio.to_thread(bot_reply, user_text, state["lang"])
        add_bubble("Asha", answer)
        status.value = "Ready"
        page.update()
        await speak(answer, lang)

    def set_busy(busy: bool):
        send_btn.disabled = busy
        mic_btn.disabled = busy and not state["recording"]
        question.disabled = busy

    async def send_message(_=None):
        text = (question.value or "").strip()
        if not text:
            status.value = "Please type a question or use the microphone."
            page.update()
            return
        question.value = ""
        set_busy(True)
        page.update()
        try:
            await process(text)
        finally:
            set_busy(False)
            page.update()

    async def toggle_voice(_=None):
        if state["recording"]:
            status.value = "Understanding your voice…"
            mic_btn.icon = ft.Icons.MIC
            mic_btn.bgcolor = TEAL
            state["recording"] = False
            page.update()
            try:
                path = await recorder.stop_recording()
                path = path or record_path
                heard = await asyncio.to_thread(transcribe_wav, path, state["lang"])
                if not heard:
                    status.value = "Could not understand. Please try again."
                    page.update()
                    return
                question.value = heard
                page.update()
                await process(heard)
                question.value = ""
            except Exception as e:
                status.value = f"Voice input failed: {e}"
            finally:
                set_busy(False)
                page.update()
            return

        try:
            if not await recorder.has_permission():
                status.value = "Microphone permission is required."
                page.update()
                return
            ok = await recorder.start_recording(output_path=record_path)
            if not ok:
                status.value = "Could not start the microphone."
                page.update()
                return
            state["recording"] = True
            mic_btn.icon = ft.Icons.STOP_CIRCLE
            mic_btn.bgcolor = "#DC2626"
            status.value = "Listening… tap mic again when finished"
            set_busy(True)
            mic_btn.disabled = False
            page.update()
        except Exception as e:
            status.value = f"Microphone error: {e}"
            page.update()

    question.on_submit = send_message
    send_btn = ft.IconButton(
        icon=ft.Icons.SEND_ROUNDED,
        icon_color=ft.Colors.WHITE,
        bgcolor=TEAL,
        on_click=send_message,
        style=ft.ButtonStyle(shape=ft.CircleBorder()),
    )
    mic_btn = ft.IconButton(
        icon=ft.Icons.MIC,
        icon_color=ft.Colors.WHITE,
        bgcolor=TEAL,
        on_click=toggle_voice,
        style=ft.ButtonStyle(shape=ft.CircleBorder()),
    )

    # ------------------------------------------------------------------
    # Screen 1 — OTP Login
    # ------------------------------------------------------------------
    name_field = ft.TextField(
        label="Your name",
        hint_text="Visitor name",
        border_radius=12,
        filled=True,
        bgcolor=IVORY,
        color=BLACK,
        label_style=ft.TextStyle(color=BLACK),
        prefix_icon=ft.Icons.PERSON_OUTLINE,
    )
    phone_field = ft.TextField(
        label="Mobile number",
        hint_text="10-digit Indian mobile",
        keyboard_type=ft.KeyboardType.PHONE,
        max_length=10,
        border_radius=12,
        filled=True,
        bgcolor=IVORY,
        color=BLACK,
        label_style=ft.TextStyle(color=BLACK),
        prefix_icon=ft.Icons.PHONE_ANDROID,
    )
    otp_field = ft.TextField(
        label="Enter OTP",
        hint_text="6-digit code",
        keyboard_type=ft.KeyboardType.NUMBER,
        max_length=6,
        border_radius=12,
        filled=True,
        bgcolor=IVORY,
        color=BLACK,
        label_style=ft.TextStyle(color=BLACK),
        prefix_icon=ft.Icons.LOCK_OUTLINE,
        visible=False,
    )
    otp_info = ft.Text("", size=12, color=BLACK, visible=False)
    login_error = ft.Text("", size=12, color="#DC2626")
    send_otp_btn = ft.OutlinedButton("Send OTP", icon=ft.Icons.SMS_OUTLINED)
    verify_btn = ft.FilledButton(
        "Verify & Continue",
        icon=ft.Icons.VERIFIED_USER,
        visible=False,
        style=ft.ButtonStyle(
            bgcolor=TEAL,
            color=ft.Colors.WHITE,
            padding=16,
            shape=ft.RoundedRectangleBorder(radius=12),
        ),
    )

    def send_otp(_=None):
        name = (name_field.value or "").strip()
        phone = (phone_field.value or "").strip()
        login_error.value = ""
        if not name:
            login_error.value = "Please enter your name."
            page.update()
            return
        if not is_valid_phone(phone):
            login_error.value = "Enter a valid 10-digit mobile number."
            page.update()
            return

        code = otp_session.issue(phone)
        state["name"] = name
        state["phone"] = phone
        state["otp_sent"] = True

        # Demo delivery is recorded locally.
        otp_field.visible = True
        otp_field.value = ""
        verify_btn.visible = True
        otp_info.visible = True
        otp_info.value = f"OTP sent to +91 {phone[-10:]}. Demo OTP: {code}"
        send_otp_btn.text = "Resend OTP"
        page.update()

    def verify_otp(_=None):
        phone = (phone_field.value or "").strip()
        otp = (otp_field.value or "").strip()
        login_error.value = ""
        if not state["otp_sent"]:
            login_error.value = "Please send OTP first."
            page.update()
            return
        ok, msg = otp_session.verify(phone, otp)
        if not ok:
            login_error.value = msg
            page.update()
            return
        state["name"] = (name_field.value or "").strip()
        state["phone"] = phone
        show_language()

    send_otp_btn.on_click = send_otp
    verify_btn.on_click = verify_otp

    login_screen = ft.Container(
        expand=True,
        bgcolor=NAVY,
        padding=24,
        content=ft.Column(
            [
                ft.Container(expand=True),
                ft.Container(
                    content=ft.Icon(ft.Icons.SUPPORT_AGENT, color=ft.Colors.WHITE, size=48),
                    width=88,
                    height=88,
                    bgcolor="#164E63",
                    border_radius=44,
                    alignment=ft.Alignment.CENTER,
                ),
                ft.Text(
                    "College AI Receptionist",
                    size=26,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.WHITE,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    "OTP login · Step 1 of 3",
                    size=14,
                    color="#A5F3FC",
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(height=16),
                card(
                    ft.Text("Secure login", size=16, weight=ft.FontWeight.W_600, color=BLACK),
                    name_field,
                    phone_field,
                    ft.Row([send_otp_btn], alignment=ft.MainAxisAlignment.END),
                    otp_info,
                    otp_field,
                    login_error,
                    verify_btn,
                    spacing=14,
                ),
                ft.Text(
                    "For demo, OTP is shown on screen. SMS gateway can be added later.",
                    size=11,
                    color=ft.Colors.WHITE,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(expand=True),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
        ),
    )

    # ------------------------------------------------------------------
    # Screen 2 — Language
    # ------------------------------------------------------------------
    lang_dd = ft.Dropdown(
        label="Select language",
        value="Auto (detect)",
        options=[ft.dropdown.Option(k) for k in LANG_OPTIONS],
        border_radius=12,
        filled=True,
        bgcolor=IVORY,
        color=BLACK,
        label_style=ft.TextStyle(color=BLACK),
    )
    lang_hint = ft.Text(
        "Voice input, replies, and speech will use this language.",
        size=13,
        color=BLACK,
    )

    def do_language_next(_=None):
        state["lang"] = LANG_OPTIONS.get(lang_dd.value or "Auto (detect)", "auto")
        show_talkbot()

    def do_language_back(_=None):
        show_login()

    lang_hello = ft.Text("Hello, visitor", size=14, color=BLACK)

    language_screen = ft.Container(
        expand=True,
        bgcolor=IVORY,
        padding=24,
        content=ft.Column(
            [
                ft.Container(height=20),
                ft.Text("Step 2 of 3", size=12, color=BLACK),
                ft.Text("Choose language", size=26, weight=ft.FontWeight.BOLD, color=BLACK),
                lang_hello,
                ft.Container(height=8),
                card(
                    ft.Text("Language", weight=ft.FontWeight.W_600, color=BLACK),
                    lang_dd,
                    lang_hint,
                    ft.Text("• Auto — detect Malayalam or English", size=13, color=BLACK),
                    ft.Text("• English — Indian English voice", size=13, color=BLACK),
                    ft.Text("• Malayalam — മലയാളം voice", size=13, color=BLACK),
                    ft.Row(
                        [
                            ft.OutlinedButton("Back", on_click=do_language_back),
                            ft.FilledButton(
                                "Next — TalkBot",
                                icon=ft.Icons.ARROW_FORWARD,
                                on_click=do_language_next,
                                style=ft.ButtonStyle(bgcolor=TEAL, color=ft.Colors.WHITE),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    spacing=12,
                ),
            ],
            scroll=ft.ScrollMode.AUTO,
        ),
    )

    # greet_label updated when entering talkbot
    greet_label = ft.Text("", size=12, color="#A5F3FC")

    # ------------------------------------------------------------------
    # Screen 3 — TalkBot
    # ------------------------------------------------------------------
    talkbot_header = ft.Container(
        content=ft.Row(
            [
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    icon_color=ft.Colors.WHITE,
                    tooltip="Change language",
                    on_click=lambda e: show_language(),
                ),
                ft.Container(
                    content=ft.Icon(ft.Icons.SUPPORT_AGENT, color=ft.Colors.WHITE, size=24),
                    width=40,
                    height=40,
                    bgcolor="#164E63",
                    border_radius=20,
                    alignment=ft.Alignment.CENTER,
                ),
                ft.Column(
                    [
                        ft.Text("TalkBot · Asha", size=17, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                        greet_label,
                    ],
                    spacing=1,
                    expand=True,
                ),
                ft.IconButton(
                    icon=ft.Icons.LOGOUT,
                    icon_color=ft.Colors.WHITE,
                    tooltip="Logout",
                    on_click=lambda e: show_login(reset=True),
                ),
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor=NAVY,
        padding=ft.Padding.only(left=4, right=8, top=10, bottom=10),
    )

    talkbot_screen = ft.Column(
        [
            talkbot_header,
            ft.Container(content=chat, expand=True, bgcolor=IVORY),
            ft.Container(
                content=ft.Column(
                    [
                        status,
                        ft.Row(
                            [question, mic_btn, send_btn],
                            spacing=8,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                    ],
                    spacing=8,
                ),
                bgcolor=ft.Colors.WHITE,
                padding=16,
                border=ft.Border.only(top=ft.BorderSide(1, "#E2E8F0")),
            ),
        ],
        expand=True,
        spacing=0,
    )

    # ------------------------------------------------------------------
    # Navigation between screens
    # ------------------------------------------------------------------
    def show_login(reset: bool = False):
        if reset:
            state["name"] = ""
            state["phone"] = ""
            state["lang"] = "auto"
            state["otp_sent"] = False
            name_field.value = ""
            phone_field.value = ""
            otp_field.value = ""
            otp_field.visible = False
            verify_btn.visible = False
            otp_info.visible = False
            otp_info.value = ""
            send_otp_btn.text = "Send OTP"
            login_error.value = ""
            chat.controls.clear()
        root.content = login_screen
        page.update()

    def show_language():
        lang_hello.value = f"Hello, {state['name']}"
        root.content = language_screen
        page.update()

    def show_talkbot():
        label = LANG_LABELS.get(state["lang"], "Auto detect")
        greet_label.value = f"{state['name']} · {label}"
        status.value = f"Language: {label} · type or tap mic"
        if not chat.controls:
            if state["lang"] == "ml":
                welcome = (
                    f"സ്വാഗതം {state['name']}. ഞാൻ ആശ, കോളേജ് റിസപ്ഷനിസ്റ്റ്. "
                    "അഡ്മിഷൻ, ഫീസ്, ഹോസ്റ്റൽ തുടങ്ങിയവ ചോദിക്കാം."
                )
            else:
                welcome = (
                    f"Welcome {state['name']}. I am Asha, your college receptionist. "
                    "Ask about admissions, fees, hostel, events, or departments."
                )
            add_bubble("Asha", welcome)
        root.content = talkbot_screen
        page.update()

    # Start on login
    root.content = login_screen
    page.add(root)


if os.environ.get("TALKBOT_WEB") == "1":
    ft.run(main, view=ft.AppView.WEB_BROWSER, host="127.0.0.1", port=8550)
else:
    ft.run(main)
