[app]
title = OnlyAudio Remote
package.name = remote
package.domain = org.audiofeel
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0

# MODIFICATION ICI : On laisse python3 tout court (plus robuste)
requirements = python3,kivy,kivymd,pillow,requests,urllib3,chardet,idna,openssl

orientation = portrait
fullscreen = 0
android.permissions = android.permission.INTERNET

# Configuration Android 14
android.api = 34
android.minapi = 21
android.ndk = 25b
android.private_storage = True
android.accept_sdk_license = True
android.archs = arm64-v8a, armeabi-v7a

# Configuration P4A
p4a.branch = develop
p4a.bootstrap = sdl2

[buildozer]
log_level = 2
warn_on_root = 1
