# CodeAI Malayalam Receptionist (Flet APK)

Android / desktop app: OTP login → input language (EN/ML) → purpose → chat.

- **Visitor:** English or Malayalam input (text + mic); spoken replies in Malayalam
- **Admin:** password login to edit college settings used by the whole app

## Flow

### Visitor
1. OTP login  
2. Choose input language (English / മലയാളം)  
3. Purpose of visit (general / college info)  
4. TalkBot — type or speak; replies are spoken in Malayalam  

### Admin
1. On login screen choose **Admin** tab  
2. Username / password (default: `admin` / `admin123`)  
3. Edit college name, phone, notes, etc. → **Save settings**  
4. Visitors see the updated info in chat  

Override credentials (optional):

```bash
set CODEAI_ADMIN_USER=admin
set CODEAI_ADMIN_PASS=your_password
```

## Setup

```bash
cd apk_app
pip install -r requirements.txt
```

Optional:

```bash
set GEMINI_API_KEY=your_key_here
```

## Run on Windows (test)

```bash
cd apk_app
flet run main.py
```

Or:

```bash
python main.py
```

## Build Android APK (Windows)

Do **not** build from a path with an apostrophe (`study's`). Use `build_apk.bat`, or:

```bat
mklink /J C:\Users\ABHIJITH\apk_app_build "C:\Users\ABHIJITH\OneDrive\Documents\study's\apk_app"
cd /d C:\Users\ABHIJITH\apk_app_build
flet build apk --arch arm64
```

APK output:

`apk_app\build\apk\` (or the junction’s `build\apk\`)

Install on phone: copy APK → allow unknown sources → install.

## Notes

- Mic needs `RECORD_AUDIO` (already in `pyproject.toml`)
- TTS / Gemini / speech recognition need internet on the phone
- College facts live in `bot.py` defaults + `college_config.json` after admin saves
- Do not ship a public APK with a hardcoded API key
