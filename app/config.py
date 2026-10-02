from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

class Config:
    SECRET_KEY = os.environ.get('SHARECIRCLE_SECRET_KEY', 'sharecircle-local-dev-key-2026')
    DATABASE = os.environ.get('SHARECIRCLE_DATABASE', str(BASE_DIR / 'sharecircle.db'))
    VERSION = '1.0'
    HACKATHON_UTILITIES_ENABLED = os.environ.get('SHARECIRCLE_HACKATHON_UTILITIES', '1').lower() not in {'0', 'false', 'no', 'off'}
