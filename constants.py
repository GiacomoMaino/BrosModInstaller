import os

API_KEY = "" #Google Drive API Key
MAIN_FOLDER = "" #Google Drive Folder ID
MODS_FOLDER = os.path.join(os.getenv('APPDATA'), ".minecraft", "mods")
VERSION_FOLDER = os.path.join(os.getenv('APPDATA'), ".minecraft", "versions")
TEMP_FOLDER = os.path.join(os.getenv('APPDATA'), "bros-loader", "mods")
PROFILES_FILE = os.path.join(os.getenv('APPDATA'), ".minecraft", "launcher_profiles.json")