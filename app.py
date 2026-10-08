"""
app.py - OpsMate (NORAM / EUROPE / APAC). Staff screens + navigation.
Admin screens are in admin_pages.py.   Run:  streamlit run app.py
"""
import io

import streamlit as st

import admin_pages
import brain
import config
import knowledge as kb
import llm
import ui

st.set_page_config(page_title=config.APP_NAME, page_icon="✈️", layout="wide")
ui.setup()
kb.init_db()
if config.AUTO_LOAD_SAMPLES:
    kb.load_samples_if_empty()   # demo hosting: refill sample SOPs after a restart

try:                                    # "Paste screenshot" button (optional add-on)
    from streamlit_paste_button import paste_image_button
except ImportError:
    paste_image_button = None

SUGGESTIONS = {
    "Ticketing": ["How do I issue a ticket in Amadeus?", "What should I check before issuing a ticket?",
                  "Can I void a ticket the next day?"],
    "Refunds": ["How do I process a refund?", "How long does a refund take?",
                "Is tax refundable on a non-refundable ticket?"],
    "Exchanges": ["How do I reissue a ticket using ATC?", "How do I change the travel date on an issued ticket?",
                  "What is a revalidation?"],
    "OBT": ["How do I help a traveller with OBT self booking?", "OBT self booking cancellation"],
    "Invoicing": ["How do I send an invoice to the client?", "Invoice to supplier process"],
    "Fare Rules": ["Where do I find the fare rules?", "What are Category 16, 31 and 33?"],
    "GDS (Amadeus/Sabre)": ["List of Amadeus commands", "How do I open the ticket image?",
                            "How do I create a new PNR step by step?"],
    "Profiles": ["How do I add a frequent flyer number?", "How do I add a meal or wheelchair request?"],
    "Travel Policy": ["When is business class allowed?", "When do I need approval before ticketing?"],
    "Quality / Errors": ["What is an ADM and how do I avoid it?", "What is the escalation matrix?"],
}
DEFAULT_TRY = ["How to reissue a ticket in Amadeus?", "Refund process step by step",
               "Can I void a ticket the next day?", "What is the escalation matrix?",
               "List of Amadeus commands"]

ss = st.session_state
for k, v in {"user": None, "is_admin": False, "region": config.REGIONS[0], "pasted": None,
             "paste_n": 0, "topic": None, "pending_q": None, "nav": "💬 Ask OpsMate"}.items():
    ss.setdefault(k, v)
ss.setdefault("chats", {r: [] for r in config.REGIONS})

# ---------------------------------------------------------------------------
# SIGN IN
# ---------------------------------------------------------------------------
if not ss.user:
    ui.topbar("Guest", "Not signed in", "—")
    left, right = st.columns([1.1, 1])
    with left:
        ui.hero("there")
        st.write("")
        with st.form("login"):
            name = st.text_input("Your name / employee ID")
            c1, c2 = st.columns(2)
            role = c1.radio("I am", ["Agent", "Admin / Process Owner"], horizontal=False)
            region = c2.radio("My region", config.REGIONS, horizontal=False)
            pwd = st.text_input("Admin password", type="password", help="Only for Admin / Process Owner")
            if st.form_submit_button("Sign in", type="primary", use_container_width=True):
                if not name.strip():
                    st.error("Please enter your name.")
                elif role.startswith("Admin") and pwd != config.ADMIN_PASSWORD:
                    st.error("Wrong admin password.")
                else:
                    ss.user, ss.is_admin, ss.region = name.strip(), role.startswith("Admin"), region
                    st.rerun()
    with right:
        ui.card("How OpsMate works", "<ol style='margin:0;padding-left:18px;line-height:1.9'>"
                "<li>Pick your region and a topic, or just type your question</li>"
                "<li>Spelling mistakes and Hindi / Kannada / Telugu in English letters are fine</li>"
                "<li>Paste a screenshot of an error to get help with it</li>"
                "<li>Get one short answer with its SOP source and a confidence level</li>"
                "<li>Rate it 👍 / 👎 - OpsMate learns from every rating</li></ol>")
        ui.card("When OpsMate is not sure", f"<p style='margin:0'>It never guesses. You will see: "
                f"<i>“{ui.esc(config.FALLBACK_TEXT)}”</i> and the question goes to the process team.</p>")
    st.stop()

# ---------------------------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown(f"### ✈️ {config.APP_NAME}")
    if st.button("＋ New Chat", use_container_width=True, type="primary"):
        ss.chats[ss.region] = []
        ss.topic, ss.nav = None, "💬 Ask OpsMate"
        st.rerun()
    staff_pages = ["💬 Ask OpsMate", "🕘 My Questions", "📚 Knowledge Library", "⚡ Quick Guides",
                   "📢 Announcements"]
    counts = {}
    admin_list = []
    if ss.is_admin:
        counts = {"🧠 Review Queue": len(kb.review_queue()), "🕳️ Knowledge Gaps": len(kb.knowledge_gaps())}
        admin_list = ["📊 Dashboard", "🗂️ Document Management", "🧠 Review Queue", "🕳️ Knowledge Gaps",
                      "✅ Learned Answers", "⚙️ Settings"]
    options = staff_pages + admin_list
    if ss.nav not in options:
        ss.nav = options[0]
    # fixed menu items (counts are only display text) so a click is never lost
    page = st.radio("Menu", options, key="nav", label_visibility="collapsed",
                    format_func=lambda o: f"{o} ({counts[o]})" if o in counts else o)
    st.divider()
    ss.region = st.radio("Region", config.REGIONS, index=config.REGIONS.index(ss.region),
                         format_func=lambda r: {"NORAM": "🌎 NORAM", "EUROPE": "🌍 EUROPE", "APAC": "🌏 APAC"}[r])
    st.divider()
    st.markdown("<div class='om-help'><b>Need more help?</b><br>If you are not sure, please consult "
                "your supervisor.</div>", unsafe_allow_html=True)
    st.caption(("🤖 AI: " + llm.label()) if llm.ai_on() else "📄 AI off - answers from documents")
    if st.button("Sign out"):
        ss.user, ss.is_admin = None, False
        st.rerun()

region = ss.region
ui.topbar(ss.user, "Admin" if ss.is_admin else "Agent", region)


# ---------------------------------------------------------------------------
# ANSWER RENDERING
# ---------------------------------------------------------------------------
def show_sources(sources, key):
    if not sources:
        return
    with st.expander(f"📄 Sources ({len(sources)})"):
        for j, s in enumerate(sources):
            a, b = st.columns([6, 1])
            color = ui.REGION_COLORS.get(s["region"], "#999")
            a.markdown(f"<div class='om-src' style='border-left-color:{color}'><b>{ui.esc(s['title'])}</b> · "
                       f"{ui.esc(s['type'])} · {ui.esc(s['location'])} · <i>{ui.esc(s['region'])}</i></div>",
                       unsafe_allow_html=True)
            with b.popover("View"):
                st.markdown(f"**{s['title']}** — {s['location']}")
                st.text(s["text"][:1500])
                doc = kb.get_document(s["doc_id"]) if s.get("doc_id") else None
                if doc:
                    st.download_button("⬇ Open document", kb.read_file(doc), file_name=doc["filename"],
                                       key=f"dl{key}{j}")


def render_answer(msg, i):
    result = msg.get("result", "answered")
    meta = msg.get("meta") or {}
    st.markdown(f"<div class='om-answer-head'>✈ {config.APP_NAME}</div>", unsafe_allow_html=True)
    if result == "not_found":
        st.markdown(f"<div class='om-fallback'>🛈 {ui.esc(msg['content'])}</div>", unsafe_allow_html=True)
        st.caption("Your question has been sent to the process team so the SOPs can be improved.")
    elif result == "conflict":
        st.markdown(f"<div class='om-conflict'>⚠️ <b>Different answers found.</b> {ui.esc(msg['content'])}</div>",
                    unsafe_allow_html=True)
        if meta.get("conflict_text"):
            st.markdown(f"**What each document says:** {meta['conflict_text']}")
        else:
            st.markdown("**What each document says:**")
            for s in msg.get("sources", [])[:2]:
                st.markdown(f"- **{s['title']}** ({s['region']}, {s['location']}): "
                            f"{brain.snippet(msg.get('question', ''), s['text'], s['location'])}")
        st.caption("Reported to the process team as a conflict to fix ✔")
    else:
        st.markdown(("✅ " if not msg["content"].lstrip().startswith(("|", "1.", "-")) else "") + msg["content"])
        if meta.get("important"):
            st.markdown(f"<div class='om-important'>❗ <b>Important:</b> {ui.esc(meta['important'])}</div>",
                        unsafe_allow_html=True)
        if meta.get("learned"):
            st.caption("🧠 From an answer OpsMate learned (process team / staff 👍)")
    if result != "not_found":
        show_sources(msg.get("sources"), f"{region}{i}")
    bits = [f"Answer based on {region} documents"]
    if msg.get("confidence") and result == "answered":
        bits.append(f"Confidence: **{msg['confidence'].title()}**")
    bits.append("🤖 AI" if meta.get("mode") == "ai" else "📄 documents")
    if meta.get("seconds") is not None:
        bits.append(f"⏱ {meta['seconds']} s")
    if meta.get("did_you_mean"):
        bits.append(f"🔤 understood as *{meta['did_you_mean']}*")
    st.caption(" · ".join(bits))
    for note in meta.get("notes", []):
        st.caption(f"ℹ️ {note}")
    if msg.get("qid") and result == "answered":
        if msg.get("rated") is True:
            st.caption("Thanks - OpsMate learns from your feedback ✔")
        elif msg.get("rated") != "pending":
            b1, b2, _ = st.columns([1.6, 2, 4])
            if b1.button("👍 Helpful", key=f"up{region}{i}"):
                kb.give_feedback(msg["qid"], True, trusted=ss.is_admin)
                msg["rated"] = True
                st.rerun()
            if b2.button("👎 Not helpful", key=f"dn{region}{i}"):
                msg["rated"] = "pending"
                st.rerun()
        if msg.get("rated") == "pending":
            with st.form(f"fb{region}{i}"):
                note = st.text_area("What was wrong or missing? (optional)")
                if st.form_submit_button("Send to process team"):
                    kb.give_feedback(msg["qid"], False, note)
                    msg["rated"] = True
                    st.rerun()


def ask_now(text, image=None):
    chat = ss.chats[region]
    chat.append({"role": "user", "content": text or "*(screenshot)*", "image": image})
    with st.spinner("Reading your screenshot and searching SOPs…" if image else "Searching all documents…"):
        res = kb.ask(region, text, ss.user, image=image)
    chat.append({"role": "assistant", "content": res["answer"], "sources": res["sources"],
                 "qid": res["id"], "result": res["result"], "confidence": res["confidence"],
                 "meta": res["meta"], "question": res["question"]})
    ss.pasted = None
    ss.paste_n += 1


# ---------------------------------------------------------------------------
# PAGE: Ask OpsMate (home + chat)
# ---------------------------------------------------------------------------
def page_ask():
    chat = ss.chats[region]
    if ss.pending_q:
        q, ss.pending_q = ss.pending_q, None
        ask_now(q)
        st.rerun()

    main, side = st.columns([3, 1.15], gap="large")
    with main:
        if not chat:
            ui.hero(ss.user.split()[0])
            st.write("")
            topics = list(config.TOPICS)
            for row in (topics[:5], topics[5:]):
                cols = st.columns(5)
                for c, t in zip(cols, row):
                    label = config.TOPIC_LABELS.get(t, t)
                    if c.button(f"{config.TOPIC_ICONS.get(t, '')} {label}", key=f"t_{t}", use_container_width=True,
                                type="primary" if ss.topic == t else "secondary"):
                        ss.topic = None if ss.topic == t else t
                        st.rerun()
            tries = SUGGESTIONS.get(ss.topic) if ss.topic else (kb.popular_questions(region, 5) or DEFAULT_TRY)
            st.markdown(f"<div class='om-section'>{'💡 ' + ss.topic + ' - try asking' if ss.topic else 'Try asking'}</div>",
                        unsafe_allow_html=True)
            cols = st.columns(3)
            for n, q in enumerate(tries[:6]):
                if cols[n % 3].button(q, key=f"try{n}", use_container_width=True):
                    ss.pending_q = q
                    st.rerun()
        else:
            h1, h2 = st.columns([4, 1])
            h1.markdown(f"<div class='om-section'>Conversation · {ui.region_pill(region)}</div>",
                        unsafe_allow_html=True)
            if h2.button("＋ New chat", use_container_width=True):
                ss.chats[region] = []
                st.rerun()
            for i, msg in enumerate(chat):
                with st.chat_message(msg["role"], avatar="🧑" if msg["role"] == "user" else "✈️"):
                    if msg.get("image"):
                        st.image(msg["image"], width=320)
                    if msg["role"] == "user":
                        st.markdown(msg["content"])
                    else:
                        render_answer(msg, i)

        # ---- attach a screenshot / ask by voice --------------------------------
        st.write("")
        t1, t2, t3 = st.columns([1.5, 1.6, 2.7])
        ask_shot = False
        with t1:
            if paste_image_button is not None:
                res = paste_image_button("📋 Paste screenshot", background_color=ui.BLUE,
                                         hover_background_color="#174a96", key=f"paste{ss.paste_n}")
                if res.image_data is not None:
                    buf = io.BytesIO()
                    res.image_data.save(buf, format="PNG")
                    ss.pasted = buf.getvalue()
        with t2:
            voice = None
            if llm.provider() == "gemini" and hasattr(st, "audio_input"):
                voice = st.audio_input("🎙 Ask by voice", key=f"voice{ss.paste_n}", label_visibility="collapsed")
            else:
                st.caption("🎙 Voice questions work when a Gemini key is added.")
        with t3:
            if ss.pasted:
                a, b = st.columns([2, 1])
                a.image(ss.pasted, caption="Screenshot attached", width=200)
                ask_shot = b.button("➤ Ask about it", type="primary")
                if b.button("✕ Remove"):
                    ss.pasted = None
                    ss.paste_n += 1
                    st.rerun()
            else:
                st.caption("Error on screen? Copy a screenshot (Win + Shift + S), click 📋 Paste screenshot, "
                           "then ask. Or attach an image with ➕ in the question box.")
        if voice is not None:
            try:
                text = llm.transcribe(voice.getvalue(), voice.type or "audio/wav")
                ask_now(text)
                st.rerun()
            except llm.AIError as e:
                st.warning(f"Could not read the voice note: {e}")

    with side:
        mine = kb.history(region, ss.user, 5)
        body = "".join(
            f"<div style='margin-bottom:10px'><div style='font-size:.9rem'>{ui.esc(r['question'][:70])}</div>"
            f"{ui.result_badge(r.get('result') or ('answered' if r['status'] in ('answered','resolved') else 'not_found'))}"
            f" <span class='om-meta'>{ui.esc(r['asked_at'][5:])}</span></div>" for r in mine) \
            or "<span class='om-meta'>Your questions will appear here.</span>"
        ui.card("Recent Questions", body)
        notes = kb.announcements(region)
        icons = {"Alert": "🔴", "Maintenance": "🛠️", "New SOP": "🟢", "Info": "🔵"}
        body = "".join(f"<div style='margin-bottom:8px'>{icons.get(a['level'], '🔵')} <b>{ui.esc(a['title'])}</b>"
                       f"<div class='om-meta'>{ui.esc(a['body'][:120])}</div></div>" for a in notes[:5]) \
            or "<span class='om-meta'>No updates right now.</span>"
        ui.card("Important Updates", body)

    prompt = st.chat_input("Type your question here… (English, Hindi, Kannada, Telugu in English letters)",
                           accept_file=True, file_type=["png", "jpg", "jpeg"])
    if prompt or (ss.pasted and ask_shot):
        text = (prompt.text if prompt else "") or ""
        image = ss.pasted
        if prompt and prompt.files:
            image = prompt.files[0].getvalue()
        if text.strip() or image:
            ask_now(text, image)
            st.rerun()


# ---------------------------------------------------------------------------
# PAGE: My Questions
# ---------------------------------------------------------------------------
def page_my_questions():
    st.header("My Questions")
    rows = kb.history(region, ss.user, 100)
    if not rows:
        st.info("You haven't asked anything in this region yet.")
    for r in rows:
        result = r.get("result") or ("answered" if r["status"] in ("answered", "resolved") else "not_found")
        label = {"answered": "✅", "not_found": "⏳", "conflict": "⚠️"}.get(result, "")
        with st.expander(f"{label} {r['asked_at']} · {r['question']}"):
            st.markdown(ui.result_badge(result), unsafe_allow_html=True)
            st.markdown(r["answer"] or "")
            if r["status"] == "resolved":
                st.success("The process team has added an answer - ask again to see it.")


# ---------------------------------------------------------------------------
# PAGE: Knowledge Library / Quick Guides / Announcements
# ---------------------------------------------------------------------------
def doc_list(docs, key):
    for d in docs:
        with st.container(border=True):
            a, b, c = st.columns([5, 2, 2])
            a.markdown(f"**{d['title']}**  \n{d['doc_type']} · {d['filename']}"
                       + (f" · v{d['version']}" if d["version"] else ""))
            b.markdown(ui.region_pill(d["region"]) + f"<br><span class='om-meta'>{d['uploaded_at']}</span>",
                       unsafe_allow_html=True)
            c.download_button("⬇ Download", kb.read_file(d), file_name=d["filename"], key=f"{key}{d['id']}")
            with c.popover("👁 View"):
                st.text(kb.document_text(d["id"], 3000))


def page_library():
    st.header("Knowledge Library")
    docs = kb.list_documents(region, status="Active")
    c1, c2 = st.columns([1, 2])
    t = c1.selectbox("Type", ["All"] + config.DOC_TYPES)
    f = c2.text_input("Search by title")
    docs = [d for d in docs if (t == "All" or d["doc_type"] == t) and (not f or f.lower() in d["title"].lower())]
    if not docs:
        st.info("No documents match.")
    doc_list(docs, "lib")


def page_quick_guides():
    st.header("Quick Guides")
    st.caption("Short how-to guides. Admins upload them with Document type = Quick Guide.")
    docs = [d for d in kb.list_documents(region, status="Active") if d["doc_type"] == "Quick Guide"]
    if not docs:
        st.info("No quick guides yet for this region.")
    for d in docs:
        with st.expander(f"⚡ {d['title']}"):
            st.text(kb.document_text(d["id"], 4000))
            st.download_button("⬇ Download", kb.read_file(d), file_name=d["filename"], key=f"qg{d['id']}")


def page_announcements():
    st.header("Announcements")
    if ss.is_admin:
        admin_pages.announcements_admin(ss.user)
    items = kb.announcements(region)
    if not items:
        st.info("No announcements right now.")
    for a in items:
        with st.container(border=True):
            st.markdown(f"**{a['title']}** · {a['level']} · {a['region']}  \n{a['body']}")
            st.caption(f"{a['author']} · {a['created_at']}")
            if ss.is_admin and st.button("Hide", key=f"hide{a['id']}"):
                kb.set_announcement(a["id"], False)
                st.rerun()


# ---------------------------------------------------------------------------
# ROUTER
# ---------------------------------------------------------------------------
name = page
if name == "💬 Ask OpsMate":
    page_ask()
elif name == "🕘 My Questions":
    page_my_questions()
elif name == "📚 Knowledge Library":
    page_library()
elif name == "⚡ Quick Guides":
    page_quick_guides()
elif name == "📢 Announcements":
    page_announcements()
elif ss.is_admin:
    admin_pages.route(name, region, ss.user)
