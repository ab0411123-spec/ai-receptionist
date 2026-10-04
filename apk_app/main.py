"""
CodeAI Malayalam Receptionist (Flet APK)
Visitor: OTP Login → Language → Purpose → TalkBot
Admin: password login → edit college settings (operates the whole app config)
Spoken input: English or Malayalam · Spoken output: Malayalam only
"""

import asyncio
import os
import tempfile

import flet as ft
import flet_audio as fta
from flet_audio_recorder import AudioEncoder, AudioRecorder, AudioRecorderConfiguration

from bot import (
    COLLEGE,
    bot_reply,
    college_overview,
    greeting,
    load_college,
    save_college,
    verify_admin,
)
from otp_auth import OtpSession, is_valid_phone
from speech import synthesize_speech, transcribe_wav

NAVY = "#0B1F3A"
TEAL = "#0F766E"
TEAL_SOFT = "#CCFBF1"
IVORY = "#F4F7FB"
BLACK = "#000000"

LANG_OPTIONS = {
    "മലയാളം (Malayalam)": "ml",
    "English": "en",
}
LANG_LABELS = {"en": "English input", "ml": "മലയാളം input"}
PURPOSE_LABELS = {
    "general": {"en": "General questions", "ml": "പൊതുവായ ചോദ്യങ്ങൾ"},
    "college": {"en": "College information", "ml": "കോളേജ് വിവരങ്ങൾ"},
}


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
    page.title = "CodeAI Receptionist"
    page.bgcolor = IVORY
    page.padding = 0
    page.theme = ft.Theme(color_scheme_seed=TEAL)

    audio = fta.Audio()
    recorder = AudioRecorder(
        configuration=AudioRecorderConfiguration(encoder=AudioEncoder.WAV),
    )
    page.services.append(audio)
    page.services.append(recorder)

    load_college()
    state = {
        "recording": False,
        "lang": "ml",  # input language only
        "purpose": "college",
        "name": "",
        "phone": "",
        "otp_sent": False,
        "welcomed": False,
        "is_admin": False,
        "login_mode": "visitor",  # visitor | admin
    }
    otp_session = OtpSession()
    record_path = os.path.join(tempfile.gettempdir(), "codeai_voice_input.wav")

    root = ft.Container(expand=True)

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
                                    "You" if is_user else "CodeAI · Reception",
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

    async def speak_malayalam(text: str):
        try:
            if not text or "ലഭ്യമല്ല" in text:
                return
            status.value = "Speaking (മലയാളം)…"
            page.update()
            data = await synthesize_speech(text, "ml")
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
        status.value = "CodeAI is responding…"
        page.update()
        answer, _ = await asyncio.to_thread(
            bot_reply, user_text, state["lang"], state["purpose"]
        )
        add_bubble("Asha", answer)
        status.value = "Ready · replies spoken in Malayalam"
        page.update()
        await speak_malayalam(answer)

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
            lang_hint = "English" if state["lang"] == "en" else "മലയാളം"
            status.value = f"Listening ({lang_hint})… tap mic again when finished"
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
    # Screen 1 — Login (Visitor OTP | Admin password)
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

    admin_user_field = ft.TextField(
        label="Admin username",
        hint_text="admin",
        border_radius=12,
        filled=True,
        bgcolor=IVORY,
        color=BLACK,
        label_style=ft.TextStyle(color=BLACK),
        prefix_icon=ft.Icons.ADMIN_PANEL_SETTINGS,
        visible=False,
    )
    admin_pass_field = ft.TextField(
        label="Admin password",
        hint_text="Password",
        password=True,
        can_reveal_password=True,
        border_radius=12,
        filled=True,
        bgcolor=IVORY,
        color=BLACK,
        label_style=ft.TextStyle(color=BLACK),
        prefix_icon=ft.Icons.LOCK_OUTLINE,
        visible=False,
    )
    admin_login_btn = ft.FilledButton(
        "Admin login",
        icon=ft.Icons.LOGIN,
        visible=False,
        style=ft.ButtonStyle(
            bgcolor=TEAL,
            color=ft.Colors.WHITE,
            padding=16,
            shape=ft.RoundedRectangleBorder(radius=12),
        ),
    )

    visitor_box = ft.Column(
        [name_field, phone_field, ft.Row([send_otp_btn], alignment=ft.MainAxisAlignment.END),
         otp_info, otp_field, verify_btn],
        spacing=14,
        tight=True,
    )
    admin_box = ft.Column(
        [admin_user_field, admin_pass_field, admin_login_btn],
        spacing=14,
        tight=True,
        visible=False,
    )
    login_subtitle = ft.Text(
        "Visitor OTP login · Step 1 of 4",
        size=14,
        color="#A5F3FC",
        text_align=ft.TextAlign.CENTER,
    )
    login_hint = ft.Text(
        "For demo, OTP is shown on screen. SMS gateway can be added later.",
        size=11,
        color=ft.Colors.WHITE,
        text_align=ft.TextAlign.CENTER,
    )

    def set_login_mode(mode: str):
        state["login_mode"] = mode
        is_admin_mode = mode == "admin"
        visitor_box.visible = not is_admin_mode
        admin_box.visible = is_admin_mode
        admin_user_field.visible = is_admin_mode
        admin_pass_field.visible = is_admin_mode
        admin_login_btn.visible = is_admin_mode
        login_error.value = ""
        if is_admin_mode:
            login_subtitle.value = "Admin login · manage college settings"
            login_hint.value = "Only admin can edit college info used by the receptionist."
            role_tabs.selected_index = 1
        else:
            login_subtitle.value = "Visitor OTP login · Step 1 of 4"
            login_hint.value = "For demo, OTP is shown on screen. SMS gateway can be added later."
            role_tabs.selected_index = 0
        page.update()

    def on_role_change(e: ft.ControlEvent):
        set_login_mode("admin" if e.control.selected_index == 1 else "visitor")

    role_tabs = ft.Tabs(
        selected_index=0,
        animation_duration=200,
        on_change=on_role_change,
        tabs=[
            ft.Tab(text="Visitor", icon=ft.Icons.PERSON_OUTLINE),
            ft.Tab(text="Admin", icon=ft.Icons.ADMIN_PANEL_SETTINGS),
        ],
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
        state["is_admin"] = False

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
        state["is_admin"] = False
        show_language()

    def do_admin_login(_=None):
        user = (admin_user_field.value or "").strip()
        pwd = admin_pass_field.value or ""
        login_error.value = ""
        if not verify_admin(user, pwd):
            login_error.value = "Invalid admin username or password."
            page.update()
            return
        state["is_admin"] = True
        state["name"] = "Admin"
        admin_pass_field.value = ""
        show_admin()

    send_otp_btn.on_click = send_otp
    verify_btn.on_click = verify_otp
    admin_login_btn.on_click = do_admin_login

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
                    "CodeAI Receptionist",
                    size=26,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.WHITE,
                    text_align=ft.TextAlign.CENTER,
                ),
                login_subtitle,
                ft.Container(height=12),
                card(
                    ft.Text("Secure login", size=16, weight=ft.FontWeight.W_600, color=BLACK),
                    role_tabs,
                    visitor_box,
                    admin_box,
                    login_error,
                    spacing=14,
                ),
                login_hint,
                ft.Container(expand=True),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
        ),
    )

    # ------------------------------------------------------------------
    # Admin screen — edit college settings (admin only)
    # ------------------------------------------------------------------
    def _admin_field(label: str, key: str, multiline: bool = False) -> ft.TextField:
        return ft.TextField(
            label=label,
            value=COLLEGE.get(key, ""),
            border_radius=12,
            filled=True,
            bgcolor=IVORY,
            color=BLACK,
            label_style=ft.TextStyle(color=BLACK),
            multiline=multiline,
            min_lines=3 if multiline else 1,
            max_lines=6 if multiline else 1,
            data=key,
        )

    admin_fields = {
        "name": _admin_field("College name (English)", "name"),
        "name_ml": _admin_field("College name (Malayalam)", "name_ml"),
        "location": _admin_field("Location (English)", "location"),
        "location_ml": _admin_field("Location (Malayalam)", "location_ml"),
        "principal": _admin_field("Principal (English)", "principal"),
        "principal_ml": _admin_field("Principal (Malayalam)", "principal_ml"),
        "phone": _admin_field("Phone", "phone"),
        "email": _admin_field("Email", "email"),
        "office_hours": _admin_field("Office hours (English)", "office_hours"),
        "office_hours_ml": _admin_field("Office hours (Malayalam)", "office_hours_ml"),
        "departments_ml": _admin_field("Departments (Malayalam, one per line)", "departments_ml", True),
        "admission_note_ml": _admin_field("Admission note (Malayalam)", "admission_note_ml", True),
        "fee_note_ml": _admin_field("Fee note (Malayalam)", "fee_note_ml", True),
        "hostel_note_ml": _admin_field("Hostel note (Malayalam)", "hostel_note_ml", True),
        "next_holiday_ml": _admin_field("Next holiday (Malayalam)", "next_holiday_ml"),
        "next_event_ml": _admin_field("Next event (Malayalam)", "next_event_ml", True),
    }
    admin_status = ft.Text("", size=13, color=TEAL)

    def refresh_admin_fields():
        load_college()
        for key, field in admin_fields.items():
            field.value = COLLEGE.get(key, "")

    def save_admin_settings(_=None):
        if not state.get("is_admin"):
            admin_status.value = "Admin only."
            admin_status.color = "#DC2626"
            page.update()
            return
        updates = {key: (field.value or "").strip() for key, field in admin_fields.items()}
        save_college(updates)
        admin_status.value = "Saved. Visitors will see the updated college info."
        admin_status.color = TEAL
        page.update()

    admin_screen = ft.Column(
        [
            ft.Container(
                content=ft.Row(
                    [
                        ft.Icon(ft.Icons.ADMIN_PANEL_SETTINGS, color=ft.Colors.WHITE),
                        ft.Column(
                            [
                                ft.Text(
                                    "Admin · College settings",
                                    size=17,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.WHITE,
                                ),
                                ft.Text(
                                    "Only admin can edit these — used by the whole receptionist APK",
                                    size=11,
                                    color="#A5F3FC",
                                ),
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
                padding=ft.Padding.symmetric(horizontal=12, vertical=10),
            ),
            ft.Container(
                expand=True,
                bgcolor=IVORY,
                padding=16,
                content=ft.Column(
                    [
                        ft.Text(
                            "Edit college profile. Changes apply to chat replies immediately after Save.",
                            size=13,
                            color=BLACK,
                        ),
                        *admin_fields.values(),
                        admin_status,
                        ft.FilledButton(
                            "Save settings",
                            icon=ft.Icons.SAVE,
                            on_click=save_admin_settings,
                            style=ft.ButtonStyle(bgcolor=TEAL, color=ft.Colors.WHITE),
                        ),
                    ],
                    spacing=12,
                    scroll=ft.ScrollMode.AUTO,
                ),
            ),
        ],
        expand=True,
        spacing=0,
    )

    # ------------------------------------------------------------------
    # Screen 2 — Input language (EN / ML)
    # ------------------------------------------------------------------
    lang_dd = ft.Dropdown(
        label="I will speak / type in",
        value="മലയാളം (Malayalam)",
        options=[ft.dropdown.Option(k) for k in LANG_OPTIONS],
        border_radius=12,
        filled=True,
        bgcolor=IVORY,
        color=BLACK,
        label_style=ft.TextStyle(color=BLACK),
    )
    lang_hint = ft.Text(
        "Spoken replies are always in Malayalam.",
        size=13,
        color=BLACK,
    )
    lang_hello = ft.Text("Hello, visitor", size=14, color=BLACK)

    def do_language_next(_=None):
        state["lang"] = LANG_OPTIONS.get(lang_dd.value or "മലയാളം (Malayalam)", "ml")
        show_purpose()

    def do_language_back(_=None):
        show_login()

    language_screen = ft.Container(
        expand=True,
        bgcolor=IVORY,
        padding=24,
        content=ft.Column(
            [
                ft.Container(height=20),
                ft.Text("Step 2 of 4", size=12, color=BLACK),
                ft.Text("Choose input language", size=26, weight=ft.FontWeight.BOLD, color=BLACK),
                lang_hello,
                ft.Container(height=8),
                card(
                    ft.Text("Input language", weight=ft.FontWeight.W_600, color=BLACK),
                    lang_dd,
                    lang_hint,
                    ft.Text("• മലയാളം — speak or type in Malayalam", size=13, color=BLACK),
                    ft.Text("• English — speak or type in English", size=13, color=BLACK),
                    ft.Text("• Output speech — always Malayalam", size=13, color=BLACK),
                    ft.Row(
                        [
                            ft.OutlinedButton("Back", on_click=do_language_back),
                            ft.FilledButton(
                                "Next — Purpose",
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

    # ------------------------------------------------------------------
    # Screen 3 — Purpose of visit
    # ------------------------------------------------------------------
    purpose_title = ft.Text("Purpose of visit", size=26, weight=ft.FontWeight.BOLD, color=BLACK)
    purpose_caption = ft.Text("How can we help you today?", size=14, color=BLACK)
    purpose_dd = ft.Dropdown(
        label="Purpose",
        value="College information",
        options=[
            ft.dropdown.Option("General questions"),
            ft.dropdown.Option("College information"),
        ],
        border_radius=12,
        filled=True,
        bgcolor=IVORY,
        color=BLACK,
        label_style=ft.TextStyle(color=BLACK),
    )

    PURPOSE_MAP = {
        "General questions": "general",
        "College information": "college",
        "പൊതുവായ ചോദ്യങ്ങൾ": "general",
        "കോളേജ് വിവരങ്ങൾ": "college",
    }

    def refresh_purpose_labels():
        if state["lang"] == "ml":
            purpose_title.value = "സന്ദർശനത്തിന്റെ ഉദ്ദേശ്യം"
            purpose_caption.value = "നിങ്ങൾ എന്തിനാണ് വന്നത്? (മറുപടി മലയാളത്തിൽ)"
            purpose_dd.label = "ഉദ്ദേശ്യം"
            purpose_dd.options = [
                ft.dropdown.Option("പൊതുവായ ചോദ്യങ്ങൾ"),
                ft.dropdown.Option("കോളേജ് വിവരങ്ങൾ"),
            ]
            purpose_dd.value = "കോളേജ് വിവരങ്ങൾ"
        else:
            purpose_title.value = "Purpose of visit"
            purpose_caption.value = "How can we help you today? (Replies spoken in Malayalam)"
            purpose_dd.label = "Purpose"
            purpose_dd.options = [
                ft.dropdown.Option("General questions"),
                ft.dropdown.Option("College information"),
            ]
            purpose_dd.value = "College information"

    def do_purpose_next(_=None):
        state["purpose"] = PURPOSE_MAP.get(purpose_dd.value or "", "college")
        state["welcomed"] = False
        chat.controls.clear()
        show_talkbot()

    def do_purpose_back(_=None):
        show_language()

    purpose_screen = ft.Container(
        expand=True,
        bgcolor=IVORY,
        padding=24,
        content=ft.Column(
            [
                ft.Container(height=20),
                ft.Text("Step 3 of 4", size=12, color=BLACK),
                purpose_title,
                purpose_caption,
                ft.Container(height=8),
                card(
                    ft.Text("Select purpose", weight=ft.FontWeight.W_600, color=BLACK),
                    purpose_dd,
                    ft.Text(
                        "General — greetings & help · College — admissions, fees, hostel…",
                        size=13,
                        color=BLACK,
                    ),
                    ft.Row(
                        [
                            ft.OutlinedButton("Back", on_click=do_purpose_back),
                            ft.FilledButton(
                                "Start chatting",
                                icon=ft.Icons.CHAT,
                                on_click=do_purpose_next,
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

    # ------------------------------------------------------------------
    # Screen 4 — TalkBot
    # ------------------------------------------------------------------
    greet_label = ft.Text("", size=12, color="#A5F3FC")

    talkbot_header = ft.Container(
        content=ft.Row(
            [
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    icon_color=ft.Colors.WHITE,
                    tooltip="Change purpose",
                    on_click=lambda e: show_purpose(),
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
                        ft.Text(
                            "CodeAI · Reception",
                            size=17,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.WHITE,
                        ),
                        greet_label,
                    ],
                    spacing=1,
                    expand=True,
                ),
                ft.IconButton(
                    icon=ft.Icons.LANGUAGE,
                    icon_color=ft.Colors.WHITE,
                    tooltip="Change language",
                    on_click=lambda e: show_language(),
                ),
                ft.IconButton(
                    icon=ft.Icons.LOGOUT,
                    icon_color=ft.Colors.WHITE,
                    tooltip="Logout",
                    on_click=lambda e: show_login(reset=True),
                ),
            ],
            spacing=4,
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
    # Navigation
    # ------------------------------------------------------------------
    def show_login(reset: bool = False):
        if reset:
            state["name"] = ""
            state["phone"] = ""
            state["lang"] = "ml"
            state["purpose"] = "college"
            state["otp_sent"] = False
            state["welcomed"] = False
            state["is_admin"] = False
            name_field.value = ""
            phone_field.value = ""
            otp_field.value = ""
            otp_field.visible = False
            verify_btn.visible = False
            otp_info.visible = False
            otp_info.value = ""
            send_otp_btn.text = "Send OTP"
            login_error.value = ""
            admin_user_field.value = ""
            admin_pass_field.value = ""
            admin_status.value = ""
            chat.controls.clear()
            set_login_mode("visitor")
        root.content = login_screen
        page.update()

    def show_admin():
        if not state.get("is_admin"):
            show_login(reset=True)
            return
        refresh_admin_fields()
        admin_status.value = ""
        root.content = admin_screen
        page.update()

    def show_language():
        lang_hello.value = f"Hello, {state['name']}"
        root.content = language_screen
        page.update()

    def show_purpose():
        refresh_purpose_labels()
        root.content = purpose_screen
        page.update()

    def show_talkbot():
        load_college()
        in_label = LANG_LABELS.get(state["lang"], "മലയാളം input")
        purpose_key = state["purpose"]
        purpose_label = PURPOSE_LABELS.get(purpose_key, PURPOSE_LABELS["college"])["ml"]
        greet_label.value = f"{state['name']} · {in_label} · {purpose_label}"
        if state["lang"] == "en":
            question.hint_text = "Type in English… (admission, fees, hostel)"
        else:
            question.hint_text = "മലയാളത്തിൽ ടൈപ്പ് ചെയ്യുക… (അഡ്മിഷൻ, ഫീസ്)"
        status.value = "Input: EN/ML · Spoken reply: Malayalam · type or tap mic"

        if not state["welcomed"]:
            welcome = greeting(state["name"])
            if state["purpose"] == "college":
                welcome = f"{welcome}\n\n{college_overview()}"
            add_bubble("Asha", welcome)
            state["welcomed"] = True
            page.run_task(speak_malayalam, welcome)

        root.content = talkbot_screen
        page.update()

    root.content = login_screen
    page.add(root)


if os.environ.get("TALKBOT_WEB") == "1":
    ft.run(main, view=ft.AppView.WEB_BROWSER, host="127.0.0.1", port=8550)
else:
    ft.run(main)
