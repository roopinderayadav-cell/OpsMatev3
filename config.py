"""
config.py - All OpsMate settings in one place.
Change values here (or in Streamlit Secrets / environment variables).
"""
import os
from pathlib import Path


def _secret(name, default=""):
    """Read a setting from an environment variable, or from Streamlit Secrets."""
    value = os.getenv(name)
    if value:
        return value
    try:
        import streamlit as st
        return str(st.secrets.get(name, default))
    except Exception:
        return default


# ---- App identity ---------------------------------------------------------
APP_NAME = "OpsMate"
TAGLINE = "Your AI Operations Companion"
COMPANY_NAME = "Your Company"

# ---- The two standard replies (edit the wording here) -----------------------
FALLBACK_TEXT = "I do not have answer to this question, please consult with your team supervisor."
CONFLICT_TEXT = ("I found different answers to this question in more than one document, so I cannot "
                 "confirm which one is correct. " + FALLBACK_TEXT)

# ---- Regions --------------------------------------------------------------
REGIONS = ["NORAM", "EUROPE", "APAC"]
GLOBAL_REGION = "GLOBAL"            # GLOBAL documents are visible to every region

# ---- Topics (home-screen buttons + dashboard grouping) --------------------
# name: words that put a question into that topic
TOPICS = {
    "Ticketing": "ticket issue issuance ttp tst pnr booking book void e-ticket eticket itinerary "
                 "name correction spelling passenger",
    "Refunds": "refund refunds refundable money back cancellation fee refnd",
    "Exchanges": "exchange reissue revalidation date change change fee atc rebook",
    "OBT": "obt online booking tool self booking self-booking concur cytric",
    "Invoicing": "invoice invoicing billing credit note supplier gst vat",
    "Fare Rules": "fare rule rules category cat 16 31 33 penalty fare basis",
    "GDS (Amadeus/Sabre)": "amadeus sabre galileo gds command cryptic entry twd fxp tqt",
    "Profiles": "profile profiles traveller profile frequent flyer ffp passport details",
    "Travel Policy": "policy approval business class economy hotel preferred out of policy",
    "Quality / Errors": "error errors adm quality debit memo mistake issue failed invalid",
}
TOPIC_LABELS = {"GDS (Amadeus/Sabre)": "GDS", "Quality / Errors": "Quality"}   # short button text
TOPIC_ICONS = {"Ticketing": "✈️", "Refunds": "💸", "Exchanges": "🔄", "OBT": "🧳", "Invoicing": "🧾",
               "Fare Rules": "📜", "GDS (Amadeus/Sabre)": "🖥️", "Profiles": "👤",
               "Travel Policy": "📋", "Quality / Errors": "⚠️"}

# ---- Document categories --------------------------------------------------
DOC_TYPES = ["SOP", "FAQ", "Quick Guide", "Process Knowledge", "Policy", "Other"]
ALLOWED_EXTENSIONS = ["pdf", "docx", "pptx", "xlsx", "txt", "md", "csv", "png", "jpg", "jpeg"]

# ---- Admin access ---------------------------------------------------------
ADMIN_PASSWORD = _secret("ADMIN_PASSWORD", "admin123")

# ---- Demo mode ------------------------------------------------------------
# Load sample_docs/ automatically when the knowledge base is empty (free hosting
# wipes data on restart). File names start with the region: NORAM_..., GLOBAL_...
AUTO_LOAD_SAMPLES = os.getenv("AUTO_LOAD_SAMPLES", "true").lower() == "true"

# ---- Storage --------------------------------------------------------------
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
DB_PATH = DATA_DIR / "knowledge.db"

# ---- Search tuning --------------------------------------------------------
CHUNK_SIZE = 700          # characters per knowledge piece
CHUNK_OVERLAP = 150
CANDIDATES = 8            # passages compared for each answer (from all documents)
PER_DOC = 2               # max passages from one document -> answers mix documents
LEARNED_BOOST = 1.25      # verified answers (written by the process team)
AUTO_LEARNED_BOOST = 1.10 # answers OpsMate learned by itself from 👍 votes

# Confidence without AI (word-match score of the best passage)
CONF_HIGH = 0.22
CONF_MEDIUM = 0.11        # below this OpsMate gives FALLBACK_TEXT instead of guessing
# Confidence with Gemini semantic search (cosine similarity of the best passage)
SEM_HIGH = 0.72
SEM_MEDIUM = 0.60

MAX_ANSWER_WORDS = 60     # "short" answers stay under this many words

# ---- Self-learning --------------------------------------------------------
AUTO_LEARN = True         # save answers that staff mark 👍 as "auto-learned"
AUTO_LEARN_MIN_VOTES = 2  # 👍 from this many DIFFERENT people before an answer is auto-learned
                          # (an admin's 👍 counts as enough on its own)
FEEDBACK_SIMILARITY = 0.55  # how similar a new question must be to reuse past 👍/👎

# ---- AI providers ----------------------------------------------------------
# OpsMate works with NO key (free, offline). Add ONE key to turn on AI:
#   Gemini (free tier available): GEMINI_API_KEY  -> also gives semantic search
#   Claude (paid):                ANTHROPIC_API_KEY
# Streamlit Cloud: App -> Settings -> Secrets. Laptop: setx GEMINI_API_KEY "..."
GEMINI_API_KEY = _secret("GEMINI_API_KEY", "")
ANTHROPIC_API_KEY = _secret("ANTHROPIC_API_KEY", "")
AI_PROVIDER = _secret("AI_PROVIDER", "auto")   # auto | gemini | claude | off

GEMINI_MODEL = _secret("GEMINI_MODEL", "gemini-3.8-flash")            # answers, screenshots
GEMINI_FAST_MODEL = _secret("GEMINI_FAST_MODEL", "gemini-3.5-flash-lite")  # rephrasing
GEMINI_EMBED_MODEL = _secret("GEMINI_EMBED_MODEL", "gemini-embedding-001")
EMBED_DIM = 768

CLAUDE_MODEL = _secret("CLAUDE_MODEL", "claude-sonnet-5-5")
CLAUDE_FAST_MODEL = _secret("CLAUDE_FAST_MODEL", "claude-haiku-4-5-20251001")

# ---- Images inside documents ----------------------------------------------
READ_DOC_IMAGES = True    # read screenshots/tables/scans inside uploaded files (AI mode)
MAX_IMAGES_PER_DOC = 25
MIN_IMAGE_PX = 120
