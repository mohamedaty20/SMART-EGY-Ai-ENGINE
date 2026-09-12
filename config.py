"""
config.py — environment, constants, and shared Gemini client.
"""
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = "gemini-2.5-flash"

client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# Where the SQLite database lives (created automatically at first run)
DB_PATH = os.path.join(os.path.dirname(__file__), "defect_data.db")
