[app]
# Basic app info
title = Threesome
package.name = threesome
package.domain = com.example  # change this to your domain

# Source
source.dir = .
# include kv, assets and json configs
source.include_exts = py,kv,png,jpg,jpeg,json
source.include_patterns = ui/*.kv, ui/assets/*, board_builder/saved_configs/*.json

# Version
version = 0.1.0

# Kivy / Python requirements
requirements = python3,kivy

# Orientation / Window
orientation = landscape
fullscreen = 1

# Android
android.archs = arm64-v8a, armeabi-v7a, x86_64
# If needed later:
# android.permissions = WAKE_LOCK, INTERNET

# Signing (fill when building release AAB)
# android.release_keystore = threesome.keystore
# android.release_keyalias = threesome
# android.release_keystore_password =
# android.release_keyalias_password =

# Optional assets
# icon.filename = ui/assets/icon.png
# presplash.filename = ui/assets/presplash.png

[buildozer]
log_level = 2
warn_on_root = 0
