[app]
title = OnlyAudio Remote
package.name = remote
package.domain = org.audiofeel
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0

# On utilise Python 3.10 qui est le standard actuel pour Android
requirements = python3==3.10.12,kivy,kivymd,pillow,requests,urllib3,chardet,idna,openssl

orientation = portrait
fullscreen = 0
android.permissions = android.permission.INTERNET

# Configuration Android 14 (API 34) avec rétrocompatibilité Android 5 (API 21)
android.api = 34
android.minapi = 21
android.ndk = 25b
android.private_storage = True
android.accept_sdk_license = True
android.archs = arm64-v8a, armeabi-v7a

# --- SECTION CRUCIALE POUR ÉVITER LES ERREURS ---
p4a.branch = develop
p4a.bootstrap = sdl2

[buildozer]
log_level = 2
warn_on_root = 1
