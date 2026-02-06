[app]

# (str) Title of your application
title = OnlyAudio Remote

# (str) Package name
package.name = remote

# (str) Package domain (needed for android/ios packaging)
package.domain = org.audiofeel

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas

# (str) Application versioning (method 1)
version = 0.1

# (list) Application requirements
# J'ai gardé vos libs et spécifié python 3.11 pour la stabilité
requirements = python3==3.11,kivy,kivymd,pillow,requests,urllib3,chardet,idna,openssl

# (list) Supported orientations
orientation = portrait

#
# Android specific
#

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) Permissions
android.permissions = android.permission.INTERNET

# (int) Target Android API
android.api = 34

# (int) Minimum API
android.minapi = 21

# (bool) Use --private data storage (True) or --dir public storage (False)
android.private_storage = True

# (str) Android entry point
android.entrypoint = org.kivy.android.PythonActivity

# (list) The Android archs to build for
android.archs = arm64-v8a, armeabi-v7a

# (bool) enables Android auto backup feature
android.allow_backup = True

#
# Python for android (p4a) specific
#

# --- MODIFICATION CRUCIALE ICI ---
# On utilise la branche 'develop' pour avoir les liens de téléchargement corrigés (fix erreur 404)
p4a.branch = develop

# (str) Bootstrap to use for android builds
p4a.bootstrap = sdl2


[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1