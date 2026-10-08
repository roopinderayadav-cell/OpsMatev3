# OpsMate - Your AI Operations Companion (NORAM · EUROPE · APAC)

Agents ask questions in plain words (typos and Hindi/Kannada/Telugu in English letters
are fine) or paste a screenshot, and get one short answer with its SOP source and a
confidence level. When OpsMate is not sure it says:
"I do not have answer to this question, please consult with your team supervisor."

## What's new in OpsMate (v3, upgraded from Compass)
- New look based on the OpsMate mock-up: home screen, topic buttons, Recent Questions,
  Important Updates, answer card with confidence, sources with View.
- More accurate: spelling + Hinglish fix, coverage check, re-ranking, optional Gemini
  semantic search. Tested: 26/26 real questions right, 10/10 out-of-scope questions refused.
- Never guesses: low confidence -> the supervisor message (config.FALLBACK_TEXT).
- Conflict check: if two documents give different answers -> shows both + CONFLICT_TEXT.
- Learns by itself: 👍 from 2 people (or 1 admin) saves the answer; 👍/👎 move passages
  up/down for similar questions; 👎 switches off a wrong learned answer; new uploads
  re-check open gaps.
- Knowledge Gaps page: unanswered / conflicting / 👎 questions grouped, with status,
  owner, note, "write the answer now", Excel export.
- Dashboard: KPIs, by region, top topics, trend, most asked, unanswered, feedback,
  Export to Excel (5 sheets).
- Document Management (archive/activate), Announcements, Quick Guides, Settings.
- AI: Gemini (free tier available) or Claude - optional. Voice questions with Gemini.

## Files
| File | What it does |
|---|---|
| `app.py` | Staff screens + menu |
| `admin_pages.py` | Dashboard, Document Management, Review Queue, Knowledge Gaps, Learned Answers, Settings |
| `ui.py` | Colours, header bar, cards |
| `knowledge.py` | Documents, search, 3-layer answering, self-learning, gaps, Excel export |
| `brain.py` | Spelling/Hinglish, topics, confidence, conflict check, short answers |
| `llm.py` | Connection to Gemini or Claude (optional) |
| `prompts.py` | Instructions given to the AI - edit to change answer style |
| `config.py` | All settings: name, standard replies, regions, topics, thresholds, AI keys |
| `.streamlit/config.toml` | Colours (blue theme) |
| `sample_docs/` | Demo documents loaded automatically |
| `demo_files/` | A document that deliberately conflicts with the FAQ - upload it to EUROPE to demo the conflict warning |

## Run on a laptop
Double-click `START_APP.bat` (installs libraries the first time), or:
`python -m pip install -r requirements.txt` then `python -m streamlit run app.py`

## Turn on AI (optional)
Streamlit Cloud → App → Settings → Secrets:
```
ADMIN_PASSWORD = "your-admin-password"
GEMINI_API_KEY = "your-gemini-key"
```
Laptop: `setx GEMINI_API_KEY "your-gemini-key"` once, then restart.
Then Settings → "Test AI connection" and "Build semantic index now".
Gemini free tier: Google may use what you send to improve its products - use sample /
non-confidential SOPs on the free tier.
