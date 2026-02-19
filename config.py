import os
from pathlib import Path

CHECK_CHANNELS_EVERY_HOURS = float(os.getenv('CHECK_CHANNELS_EVERY_HOURS', '24'))
SECRETS_DIR = Path(os.getenv('SECRETS_DIR', '/app/secrets'))
CONFIG_DIR = Path(os.getenv('CONFIG_DIR', '/app/config'))

GOOGLE_API_KEY_FILE = SECRETS_DIR / "client_secret.json"
TOKEN_FILE = SECRETS_DIR / "token.pickle"
CONFIG_FILE = CONFIG_DIR / "config.json"  