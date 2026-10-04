# Attendance APK

Professional teacher attendance app for **St. Mary's Polytechnic College Palakkad**.

## Features

- Clean login screen
- Class details (dept, year, semester, subject)
- Tap roll numbers to mark Present / Absent
- Save to CSV
- Admin can view records

## Demo logins

| Username  | Password   |
|-----------|------------|
| neethu    | neethu123  |
| teacher2  | pass456    |
| jinto     | jinto123   |
| admin     | admin123   |

## Run on Windows (preview)

```bash
cd AttendanceAPK
pip install -r requirements.txt
python main.py
```

## Get the APK

### Option A — GitHub Actions (easiest on Windows)

1. Push this folder to a GitHub repo
2. Open **Actions** → **Build APK** → **Run workflow**
3. Download the APK from Artifacts

### Option B — WSL / Linux

```bash
cd AttendanceAPK
pip install buildozer cython
buildozer android debug
```

APK path: `bin/attendance-1.0.0-arm64-v8a-debug.apk`

Install on phone: enable **Install unknown apps**, then open the APK.
