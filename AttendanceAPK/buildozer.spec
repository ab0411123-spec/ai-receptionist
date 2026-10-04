[app]
title = Attendance
package.name = attendance
package.domain = org.stmarys
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,csv,json
source.include_patterns = main.py
version = 1.0.0
requirements = python3,kivy==2.3.0,kivymd==1.2.0,pillow,android
orientation = portrait
fullscreen = 0
android.permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.api = 33
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a
android.accept_sdk_license = True
android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 1
