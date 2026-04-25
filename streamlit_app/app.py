"""
LegalSaathi – Streamlit Web App (Phase 1)
Run with:  streamlit run streamlit_app/app.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import uuid
from datetime import datetime, timezone

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="LegalSaathi",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Lazy service imports (so app loads even without all deps installed) ────────
def _load_services():
    try:
        from backend.services import ai_service, citation_service, ocr_service, storage_service
        from backend.services.auth_service import register_and_send_otp, verify_otp_and_login, get_user_by_mobile
        from backend.models.schemas import Language, DocumentType, CreateDocumentRequest
        return True
    except Exception as e:
        st.error(f"Service load error: {e}")
        return False


# ── Session State Helpers ─────────────────────────────────────────────────────
def _init_state():
    defaults = {
        "logged_in": False,
        "user": None,
        "token": None,
        "language": "en",
        "mode": "simple",
        "page": "home",
        "doc_result": None,
        "scan_result": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


_init_state()

# ── Styles ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; }
    .stButton>button { border-radius: 8px; font-weight: 500; }
    .risk-high  { color: #c0392b; font-weight: bold; }
    .risk-med   { color: #e67e22; font-weight: bold; }
    .risk-low   { color: #27ae60; font-weight: bold; }
    .badge { display:inline-block; padding:2px 10px; border-radius:12px;
             font-size:0.75rem; font-weight:600; }
    .badge-high { background:#fde8e8; color:#c0392b; }
    .badge-med  { background:#fef3e2; color:#e67e22; }
    .badge-low  { background:#e8f8f0; color:#27ae60; }
</style>
""", unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://via.placeholder.com/200x60?text=⚖️+LegalSaathi", use_column_width=True)
    st.markdown("---")

    if st.session_state.logged_in:
        user = st.session_state.user
        st.success(f"👤 {user['name']}")
        st.caption(f"📱 {user['mobile']}")

        lang_map = {"en": "English", "hi": "हिंदी (Hindi)"}
        selected_lang = st.selectbox(
            "Language / भाषा",
            list(lang_map.keys()),
            format_func=lambda x: lang_map[x],
            index=list(lang_map.keys()).index(st.session_state.language),
        )
        st.session_state.language = selected_lang

        mode = st.radio("Mode", ["simple", "advanced"], index=0 if st.session_state.mode == "simple" else 1)
        st.session_state.mode = mode

        st.markdown("---")
        nav = st.radio(
            "Navigate",
            ["🏠 Home", "📝 Create Document", "📤 Scan Document", "📋 My Documents", "❓ Q&A"],
        )
        st.session_state.page = nav

        st.markdown("---")
        if st.button("🚪 Logout"):
            for k in ["logged_in", "user", "token", "doc_result", "scan_result"]:
                st.session_state[k] = None if k != "logged_in" else False
            st.rerun()
    else:
        st.info("Please login to access LegalSaathi")
        st.session_state.page = "login"


# ═════════════════════════════════════════════════════════════════════════════
# Pages
# ═════════════════════════════════════════════════════════════════════════════

# ── LOGIN / REGISTER ──────────────────────────────────────────────────────────
def page_login():
    st.title("⚖️ LegalSaathi")
    st.markdown("### AI-Powered Legal Assistant for Every Indian")
    st.markdown("---")

    tab1, tab2 = st.tabs(["Login / OTP", "New Registration"])

    with tab2:
        st.subheader("Register")
        name = st.text_input("Full Name")
        mobile = st.text_input("Mobile Number (10 digits)", max_chars=10)
        lang = st.selectbox("Preferred Language", ["en", "hi"],
                            format_func=lambda x: "English" if x == "en" else "हिंदी")
        mode = st.radio("Interface Mode", ["simple", "advanced"],
                        captions=["Large buttons, voice-friendly", "Advanced filters & search"])
        email = st.text_input("Email (optional)")

        if st.button("📲 Send OTP", type="primary"):
            if not name or len(mobile) != 10 or not mobile.isdigit():
                st.error("Please enter a valid name and 10-digit mobile number.")
            else:
                try:
                    from backend.services.auth_service import register_and_send_otp
                    from backend.models.schemas import UserRegister, Language, InterfaceMode
                    data = UserRegister(
                        mobile=mobile, name=name,
                        language=Language(lang),
                        mode=InterfaceMode(mode),
                        email=email or None,
                    )
                    result = register_and_send_otp(data)
                    st.success(f"OTP sent! (Dev mode OTP: **{result.get('dev_otp')}**)")
                    st.session_state["reg_mobile"] = mobile
                except Exception as e:
                    st.error(f"Error: {e}")

    with tab1:
        st.subheader("Verify OTP")
        login_mobile = st.text_input("Mobile Number", key="login_mobile", max_chars=10)
        otp = st.text_input("OTP (6 digits)", max_chars=6, key="otp_input")

        if st.button("✅ Verify & Login", type="primary"):
            try:
                from backend.services.auth_service import verify_otp_and_login
                result = verify_otp_and_login(login_mobile, otp)
                if result:
                    st.session_state.logged_in = True
                    st.session_state.user = {
                        "id": result.user.id,
                        "name": result.user.name,
                        "mobile": result.user.mobile,
                        "language": result.user.language.value,
                        "mode": result.user.mode.value,
                    }
                    st.session_state.token = result.access_token
                    st.session_state.language = result.user.language.value
                    st.session_state.mode = result.user.mode.value
                    st.session_state.page = "🏠 Home"
                    st.rerun()
                else:
                    st.error("Invalid OTP. Please try again.")
            except Exception as e:
                st.error(f"Login error: {e}")

    st.markdown("---")
    st.caption("🔒 Guest mode: Use the Scan tab without logging in (no save).")


# ── HOME ──────────────────────────────────────────────────────────────────────
def page_home():
    user = st.session_state.user
    st.title(f"Namaste, {user['name']}! 🙏")
    st.markdown("What would you like to do today?")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("📝\n\nCreate Document", use_container_width=True, type="primary"):
            st.session_state.page = "📝 Create Document"; st.rerun()
    with col2:
        if st.button("📤\n\nScan Document", use_container_width=True):
            st.session_state.page = "📤 Scan Document"; st.rerun()
    with col3:
        if st.button("📋\n\nMy Documents", use_container_width=True):
            st.session_state.page = "📋 My Documents"; st.rerun()
    with col4:
        if st.button("❓\n\nAsk a Question", use_container_width=True):
            st.session_state.page = "❓ Q&A"; st.rerun()

    st.markdown("---")
    st.markdown("#### Phase 1 – Supported Document Types")
    c1, c2, c3 = st.columns(3)
    with c1: st.info("📄 Rental Agreement\n\nकिराया समझौता")
    with c2: st.info("📜 Affidavit\n\nशपथ पत्र")
    with c3: st.info("🖊️ Will\n\nवसीयत")


# ── CREATE DOCUMENT ───────────────────────────────────────────────────────────
def page_create_document():
    st.title("📝 Create a Legal Document")

    doc_type = st.selectbox(
        "Select Document Type",
        ["rental_agreement", "affidavit", "will"],
        format_func=lambda x: {
            "rental_agreement": "Rental Agreement / किराया समझौता",
            "affidavit": "Affidavit / शपथ पत्र",
            "will": "Will / वसीयत",
        }[x],
    )

    lang = st.selectbox("Output Language", ["en", "hi"],
                        format_func=lambda x: "English" if x == "en" else "हिंदी")

    st.markdown("---")
    data = {}

    if doc_type == "rental_agreement":
        st.subheader("🏠 Rental Agreement Details")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Landlord (Party A)**")
            data["party_a"] = {
                "name": st.text_input("Landlord Name"),
                "address": st.text_area("Landlord Address", height=80),
                "contact": st.text_input("Landlord Contact"),
            }
        with c2:
            st.markdown("**Tenant (Party B)**")
            data["party_b"] = {
                "name": st.text_input("Tenant Name"),
                "address": st.text_area("Tenant Address", height=80),
                "contact": st.text_input("Tenant Contact"),
            }

        data["property_address"] = st.text_area("Property Address", height=80)
        c1, c2, c3 = st.columns(3)
        data["monthly_rent"] = c1.number_input("Monthly Rent (₹)", min_value=0.0, step=500.0)
        data["security_deposit"] = c2.number_input("Security Deposit (₹)", min_value=0.0, step=1000.0)
        data["duration_months"] = c3.number_input("Duration (months)", min_value=1, step=1, value=11)
        data["start_date"] = st.date_input("Start Date").isoformat()

    elif doc_type == "affidavit":
        st.subheader("📜 Affidavit Details")
        data["deponent"] = {
            "name": st.text_input("Deponent Name"),
            "address": st.text_area("Deponent Address", height=80),
        }
        data["subject"] = st.text_input("Subject of Affidavit")
        statements_raw = st.text_area("Statements (one per line)", height=120)
        data["statements"] = [s.strip() for s in statements_raw.splitlines() if s.strip()]
        data["place"] = st.text_input("Place")
        data["date"] = st.date_input("Date").isoformat()

    elif doc_type == "will":
        st.subheader("🖊️ Will Details")
        data["testator"] = {
            "name": st.text_input("Testator (Will Maker) Name"),
            "address": st.text_area("Testator Address", height=80),
        }
        data["assets"] = [a.strip() for a in st.text_area("Assets (one per line)", height=100).splitlines() if a.strip()]
        data["special_instructions"] = st.text_area("Special Instructions (optional)", height=80)

    st.markdown("---")
    if st.button("🤖 Generate Document", type="primary"):
        if not _validate_data(doc_type, data):
            st.error("Please fill in all required fields.")
            return

        with st.spinner("AI is drafting your document… This may take 30–60 seconds."):
            try:
                from backend.services import ai_service, citation_service
                from backend.models.schemas import Language, DocumentType
                import uuid
                from datetime import datetime, timezone

                lang_enum = Language(lang)
                doc_type_enum = DocumentType(doc_type)

                draft = ai_service.draft_document(doc_type_enum, data, lang_enum)
                raw_cites = citation_service.extract_citations_from_text(draft)
                cite_results = citation_service.verify_all_citations(raw_cites)
                verified_texts = [r.citation_text for r in cite_results if r.is_verified]
                if verified_texts:
                    draft = ai_service.draft_document(doc_type_enum, data, lang_enum, verified_texts)

                risks = ai_service.detect_risks(draft)
                overall = ai_service.overall_risk(risks)
                summary = ai_service.summarize_document(draft, Language.EN)
                summary_hi = ai_service.translate_text(summary, lang_enum) if lang_enum != Language.EN else None

                from backend.models.schemas import DocumentResult, RiskLevel
                result = DocumentResult(
                    document_id=str(uuid.uuid4()),
                    document_type=doc_type_enum,
                    content=draft,
                    summary=summary,
                    summary_translated=summary_hi,
                    citations=cite_results,
                    risk_clauses=risks,
                    overall_risk=overall,
                    created_at=datetime.now(timezone.utc),
                    language=lang_enum,
                )

                from backend.services import storage_service
                storage_service.save_created_document(result, st.session_state.user["mobile"])
                st.session_state.doc_result = result
                st.success("✅ Document generated successfully!")
            except Exception as e:
                st.error(f"Generation failed: {e}")

    if st.session_state.doc_result:
        _render_document_result(st.session_state.doc_result)


# ── SCAN DOCUMENT ─────────────────────────────────────────────────────────────
def page_scan_document():
    st.title("📤 Scan a Document")
    st.markdown("Upload a legal document to get a plain-language summary, risk analysis, and citation check.")

    uploaded = st.file_uploader("Upload PDF, DOCX, JPG, or PNG", type=["pdf", "docx", "jpg", "jpeg", "png"])
    lang = st.selectbox("Output Language", ["en", "hi"],
                        format_func=lambda x: "English" if x == "en" else "हिंदी")

    if uploaded and st.button("🔍 Analyse Document", type="primary"):
        with st.spinner("Reading and analysing document…"):
            try:
                from backend.services import ai_service, citation_service, ocr_service, storage_service
                from backend.models.schemas import Language, ScanDocumentResult
                import uuid
                from datetime import datetime, timezone

                file_bytes = uploaded.read()
                lang_enum = Language(lang)

                text, detected = ocr_service.extract_text_from_file(file_bytes, uploaded.name)
                if len(text) < 30:
                    st.error("Could not extract enough text from this file.")
                    return

                summary = ai_service.summarize_document(text, Language.EN)
                summary_hi = ai_service.translate_text(summary, lang_enum) if lang_enum != Language.EN else None
                raw_cites = citation_service.extract_citations_from_text(text)
                cite_results = citation_service.verify_all_citations(raw_cites)
                risks = ai_service.detect_risks(text)
                overall = ai_service.overall_risk(risks)

                result = ScanDocumentResult(
                    document_id=str(uuid.uuid4()),
                    extracted_text=text,
                    detected_language=detected,
                    summary=summary,
                    summary_translated=summary_hi,
                    citations=cite_results,
                    risk_clauses=risks,
                    overall_risk=overall,
                    scanned_at=datetime.now(timezone.utc),
                )
                storage_service.save_scanned_document(result, st.session_state.user["mobile"])
                st.session_state.scan_result = result
            except Exception as e:
                st.error(f"Scan failed: {e}")

    if st.session_state.scan_result:
        r = st.session_state.scan_result
        st.markdown("---")
        st.markdown(f"**Detected Language:** `{r.detected_language}`")
        _render_summary(r.summary, r.summary_translated)
        _render_risk_section(r.risk_clauses, r.overall_risk)
        _render_citations(r.citations)

        with st.expander("📄 Extracted Text"):
            st.text_area("", r.extracted_text, height=300)


# ── Q&A ───────────────────────────────────────────────────────────────────────
def page_qa():
    st.title("❓ Ask About Your Document")

    from backend.services.storage_service import _user_doc_index, _created_docs, _scanned_docs

    mobile = st.session_state.user["mobile"]
    doc_ids = _user_doc_index.get(mobile, [])
    if not doc_ids:
        st.info("No documents found. Create or scan a document first.")
        return

    doc_labels = {}
    for did in doc_ids:
        if did in _created_docs:
            doc = _created_docs[did]
            doc_labels[did] = f"📝 {doc.document_type.value.replace('_', ' ').title()} ({did[:8]}…)"
        elif did in _scanned_docs:
            doc_labels[did] = f"📤 Scanned Document ({did[:8]}…)"

    selected_id = st.selectbox("Select Document", list(doc_labels.keys()),
                               format_func=lambda x: doc_labels.get(x, x))

    question = st.text_input("Your Question", placeholder="What happens if I miss a payment?")
    lang = st.selectbox("Answer Language", ["en", "hi"],
                        format_func=lambda x: "English" if x == "en" else "हिंदी")

    if st.button("🤖 Get Answer", type="primary") and question:
        with st.spinner("Finding answer…"):
            try:
                from backend.services import ai_service, storage_service
                from backend.models.schemas import Language
                doc_text = storage_service.get_document_text(selected_id)
                lang_enum = Language(lang)
                result = ai_service.answer_question(doc_text, question, lang_enum)
                translated = None
                if lang_enum.value != "en":
                    translated = ai_service.translate_text(result["answer"], lang_enum)

                st.markdown("### Answer")
                st.success(result["answer"])
                if translated:
                    st.info(f"**Hindi / हिंदी:** {translated}")
                if result["relevant_clauses"]:
                    st.markdown("**Relevant clauses:**")
                    for c in result["relevant_clauses"]:
                        st.caption(f"• {c}")
            except Exception as e:
                st.error(f"Q&A failed: {e}")


# ── HISTORY ───────────────────────────────────────────────────────────────────
def page_history():
    st.title("📋 My Documents")
    from backend.services import storage_service
    docs = storage_service.list_user_documents(st.session_state.user["mobile"])

    if not docs:
        st.info("No documents yet. Create or scan your first document!")
        return

    for doc in docs:
        badge = {"Low": "🟢 Low", "Medium": "🟡 Medium", "High": "🔴 High"}.get(doc.get("overall_risk", {}).get("value", "–"), "–")
        with st.expander(f"{doc.get('title', 'Document')} — {badge} risk | {doc.get('created_at', doc.get('scanned_at', 'Unknown')).split('T')[0]}"):
            st.caption(f"Document ID: `{doc['document_id']}`")
            col1, col2 = st.columns(2)
            col1.metric("Risk Level", doc.get("overall_risk", {}).get("value", "Unknown"))
            col2.metric("Created", doc.get('created_at', doc.get('scanned_at', 'Unknown')).split('T')[0])


# ── Render Helpers ────────────────────────────────────────────────────────────
def _render_document_result(result):
    st.markdown("---")
    tabs = st.tabs(["📄 Document", "📝 Summary", "⚠️ Risk Analysis", "📚 Citations"])

    with tabs[0]:
        st.text_area("Generated Document", result.content, height=500)
        st.download_button("⬇️ Download as TXT", result.content,
                           file_name=f"{result.document_type.value}.txt")

    with tabs[1]:
        _render_summary(result.summary, result.summary_translated)

    with tabs[2]:
        _render_risk_section(result.risk_clauses, result.overall_risk)

    with tabs[3]:
        _render_citations(result.citations)


def _render_summary(summary: str, translated=None):
    st.markdown("#### Plain-Language Summary")
    st.info(summary)
    if translated:
        st.markdown("#### हिंदी में सारांश")
        st.info(translated)


def _render_risk_section(risk_clauses, overall_risk):
    colours = {"Low": "🟢", "Medium": "🟡", "High": "🔴"}
    st.markdown(f"#### Overall Risk: {colours.get(overall_risk.value, '')} **{overall_risk.value}**")
    if not risk_clauses:
        st.success("No significant risks detected.")
        return
    for clause in risk_clauses:
        icon = colours.get(clause.risk_level.value, "")
        with st.expander(f"{icon} {clause.clause_text[:80]}…"):
            st.markdown(f"**Risk:** {clause.risk_reason}")
            st.markdown(f"**Level:** {clause.risk_level.value}")
            if clause.suggestion:
                st.markdown(f"**Suggestion:** {clause.suggestion}")


def _render_citations(citations):
    st.markdown("#### Citation Verification")
    if not citations:
        st.info("No legal citations found in this document.")
        return
    verified = sum(1 for c in citations if c.is_verified)
    st.metric("Verified Citations", f"{verified}/{len(citations)}")
    for c in citations:
        icon = "✅" if c.is_verified else "❌"
        with st.expander(f"{icon} {c.citation_text}"):
            if c.is_verified:
                st.success(f"Verified – {c.case_name or ''}")
                if c.source:
                    st.markdown(f"[View on Indian Kanoon]({c.source})")
            else:
                st.error("Could not verify this citation. It may be inaccurate.")


def _validate_data(doc_type: str, data: dict) -> bool:
    if doc_type == "rental_agreement":
        return bool(
            data.get("party_a", {}).get("name")
            and data.get("party_b", {}).get("name")
            and data.get("property_address")
        )
    if doc_type == "affidavit":
        return bool(data.get("deponent", {}).get("name") and data.get("subject"))
    if doc_type == "will":
        return bool(data.get("testator", {}).get("name"))
    return True


# ═════════════════════════════════════════════════════════════════════════════
# Router
# ═════════════════════════════════════════════════════════════════════════════
if not st.session_state.logged_in:
    page_login()
else:
    page = st.session_state.page
    if page == "🏠 Home":
        page_home()
    elif page == "📝 Create Document":
        page_create_document()
    elif page == "📤 Scan Document":
        page_scan_document()
    elif page == "❓ Q&A":
        page_qa()
    elif page == "📋 My Documents":
        page_history()
    else:
        page_home()

# Footer
st.markdown("---")
st.caption("⚖️ LegalSaathi v1.0 – Phase 1 | "
           "AI-generated documents are for reference only. Consult a qualified lawyer for final decisions.")
