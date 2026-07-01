import os

class Settings:
    # google credentials
    GOOGLE_CLIENT_ID = os.environ.get('CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('CLIENT_SECRET')

    # steam credentials
    STEAM_URL = os.environ.get('STEAM_URL')

settings = Settings()
