"""
Attendance — Professional Teacher Attendance APK
College: St. Mary's Polytechnic College Palakkad

Run on PC:  pip install kivymd kivy && python main.py
Build APK:  buildozer android debug   (Linux / WSL)
"""

import csv
import os
from datetime import date

from kivy.core.window import Window
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.storage.jsonstore import JsonStore
from kivy.utils import platform
from kivymd.app import MDApp
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDLabel
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.screen import MDScreen
from kivymd.uix.snackbar import Snackbar

# Phone-sized window when testing on desktop
if platform == "win":
    Window.size = (390, 780)

TEACHERS = {
    "neethu": "neethu123",
    "teacher2": "pass456",
    "jinto": "jinto123",
    "admin": "admin123",
}

DEPARTMENTS = ["CT", "CE", "EEE", "MECH A", "MECH B", "AU", "FS"]
YEARS = ["1st Year", "2nd Year", "3rd Year"]
SEMESTERS = ["1", "2", "3", "4", "5", "6"]
CSV_FILE = "attendance.csv"

KV = """
#:import hex kivy.utils.get_color_from_hex

MDScreenManager:
    LoginScreen:
    HomeScreen:
    RecordsScreen:

<LoginScreen>:
    name: "login"
    md_bg_color: hex("#F4F7F6")

    MDBoxLayout:
        orientation: "vertical"
        padding: "28dp"
        spacing: "12dp"

        Widget:
            size_hint_y: 0.12

        MDLabel:
            text: "ATTENDANCE"
            font_style: "H4"
            bold: True
            halign: "center"
            theme_text_color: "Custom"
            text_color: hex("#0D7377")
            size_hint_y: None
            height: self.texture_size[1]

        MDLabel:
            text: "St. Mary's Polytechnic College"
            font_style: "Caption"
            halign: "center"
            theme_text_color: "Secondary"
            size_hint_y: None
            height: self.texture_size[1]

        Widget:
            size_hint_y: None
            height: "28dp"

        MDCard:
            orientation: "vertical"
            padding: "22dp"
            spacing: "8dp"
            size_hint_y: None
            height: "280dp"
            radius: [16]
            elevation: 2
            md_bg_color: 1, 1, 1, 1

            MDLabel:
                text: "Sign in"
                font_style: "H6"
                size_hint_y: None
                height: self.texture_size[1]

            MDTextField:
                id: username
                hint_text: "Username"
                mode: "rectangle"
                size_hint_y: None
                height: "48dp"

            MDTextField:
                id: password
                hint_text: "Password"
                password: True
                mode: "rectangle"
                size_hint_y: None
                height: "48dp"

            Widget:
                size_hint_y: None
                height: "8dp"

            MDRaisedButton:
                text: "LOGIN"
                size_hint_x: 1
                md_bg_color: hex("#0D7377")
                on_release: app.do_login()

        Widget:

<HomeScreen>:
    name: "home"
    md_bg_color: hex("#F4F7F6")

    MDBoxLayout:
        orientation: "vertical"

        MDTopAppBar:
            id: topbar
            title: "Mark Attendance"
            elevation: 1
            md_bg_color: hex("#0D7377")
            specific_text_color: 1, 1, 1, 1
            left_action_items: [["logout", lambda x: app.do_logout()]]
            right_action_items: [["clipboard-list-outline", lambda x: app.open_records()]]

        ScrollView:
            MDBoxLayout:
                orientation: "vertical"
                padding: "16dp"
                spacing: "12dp"
                adaptive_height: True

                MDLabel:
                    id: teacher_label
                    text: ""
                    font_style: "Caption"
                    theme_text_color: "Secondary"
                    size_hint_y: None
                    height: self.texture_size[1]

                MDCard:
                    orientation: "vertical"
                    padding: "16dp"
                    spacing: "6dp"
                    size_hint_y: None
                    height: "340dp"
                    radius: [14]
                    elevation: 1
                    md_bg_color: 1, 1, 1, 1

                    MDLabel:
                        text: "Class details"
                        font_style: "Subtitle1"
                        bold: True
                        size_hint_y: None
                        height: self.texture_size[1]

                    MDTextField:
                        id: college
                        hint_text: "College"
                        text: "St.Mary's Polytechnic College Palakkad"
                        mode: "rectangle"
                        font_size: "13sp"

                    MDBoxLayout:
                        size_hint_y: None
                        height: "56dp"
                        spacing: "8dp"
                        MDTextField:
                            id: department
                            hint_text: "Dept"
                            text: "CT"
                            readonly: True
                            mode: "rectangle"
                            on_focus: if self.focus: app.open_menu("department")
                        MDTextField:
                            id: year
                            hint_text: "Year"
                            text: "1st Year"
                            readonly: True
                            mode: "rectangle"
                            on_focus: if self.focus: app.open_menu("year")

                    MDBoxLayout:
                        size_hint_y: None
                        height: "56dp"
                        spacing: "8dp"
                        MDTextField:
                            id: semester
                            hint_text: "Sem"
                            text: "1"
                            readonly: True
                            mode: "rectangle"
                            on_focus: if self.focus: app.open_menu("semester")
                        MDTextField:
                            id: subject
                            hint_text: "Subject"
                            mode: "rectangle"

                    MDBoxLayout:
                        size_hint_y: None
                        height: "56dp"
                        spacing: "8dp"
                        MDTextField:
                            id: end_roll
                            hint_text: "Students (1 to N)"
                            text: "30"
                            input_filter: "int"
                            mode: "rectangle"
                        MDRaisedButton:
                            text: "LOAD"
                            md_bg_color: hex("#0D7377")
                            pos_hint: {"center_y": 0.5}
                            on_release: app.load_rolls()

                MDLabel:
                    id: summary_label
                    text: "Load students to mark attendance"
                    font_style: "Caption"
                    theme_text_color: "Hint"
                    size_hint_y: None
                    height: self.texture_size[1]

                MDGridLayout:
                    id: roll_grid
                    cols: 3
                    spacing: "8dp"
                    padding: "2dp"
                    size_hint_y: None
                    height: self.minimum_height
                    adaptive_height: True

                Widget:
                    size_hint_y: None
                    height: "72dp"

        MDBoxLayout:
            size_hint_y: None
            height: "64dp"
            padding: "12dp"
            md_bg_color: 1, 1, 1, 1
            MDRaisedButton:
                text: "SAVE ATTENDANCE"
                size_hint_x: 1
                md_bg_color: hex("#0D7377")
                on_release: app.save_attendance()

<RecordsScreen>:
    name: "records"
    md_bg_color: hex("#F4F7F6")

    MDBoxLayout:
        orientation: "vertical"
        MDTopAppBar:
            title: "Records"
            elevation: 1
            md_bg_color: hex("#0D7377")
            specific_text_color: 1, 1, 1, 1
            left_action_items: [["arrow-left", lambda x: app.go_home()]]
            right_action_items: [["delete-outline", lambda x: app.confirm_clear_records()]]
        ScrollView:
            MDLabel:
                id: records_label
                text: "No records yet."
                padding: "16dp"
                size_hint_y: None
                height: self.texture_size[1]
                text_size: self.width, None
        MDBoxLayout:
            size_hint_y: None
            height: "64dp"
            padding: "12dp"
            spacing: "8dp"
            md_bg_color: 1, 1, 1, 1
            MDRaisedButton:
                text: "CLEAR ALL RECORDS"
                size_hint_x: 1
                md_bg_color: hex("#C62828")
                on_release: app.confirm_clear_records()
"""


class LoginScreen(MDScreen):
    pass


class HomeScreen(MDScreen):
    pass


class RecordsScreen(MDScreen):
    pass


class RollChip(MDCard):
    """Compact present/absent toggle chip."""

    def __init__(self, roll_no, on_toggle=None, **kwargs):
        super().__init__(**kwargs)
        self.roll_no = roll_no
        self.present = True
        self.on_toggle = on_toggle
        self.size_hint_y = None
        self.height = dp(52)
        self.radius = [10]
        self.elevation = 0
        self.padding = dp(4)
        self.ripple_behavior = True
        self._label = MDLabel(
            text=str(roll_no),
            halign="center",
            bold=True,
            theme_text_color="Custom",
        )
        self.add_widget(self._label)
        self._paint()
        self.bind(on_release=self._toggle)

    def _paint(self):
        if self.present:
            self.md_bg_color = (0.05, 0.45, 0.47, 1)  # teal
            self._label.text_color = (1, 1, 1, 1)
            self._label.text = f"{self.roll_no}"
        else:
            self.md_bg_color = (0.93, 0.93, 0.93, 1)
            self._label.text_color = (0.4, 0.4, 0.4, 1)
            self._label.text = f"{self.roll_no}"

    def _toggle(self, *_):
        self.present = not self.present
        self._paint()
        if self.on_toggle:
            self.on_toggle()


class AttendanceApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "Attendance"
        self.teacher = ""
        self.roll_chips = {}
        self.menus = {}
        self.clear_dialog = None
        self.session = JsonStore("session.json")

    def build(self):
        self.theme_cls.primary_palette = "Teal"
        self.theme_cls.primary_hue = "700"
        self.theme_cls.theme_style = "Light"
        return Builder.load_string(KV)

    def on_start(self):
        if self.session.exists("user"):
            self.teacher = self.session.get("user")["name"]
            self._show_home()

    def _toast(self, message):
        try:
            Snackbar(text=message, duration=2).open()
        except Exception:
            # Newer KivyMD snackbar API fallback
            from kivymd.uix.snackbar import MDSnackbar

            MDSnackbar(MDLabel(text=message), y=dp(24), pos_hint={"center_x": 0.5}).open()

    def do_login(self):
        screen = self.root.get_screen("login")
        user = screen.ids.username.text.strip()
        pwd = screen.ids.password.text.strip()

        if user in TEACHERS and TEACHERS[user] == pwd:
            self.teacher = user
            self.session.put("user", name=user)
            screen.ids.username.text = ""
            screen.ids.password.text = ""
            self._show_home()
            self._toast("Welcome, " + user)
        else:
            self._toast("Invalid username or password")

    def do_logout(self):
        self.teacher = ""
        if self.session.exists("user"):
            self.session.delete("user")
        self.roll_chips.clear()
        home = self.root.get_screen("home")
        home.ids.roll_grid.clear_widgets()
        home.ids.summary_label.text = "Load students to mark attendance"
        self.root.current = "login"

    def _show_home(self):
        home = self.root.get_screen("home")
        home.ids.teacher_label.text = f"Signed in as {self.teacher}"
        self.root.current = "home"

    def go_home(self):
        self.root.current = "home"

    def open_menu(self, field_id):
        options = {
            "department": DEPARTMENTS,
            "year": YEARS,
            "semester": SEMESTERS,
        }[field_id]
        field = self.root.get_screen("home").ids[field_id]

        def choose(value, fid=field_id):
            self.root.get_screen("home").ids[fid].text = value
            if fid in self.menus and self.menus[fid]:
                self.menus[fid].dismiss()

        items = [
            {
                "text": opt,
                "viewclass": "OneLineListItem",
                "height": dp(44),
                "on_release": lambda x=opt: choose(x),
            }
            for opt in options
        ]
        menu = MDDropdownMenu(caller=field, items=items, width_mult=3)
        self.menus[field_id] = menu
        menu.open()

    def _update_summary(self):
        if not self.roll_chips:
            return
        present = sum(1 for c in self.roll_chips.values() if c.present)
        absent = len(self.roll_chips) - present
        self.root.get_screen("home").ids.summary_label.text = (
            f"Present {present}  ·  Absent {absent}  ·  Tap a number to toggle"
        )

    def load_rolls(self):
        home = self.root.get_screen("home")
        try:
            end_roll = int(home.ids.end_roll.text.strip() or "0")
        except ValueError:
            self._toast("Enter a valid number")
            return
        if end_roll < 1 or end_roll > 120:
            self._toast("Enter students between 1 and 120")
            return

        grid = home.ids.roll_grid
        grid.clear_widgets()
        self.roll_chips.clear()

        for roll in range(1, end_roll + 1):
            chip = RollChip(roll, on_toggle=self._update_summary)
            self.roll_chips[roll] = chip
            grid.add_widget(chip)

        self._update_summary()
        self._toast(f"Loaded {end_roll} students")

    def save_attendance(self):
        if not self.roll_chips:
            self._toast("Load students first")
            return

        home = self.root.get_screen("home")
        subject = home.ids.subject.text.strip()
        if not subject:
            self._toast("Enter subject name")
            return

        today_str = str(date.today())
        fields = [
            "Date",
            "Teacher",
            "College",
            "Department",
            "Year",
            "Semester",
            "Subject",
            "Roll No",
            "Status",
        ]
        rows = [
            {
                "Date": today_str,
                "Teacher": self.teacher,
                "College": home.ids.college.text.strip(),
                "Department": home.ids.department.text.strip(),
                "Year": home.ids.year.text.strip(),
                "Semester": home.ids.semester.text.strip(),
                "Subject": subject,
                "Roll No": roll,
                "Status": "Present" if chip.present else "Absent",
            }
            for roll, chip in self.roll_chips.items()
        ]

        exists = os.path.exists(CSV_FILE)
        with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            if not exists:
                writer.writeheader()
            writer.writerows(rows)

        present = sum(1 for c in self.roll_chips.values() if c.present)
        absent = len(self.roll_chips) - present
        self._toast(f"Saved — Present {present}, Absent {absent}")

    def open_records(self):
        if self.teacher != "admin":
            self._toast("Admin only")
            return
        self._refresh_records_view()
        self.root.current = "records"

    def _refresh_records_view(self):
        screen = self.root.get_screen("records")
        if not os.path.exists(CSV_FILE):
            screen.ids.records_label.text = "No records yet."
        else:
            with open(CSV_FILE, encoding="utf-8") as f:
                content = f.read().strip()
                screen.ids.records_label.text = content or "No records yet."

    def confirm_clear_records(self):
        if self.teacher != "admin":
            self._toast("Admin only")
            return
        if not os.path.exists(CSV_FILE):
            self._toast("No records to clear")
            return

        if self.clear_dialog:
            self.clear_dialog.dismiss()

        self.clear_dialog = MDDialog(
            title="Clear all records?",
            text="This will permanently delete every attendance entry. This cannot be undone.",
            buttons=[
                MDFlatButton(text="CANCEL", on_release=lambda *_: self.clear_dialog.dismiss()),
                MDRaisedButton(
                    text="CLEAR",
                    md_bg_color=(0.78, 0.16, 0.16, 1),
                    on_release=lambda *_: self.clear_records(),
                ),
            ],
        )
        self.clear_dialog.open()

    def clear_records(self):
        if self.clear_dialog:
            self.clear_dialog.dismiss()
            self.clear_dialog = None

        if self.teacher != "admin":
            self._toast("Admin only")
            return

        try:
            if os.path.exists(CSV_FILE):
                os.remove(CSV_FILE)
            self._refresh_records_view()
            self._toast("All records cleared")
        except OSError:
            self._toast("Could not clear records")


if __name__ == "__main__":
    AttendanceApp().run()
