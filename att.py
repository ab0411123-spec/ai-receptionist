"""
Teacher Attendance — launches the professional APK app.

Prefer running from the project folder:
  cd AttendanceAPK
  pip install -r requirements.txt
  python main.py
"""

import runpy
import sys
from pathlib import Path

app_dir = Path(__file__).resolve().parent / "AttendanceAPK"
sys.path.insert(0, str(app_dir))
runpy.run_path(str(app_dir / "main.py"), run_name="__main__")
