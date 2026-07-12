import os
import json
import time
import textwrap
import io
import requests
import streamlit as st
from datetime import datetime
from dotenv import load_dotenv
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from evaluation.evaluator import SystemEvaluator
from evaluation.dashboard import show_evaluation_dashboard

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

st.set_page_config(
    page_title="Courtroom AI - Legal Simulation",
    page_icon="⚖️",
    layout="wide"
)

# ============================================
# CSS – Baby Blue & Baby Pink Theme
# ============================================
st.markdown("""
<style>
    .stApp {
        background: #F5F9FF !important;
        font-family: 'Inter', 'Segoe UI', Roboto, sans-serif;
    }
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #E8F0FE; }
    ::-webkit-scrollbar-thumb { background: #FFB6C1; border-radius: 8px; }

    /* ---- Header ---- */
    .court-header {
        background: linear-gradient(135deg, #D4E8FF 0%, #FFE0ED 100%);
        padding: 1.8rem 2.5rem;
        border-bottom: 3px solid #FFB6C1;
        margin-bottom: 2rem;
        text-align: center;
        border-radius: 0 0 30px 30px;
        box-shadow: 0 4px 20px rgba(168, 216, 234, 0.15);
    }
    .court-header h1 {
        font-size: 32px;
        font-weight: 700;
        letter-spacing: 2px;
        color: #2A4B7C;
        margin: 0;
    }
    .court-header h1 span {
        color: #B85C7A;
        background: rgba(255, 182, 193, 0.25);
        padding: 0 12px;
        border-radius: 40px;
    }
    .court-header p {
        color: #3A5A8A;
        font-size: 14px;
        letter-spacing: 3px;
        text-transform: uppercase;
        margin: 6px 0 0 0;
        font-weight: 400;
    }

    /* ---- Cards / Containers ---- */
    .top-card {
        background: white;
        border: 1px solid #E6EDFF;
        padding: 1.2rem 1.5rem;
        border-radius: 16px;
        height: 100%;
        border-top: 4px solid #A8D8EA;
        box-shadow: 0 2px 8px rgba(0,0,0,0.02);
        min-height: 140px;
    }
    .top-card h4 {
        color: #2A4B7C;
        font-size: 13px;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin: 0 0 0.8rem 0;
        font-weight: 600;
    }
    .top-card .item {
        color: #1E2937;
        font-size: 14px;
        padding: 4px 0;
        border-bottom: 1px solid #E8F0FE;
    }
    .top-card .item strong {
        color: #2A4B7C;
        font-weight: 600;
        margin-right: 6px;
    }
    .top-card .item .value {
        color: #1E2937;
        white-space: pre-wrap;
        word-wrap: break-word;
        line-height: 1.6;
    }
    .top-card .empty {
        color: #94A3B8;
        font-size: 14px;
        font-style: italic;
    }
    .top-card.consultant-panel {
        background: #F8FAFF;
        border: 1px solid #FFE0ED;
        border-top: 4px solid #FFB6C1;
        box-shadow: 0 2px 8px rgba(255, 182, 193, 0.08);
    }
    .top-card.consultant-panel h4 {
        color: #B85C7A;
    }
    .top-card .sublabel {
        color: #A8D8EA;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin: 0.9rem 0 0.3rem 0;
        font-weight: 600;
    }
    .top-card ul.bullet-list {
        margin: 0;
        padding-left: 1.1rem;
        color: #1E2937;
        font-size: 13.5px;
        line-height: 1.7;
    }
    .top-card ul.bullet-list li { margin-bottom: 2px; }
    .top-card ul.bullet-list.missing li { color: #B85C7A; }

    /* ---- Legal Research Cards ---- */
    .law-card {
        background: #F8FAFF;
        border-left: 4px solid #FFB6C1;
        padding: 0.6rem 0.9rem;
        margin-bottom: 0.6rem;
        font-size: 13.5px;
        color: #1E2937;
        border-radius: 0 8px 8px 0;
    }
    .law-card .title {
        font-weight: 600;
        color: #2A4B7C;
        margin-bottom: 2px;
    }
    .law-card .meta {
        color: #64748B;
        font-size: 11.5px;
        margin-bottom: 4px;
    }
    .law-card .relevance {
        color: #475569;
        line-height: 1.6;
    }

    /* ---- Judge Container ---- */
    .judge-container {
        background: white;
        border: 1px solid #E6EDFF;
        border-left: 6px solid #FFB6C1;
        padding: 1.2rem 2rem;
        margin-bottom: 1.5rem;
        text-align: center;
        border-radius: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.02);
    }
    .judge-container .label {
        color: #64748B;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    .judge-container .verdict-text {
        font-size: 26px;
        font-weight: 700;
        letter-spacing: 1px;
    }
    .judge-container .verdict-green { color: #4ade80; }
    .judge-container .verdict-red { color: #f87171; }
    .judge-container .verdict-amber { color: #fbbf24; }
    .judge-container .confidence {
        background: #F8FAFF;
        padding: 4px 16px;
        border-radius: 30px;
        color: #B85C7A;
        font-size: 13px;
        font-weight: 600;
        border: 1px solid #FFE0ED;
    }

    /* ---- Verdict Fields ---- */
    .verdict-reasoning {
        background: white;
        border: 1px solid #E6EDFF;
        border-left: 4px solid #FFB6C1;
        padding: 1.5rem 2rem;
        margin-bottom: 1.5rem;
        border-radius: 16px;
        text-align: left;
        box-shadow: 0 2px 8px rgba(0,0,0,0.02);
    }
    .verdict-reasoning .label {
        color: #B85C7A;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 0.75rem;
        display: block;
    }
    .verdict-reasoning .content {
        color: #1E2937;
        font-size: 15px;
        line-height: 1.8;
        white-space: pre-wrap;
        word-wrap: break-word;
    }
    .verdict-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1rem;
        margin-bottom: 1.5rem;
    }
    .verdict-field {
        background: white;
        border: 1px solid #E6EDFF;
        border-left: 4px solid #A8D8EA;
        padding: 1rem 1.3rem;
        border-radius: 12px;
    }
    .verdict-field .label {
        color: #2A4B7C;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin-bottom: 0.4rem;
        display: block;
    }
    .verdict-field .content {
        color: #1E2937;
        font-size: 14px;
        line-height: 1.7;
    }
    .sections-pill-row {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
    }
    .sections-pill {
        background: #F8FAFF;
        border: 1px solid #A8D8EA;
        color: #2A4B7C;
        font-size: 12px;
        font-weight: 600;
        padding: 4px 12px;
        border-radius: 30px;
    }

    /* ---- Debate Columns ---- */
    .debate-column {
        background: white;
        border: 1px solid #E6EDFF;
        padding: 1.5rem 1.8rem;
        height: 100%;
        min-height: 250px;
        border-top: 4px solid #FFB6C1;
        overflow-y: auto;
        max-height: 500px;
        border-radius: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.02);
    }
    .debate-column .col-header {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        border-bottom: 1px solid #E8F0FE;
        padding-bottom: 0.75rem;
        margin-bottom: 1rem;
        position: sticky;
        top: 0;
        background: white;
        z-index: 2;
    }
    .debate-column .col-header .icon { font-size: 22px; }
    .debate-column .col-header h3 {
        margin: 0;
        color: #2A4B7C;
        font-size: 18px;
        font-weight: 600;
        letter-spacing: 0.5px;
    }
    .debate-column .col-header .sub {
        color: #94A3B8;
        font-size: 12px;
        font-weight: 300;
        margin-left: auto;
    }
    .debate-column .empty-state {
        color: #94A3B8;
        font-size: 14px;
        font-style: italic;
        padding: 1.2rem 0;
        text-align: center;
    }
    .argument-block {
        background: #F8FAFF;
        border-left: 4px solid #A8D8EA;
        padding: 1rem 1.2rem;
        margin-bottom: 1rem;
        border-radius: 0 8px 8px 0;
        color: #1E2937;
        font-size: 14px;
        line-height: 1.8;
        white-space: pre-wrap;
        word-wrap: break-word;
    }
    .argument-block .round-tag {
        font-size: 11px;
        text-transform: uppercase;
        color: #2A4B7C;
        font-weight: 600;
        letter-spacing: 1px;
        margin-bottom: 4px;
        display: block;
    }
    .argument-block.prosecution { border-left-color: #A8D8EA; }
    .argument-block.defense { border-left-color: #FFB6C1; }

    /* ---- Reporter Card ---- */
    .reporter-card {
        background: white;
        border: 1px solid #E6EDFF;
        padding: 1.2rem 2rem;
        border-radius: 16px;
        border-top: 4px solid #A8D8EA;
        margin-top: 1.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.02);
    }
    .reporter-card h4 {
        color: #2A4B7C;
        font-size: 13px;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin: 0 0 0.8rem 0;
        font-weight: 600;
    }
    .reporter-card .headline {
        color: #2A4B7C;
        font-size: 18px;
        font-weight: 600;
        margin-bottom: 0.75rem;
        border-left: 4px solid #FFB6C1;
        padding-left: 1rem;
    }
    .reporter-card .report {
        color: #1E2937;
        font-size: 15px;
        line-height: 1.8;
        white-space: pre-wrap;
        word-wrap: break-word;
    }
    .reporter-card .empty {
        color: #94A3B8;
        font-size: 14px;
        font-style: italic;
    }

    /* ---- Text Input & Buttons ---- */
    .stTextArea textarea {
        background: white !important;
        color: #1E2937 !important;
        border: 1px solid #D4E8FF !important;
        border-radius: 12px !important;
        font-size: 14px !important;
        line-height: 1.6 !important;
        font-family: 'Inter', sans-serif !important;
    }
    .stTextArea textarea:focus {
        border-color: #FFB6C1 !important;
        box-shadow: 0 0 0 3px rgba(255, 182, 193, 0.15) !important;
    }
    .stButton button {
        background: #FFB6C1 !important;
        color: white !important;
        font-weight: 700 !important;
        border: none !important;
        border-radius: 30px !important;
        padding: 0.6rem 2.5rem !important;
        letter-spacing: 1px;
        text-transform: uppercase;
        font-size: 14px !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 4px 14px rgba(255, 182, 193, 0.3);
        width: 100%;
    }
    .stButton button:hover {
        background: #FF9EAB !important;
        box-shadow: 0 6px 20px rgba(255, 182, 193, 0.4) !important;
        transform: translateY(-2px);
    }
    .stButton button:disabled {
        opacity: 0.4;
        pointer-events: none;
    }

    /* ---- Dividers & Status ---- */
    .gold-divider {
        height: 2px;
        background: linear-gradient(90deg, transparent, #FFB6C1, transparent);
        margin: 1rem 0 1.5rem 0;
        opacity: 0.6;
    }
    .status-text {
        color: #94A3B8;
        font-size: 13px;
        text-align: center;
        padding: 0.5rem 0;
        letter-spacing: 1px;
    }
    .status-text .gold {
        color: #FFB6C1;
    }
    .idle-state {
        text-align: center;
        padding: 4rem 1rem;
        color: #94A3B8;
    }
    .idle-state .icon {
        font-size: 64px;
        margin-bottom: 1rem;
        opacity: 0.6;
    }
    .idle-state h2 {
        color: #2A4B7C;
        font-weight: 400;
        letter-spacing: 2px;
        font-size: 26px;
    }
    .idle-state p {
        color: #94A3B8;
        font-size: 15px;
    }

    /* ---- Complaint Box ---- */
    .complaint-box {
        background: #F8FAFF;
        border-left: 4px solid #FFB6C1;
        padding: 1rem 1.5rem;
        margin-bottom: 1rem;
        border-radius: 0 12px 12px 0;
    }
    .complaint-box .label {
        color: #2A4B7C;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin: 0 0 0.3rem 0;
    }
    .complaint-box .text {
        color: #1E2937;
        font-size: 15px;
        line-height: 1.6;
        margin: 0;
        white-space: pre-wrap;
    }

    /* ---- Responsive ---- */
    @media (max-width: 768px) {
        .judge-container {
            flex-direction: column;
            gap: 0.5rem;
            text-align: center;
        }
        .debate-column {
            min-height: auto;
            max-height: none;
        }
        .top-card {
            min-height: auto;
        }
        .verdict-grid {
            grid-template-columns: 1fr;
        }
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# HELPERS
# ============================================
import html as _html_module

def esc(text) -> str:
    if text is None:
        return ""
    return _html_module.escape(str(text))

# ============================================
# SSE PARSER
# ============================================
def _parse_sse_stream(response):
    """Minimal SSE parser for the backend's text/event-stream response."""
    event, data = None, None
    for raw_line in response.iter_lines(decode_unicode=True):
        if raw_line is None:
            continue
        line = raw_line.strip()
        if line == "":
            if event and data is not None:
                yield event, data
            event, data = None, None
            continue
        if line.startswith("event:"):
            event = line[len("event:"):].strip()
        elif line.startswith("data:"):
            data = line[len("data:"):].strip()
    if event and data is not None:
        yield event, data

# ============================================
# REPORT GENERATION
# ============================================
def _build_report_content(state: dict) -> str:
    report_lines = []
    report_lines.append("# ⚖️ Courtroom AI Simulation Report")
    report_lines.append(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")
    report_lines.append("## 🏛️ Top Consultant")
    report_lines.append(state.get('top_consultant', 'Not available.') or 'Not available.')
    report_lines.append("")
    report_lines.append("## ⚔️ Prosecution Round 1")
    report_lines.append(state.get('pros_r1', 'Not available.') or 'Not available.')
    report_lines.append("")
    report_lines.append("## 🛡️ Defense Round 1")
    report_lines.append(state.get('def_r1', 'Not available.') or 'Not available.')
    report_lines.append("")
    report_lines.append("## ⚔️ Prosecution Round 2")
    report_lines.append(state.get('pros_r2', 'Not available.') or 'Not available.')
    report_lines.append("")
    report_lines.append("## 🛡️ Defense Round 2")
    report_lines.append(state.get('def_r2', 'Not available.') or 'Not available.')
    report_lines.append("")
    report_lines.append("## 👨‍⚖️ Judge")
    jv = state.get("judge_verdict")
    if jv:
        report_lines.append(f"- **Verdict:** {jv.get('verdict', 'Unknown')}")
        report_lines.append(f"- **Confidence:** {jv.get('confidence', 'N/A')}%")
        report_lines.append(f"- **Findings:** {jv.get('findings', '')}")
        report_lines.append(f"- **Prosecution Assessment:** {jv.get('prosecution_assessment', '')}")
        report_lines.append(f"- **Defense Assessment:** {jv.get('defense_assessment', '')}")
        report_lines.append(f"- **Reasoning:** {jv.get('reasoning', '')}")
        sections_applied_list = jv.get("sections_applied") or []
        report_lines.append(f"- **Sections Applied:** {', '.join(sections_applied_list)}")
        report_lines.append(f"- **Probable Punishment:** {jv.get('probable_punishment', '')}")
    else:
        report_lines.append(f"- **Verdict Short:** {state.get('verdict_short', 'Unknown')}")
        report_lines.append(f"- **Confidence:** {state.get('confidence', 'N/A')}%")
        report_lines.append(f"- **Full Verdict:**\n{state.get('verdict', 'Not available.')}")
    report_lines.append("")
    report_lines.append("## 📰 Reporter")
    report_lines.append(f"- **Headline:** {state.get('headline', 'No headline.')}")
    report_lines.append(f"- **Report:**\n{state.get('report', 'Not available.')}")
    report_lines.append("")
    report_lines.append("## 📂 Case Manager")
    ci = state.get("case_intake")
    if ci:
        report_lines.append(f"- **Accused:** {ci.get('accused', 'Unknown')}")
        report_lines.append(f"- **Victim:** {ci.get('victim', 'Unknown')}")
        report_lines.append(f"- **Offences:** {ci.get('offences', 'Unknown')}")
        report_lines.append(f"- **Allegation:** {ci.get('allegation', 'Unknown')}")
        report_lines.append(f"- **Jurisdiction:** {ci.get('jurisdiction', 'Unknown')}")
        facts_list = ci.get("facts") or []
        if facts_list:
            report_lines.append("- **Facts:**")
            for f in facts_list:
                report_lines.append(f"  - {f}")
        missing_list = ci.get("missing_information") or []
        if missing_list:
            report_lines.append("- **Missing Information:**")
            for m in missing_list:
                report_lines.append(f"  - {m}")
    else:
        report_lines.append(f"- **Accused:** {state.get('accused', 'Unknown')}")
        report_lines.append(f"- **Victim:** {state.get('victim', 'Unknown')}")
        report_lines.append(f"- **Offence:** {state.get('offence', 'Unknown')}")
        report_lines.append(f"- **Facts:** {state.get('facts', 'Unknown')}")
    report_lines.append("")
    report_lines.append("## 📚 Legal Research")
    lr = state.get("legal_research")
    if lr:
        sections = lr.get("applicable_sections") or []
        for sec in sections:
            report_lines.append(f"- **{sec.get('section')} | {sec.get('act')}** — {sec.get('relevance')}")
        precedents = lr.get("precedents") or []
        if precedents:
            report_lines.append("- **Precedents:**")
            for p in precedents:
                report_lines.append(f"  - {p.get('case_name')} ({p.get('court')}, {p.get('year')}) — {p.get('relevance')}")
        evidentiary_notes = lr.get("evidentiary_notes") or []
        if evidentiary_notes:
            report_lines.append("- **Evidentiary Notes:**")
            for n in evidentiary_notes:
                report_lines.append(f"  - {n}")
    else:
        report_lines.append(f"- **Laws:** {state.get('laws', 'Not specified')}")
        report_lines.append(f"- **Sections Applied:** {state.get('sections_applied', 'Not specified')}")
        report_lines.append(f"- **Precedents:** {state.get('precedents', 'Not specified')}")
    report_lines.append("")
    report_lines.append("## 🧭 Internal Consultant")
    report_lines.append(state.get('consultant', 'Not available.') or 'Not available.')
    report_lines.append("")
    return "\n".join(report_lines)

def _build_pdf_bytes(report_text: str) -> bytes:
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    left = 50
    top = height - 50
    line_height = 12

    def draw_wrapped(text: str, x: int, y: int, font_name: str = "Helvetica", font_size: int = 10):
        nonlocal top
        c.setFont(font_name, font_size)
        text = text.replace("**", "")
        for raw_line in text.split("\n"):
            if y < 50:
                c.showPage()
                c.setFont(font_name, font_size)
                y = height - 50
            if not raw_line.strip():
                y -= line_height
                continue
            wrapped = textwrap.wrap(raw_line, width=110)
            for chunk in wrapped:
                if y < 50:
                    c.showPage()
                    c.setFont(font_name, font_size)
                    y = height - 50
                c.drawString(x, y, chunk)
                y -= line_height
        return y

    y = top
    for line in report_text.splitlines():
        if y < 50:
            c.showPage()
            y = height - 50
        if line.startswith("# "):
            y = draw_wrapped(line[2:], left, y, font_name="Helvetica-Bold", font_size=16)
            y -= 6
        elif line.startswith("## "):
            y = draw_wrapped(line[3:], left, y, font_name="Helvetica-Bold", font_size=12)
            y -= 4
        elif line.startswith("- **"):
            y = draw_wrapped(line[2:].replace("- **", "").replace("**", ""), left + 6, y)
        elif line.startswith("  - "):
            y = draw_wrapped(line[4:], left + 18, y)
        elif line.startswith("- "):
            y = draw_wrapped(line[2:], left + 6, y)
        else:
            y = draw_wrapped(line, left, y)
    c.save()
    return buffer.getvalue()

# ============================================
# SESSION STATE INIT
# ============================================
EMPTY_CASE_STATE = {
    "complaint": "",
    "entities": None, "accused": None, "victim": None,
    "offence": None, "facts": None, "case_intake": None,
    "laws": None, "sections_applied": None, "precedents": None,
    "legal_research": None,
    "consultant": None,
    "top_consultant": None,
    "pros_r1": None, "def_r1": None,
    "pros_r2": None, "def_r2": None,
    "verdict": None, "verdict_short": None,
    "confidence": None, "reasoning": None, "probable_punishment": None,
    "judge_verdict": None,
    "headline": None, "report": None,
    "is_running": False,
    "execution_times": {},
}

if "case_state" not in st.session_state:
    st.session_state.case_state = dict(EMPTY_CASE_STATE)

if "simulation_complete" not in st.session_state:
    st.session_state.simulation_complete = False

if "stream_event_generator" not in st.session_state:
    st.session_state.stream_event_generator = None

if "node_times" not in st.session_state:
    st.session_state.node_times = {}

if "evaluator" not in st.session_state:
    st.session_state.evaluator = SystemEvaluator()

if "complaint_input" not in st.session_state:
    st.session_state.complaint_input = ""

if "uploaded_complaint" not in st.session_state:
    st.session_state.uploaded_complaint = ""

if "metrics_recorded" not in st.session_state:
    st.session_state.metrics_recorded = False

if "last_metrics" not in st.session_state:
    st.session_state.last_metrics = None

if "simulation_error" not in st.session_state:
    st.session_state.simulation_error = None

# ============================================
# HEADER & HEALTH CHECK
# ============================================
st.markdown("""
<div class="court-header">
    <h1>⚖️ <span>COURTROOM</span> AI</h1>
    <p>Indian Law · Multi-Agent Adversarial Simulation</p>
</div>
""", unsafe_allow_html=True)

try:
    health = requests.get(f"{BACKEND_URL}/health", timeout=5).json()
    if not health.get("ok"):
        st.error(f"Backend not ready: {health.get('message')}")
        st.stop()
except requests.exceptions.RequestException:
    st.error(f"Cannot reach backend at {BACKEND_URL}. Is it running? (`uvicorn main:app --reload`)")
    st.stop()

# ============================================
# TABS
# ============================================
tab_simulation, tab_metrics = st.tabs(["⚖️ Simulation", "📊 Metrics"])

# ============================================
# TAB 1: SIMULATION
# ============================================
with tab_simulation:
    # ----- INPUT SECTION -----
    if not st.session_state.case_state.get("is_running") and not st.session_state.simulation_complete:
        with st.container():
            col_input1, col_input2 = st.columns([3, 1])
            with col_input1:
                uploaded_file = st.file_uploader(
                    "Or upload a complaint file (.txt, .pdf)",
                    type=['txt', 'pdf'],
                    key="complaint_uploader",
                    disabled=False,
                    label_visibility="visible"
                )

                if uploaded_file is not None:
                    try:
                        file_type = uploaded_file.type
                        text = ""
                        if file_type == "text/plain":
                            text = uploaded_file.getvalue().decode("utf-8")
                        elif file_type == "application/pdf":
                            try:
                                from pypdf import PdfReader
                                reader = PdfReader(uploaded_file)
                                for page in reader.pages:
                                    page_text = page.extract_text()
                                    if page_text:
                                        text += page_text + "\n"
                            except ImportError:
                                st.error("The 'pypdf' library is required for PDF uploads. Please install it with: pip install pypdf")
                                text = ""
                        if text:
                            st.session_state.uploaded_complaint = text
                            st.success(f"✅ File uploaded successfully ({len(text)} characters)")
                    except Exception as e:
                        st.error(f"Error reading file: {e}")

                complaint = st.text_area(
                    "Complaint or case brief",
                    height=120,
                    placeholder="Enter the case brief / complaint details here... or upload a file above.",
                    key="complaint_input",
                    disabled=False,
                    label_visibility="visible"
                )

            with col_input2:
                st.write("")
                st.write("")
                if st.button("⚖️ Begin Simulation", type="primary", use_container_width=True):
                    current_complaint = st.session_state.get("uploaded_complaint") or st.session_state.get("complaint_input", "")
                    if not current_complaint.strip():
                        st.warning("Please enter a complaint or upload a file.")
                        st.stop()

                    # Reset state
                    st.session_state.case_state = dict(EMPTY_CASE_STATE)
                    st.session_state.case_state["complaint"] = current_complaint
                    st.session_state.case_state["is_running"] = True
                    st.session_state.simulation_complete = False
                    st.session_state.node_times = {}
                    st.session_state.metrics_recorded = False
                    st.session_state.last_metrics = None
                    st.session_state.simulation_error = None
                    st.session_state.stream_event_generator = None

                    try:
                        response = requests.post(
                            f"{BACKEND_URL}/simulate",
                            json={"complaint": current_complaint},
                            stream=True,
                            timeout=300,
                        )
                        response.raise_for_status()
                        st.session_state.stream_event_generator = _parse_sse_stream(response)
                        st.session_state.sim_start_time = time.time()
                    except Exception as e:
                        st.error(f"Failed to start simulation: {e}")
                        st.session_state.case_state["is_running"] = False
                        st.stop()

                    st.rerun()

    # ----- STATUS & ERROR DISPLAY -----
    if st.session_state.simulation_error:
        st.error(f"❌ {st.session_state.simulation_error}")

    if st.session_state.case_state.get("is_running"):
        st.markdown('<div class="status-text"><span class="gold">⚖️</span> Court is in session... Arguments are being exchanged.</div>', unsafe_allow_html=True)
        with st.expander("🔧 Debug Info"):
            st.write(f"is_running: {st.session_state.case_state.get('is_running')}")
            st.write(f"simulation_complete: {st.session_state.simulation_complete}")
            st.write(f"stream_event_generator exists: {st.session_state.stream_event_generator is not None}")
    elif st.session_state.simulation_complete:
        st.markdown('<div class="status-text"><span class="gold">✅</span> The Hon\'ble Judge has delivered the final verdict.</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-text">🏛️ Enter a case brief and begin the simulation.</div>', unsafe_allow_html=True)

    st.markdown('<div class="gold-divider"></div>', unsafe_allow_html=True)

    # ----- ROW 1: CASE MANAGER | LEGAL RESEARCH | CONSULTANT -----
    col_cm, col_lr, col_cons = st.columns(3, gap="large")

    with col_cm:
        st.markdown('<div class="top-card"><h4>📂 Case Manager</h4>', unsafe_allow_html=True)
        case_intake = st.session_state.case_state.get("case_intake")
        if case_intake:
            accused = case_intake.get("accused")
            victim = case_intake.get("victim")
            offences = case_intake.get("offences")
            allegation = case_intake.get("allegation")
            jurisdiction = case_intake.get("jurisdiction")
            facts_list = case_intake.get("facts") or []
            missing_list = case_intake.get("missing_information") or []
            if accused:
                st.markdown(f'<div class="item"><strong>Accused:</strong> <span class="value">{esc(accused)}</span></div>', unsafe_allow_html=True)
            if victim:
                st.markdown(f'<div class="item"><strong>Victim:</strong> <span class="value">{esc(victim)}</span></div>', unsafe_allow_html=True)
            if offences:
                st.markdown(f'<div class="item"><strong>Offences:</strong> <span class="value">{esc(offences)}</span></div>', unsafe_allow_html=True)
            if allegation:
                st.markdown(f'<div class="item"><strong>Allegation:</strong> <span class="value">{esc(allegation)}</span></div>', unsafe_allow_html=True)
            if jurisdiction:
                st.markdown(f'<div class="item"><strong>Jurisdiction:</strong> <span class="value">{esc(jurisdiction)}</span></div>', unsafe_allow_html=True)
            if facts_list:
                st.markdown('<div class="sublabel">Material Facts</div>', unsafe_allow_html=True)
                items = "".join(f"<li>{esc(f)}</li>" for f in facts_list)
                st.markdown(f'<ul class="bullet-list">{items}</ul>', unsafe_allow_html=True)
            if missing_list:
                st.markdown('<div class="sublabel">Missing Information</div>', unsafe_allow_html=True)
                items = "".join(f"<li>{esc(m)}</li>" for m in missing_list)
                st.markdown(f'<ul class="bullet-list missing">{items}</ul>', unsafe_allow_html=True)
        else:
            accused = st.session_state.case_state.get("accused")
            victim = st.session_state.case_state.get("victim")
            offence = st.session_state.case_state.get("offence")
            facts = st.session_state.case_state.get("facts")
            if accused or victim or offence:
                if accused:
                    st.markdown(f'<div class="item"><strong>Accused:</strong> <span class="value">{esc(accused)}</span></div>', unsafe_allow_html=True)
                if victim:
                    st.markdown(f'<div class="item"><strong>Victim:</strong> <span class="value">{esc(victim)}</span></div>', unsafe_allow_html=True)
                if offence:
                    st.markdown(f'<div class="item"><strong>Offence:</strong> <span class="value">{esc(offence)}</span></div>', unsafe_allow_html=True)
                if facts:
                    st.markdown(f'<div class="item"><strong>Facts:</strong> <span class="value">{esc(facts)}</span></div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="empty">Awaiting case analysis...</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_lr:
        st.markdown('<div class="top-card"><h4>📚 Legal Research</h4>', unsafe_allow_html=True)
        legal_research = st.session_state.case_state.get("legal_research")
        if legal_research:
            sections = legal_research.get("applicable_sections") or []
            precedents = legal_research.get("precedents") or []
            evidentiary_notes = legal_research.get("evidentiary_notes") or []
            unsettled = legal_research.get("unsettled_questions") or []
            if sections:
                st.markdown('<div class="sublabel">Applicable Sections</div>', unsafe_allow_html=True)
                for s in sections:
                    st.markdown(f"""
                    <div class="law-card">
                        <div class="title">{esc(s.get('section'))} — {esc(s.get('act'))}</div>
                        <div class="relevance">{esc(s.get('relevance'))}</div>
                    </div>
                    """, unsafe_allow_html=True)
            if precedents:
                st.markdown('<div class="sublabel">Precedents</div>', unsafe_allow_html=True)
                for p in precedents:
                    st.markdown(f"""
                    <div class="law-card">
                        <div class="title">{esc(p.get('case_name'))}</div>
                        <div class="meta">{esc(p.get('court'))} · {esc(p.get('year'))}</div>
                        <div class="relevance">{esc(p.get('relevance'))}</div>
                    </div>
                    """, unsafe_allow_html=True)
            if evidentiary_notes:
                st.markdown('<div class="sublabel">Evidentiary Notes</div>', unsafe_allow_html=True)
                items = "".join(f"<li>{esc(n)}</li>" for n in evidentiary_notes)
                st.markdown(f'<ul class="bullet-list">{items}</ul>', unsafe_allow_html=True)
            if unsettled:
                st.markdown('<div class="sublabel">Unsettled Questions</div>', unsafe_allow_html=True)
                items = "".join(f"<li>{esc(q)}</li>" for q in unsettled)
                st.markdown(f'<ul class="bullet-list">{items}</ul>', unsafe_allow_html=True)
            if not (sections or precedents or evidentiary_notes or unsettled):
                st.markdown('<div class="empty">No applicable law identified.</div>', unsafe_allow_html=True)
        else:
            laws = st.session_state.case_state.get("laws")
            sections_txt = st.session_state.case_state.get("sections_applied")
            precedents_txt = st.session_state.case_state.get("precedents")
            if laws or sections_txt or precedents_txt:
                if laws and laws != "Not specified":
                    st.markdown(f'<div class="item"><strong>Laws:</strong> <span class="value">{esc(laws)}</span></div>', unsafe_allow_html=True)
                if sections_txt and sections_txt != "Not specified":
                    st.markdown(f'<div class="item"><strong>Sections:</strong> <span class="value">{esc(sections_txt)}</span></div>', unsafe_allow_html=True)
                if precedents_txt and precedents_txt != "Not specified":
                    st.markdown(f'<div class="item"><strong>Precedents:</strong> <span class="value">{esc(precedents_txt)}</span></div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="empty">Researching applicable laws...</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_cons:
        st.markdown('<div class="top-card"><h4>🧭 Internal Consultant</h4>', unsafe_allow_html=True)
        consultant = st.session_state.case_state.get("consultant")
        if consultant:
            st.markdown(f'<div class="item"><span class="value">{esc(consultant)}</span></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="empty">Awaiting internal consultant review...</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ----- ROW 2: JUDGE -----
    judge_verdict = st.session_state.case_state.get("judge_verdict")
    verdict_short = st.session_state.case_state.get("verdict_short")
    confidence = st.session_state.case_state.get("confidence")

    if not verdict_short:
        st.markdown("""
        <div class="judge-container">
            <span class="label">👨‍⚖️ The Hon'ble Judge</span><br>
            <span style="color: #94A3B8; font-size: 18px;">Deliberating on the case...</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        v_lower = str(verdict_short).lower()
        if "not guilty" in v_lower:
            verdict_color = "verdict-green"
            status_text = "NOT GUILTY"
        elif "partially" in v_lower:
            verdict_color = "verdict-amber"
            status_text = "PARTIALLY LIABLE"
        elif "guilty" in v_lower:
            verdict_color = "verdict-red"
            status_text = "GUILTY"
        else:
            verdict_color = "verdict-amber"
            status_text = esc(verdict_short).upper()

        st.markdown(f"""
        <div class="judge-container">
            <span class="label">👨‍⚖️ The Hon'ble Judge</span><br>
            <span class="verdict-text {verdict_color}">{status_text}</span><br>
            <span style="color: #475569; font-size: 16px;">{esc(verdict_short)}</span><br>
            <span class="confidence">Confidence {esc(confidence)}%</span>
        </div>
        """, unsafe_allow_html=True)

    if judge_verdict:
        findings = judge_verdict.get("findings")
        pros_assessment = judge_verdict.get("prosecution_assessment")
        def_assessment = judge_verdict.get("defense_assessment")
        reasoning = judge_verdict.get("reasoning")
        sections_applied_list = judge_verdict.get("sections_applied") or []
        probable_punishment = judge_verdict.get("probable_punishment")
        if findings or pros_assessment or def_assessment:
            st.markdown('<div class="verdict-grid">', unsafe_allow_html=True)
            if findings:
                st.markdown(f"""
                <div class="verdict-field">
                    <span class="label">Findings</span>
                    <div class="content">{esc(findings)}</div>
                </div>
                """, unsafe_allow_html=True)
            if pros_assessment:
                st.markdown(f"""
                <div class="verdict-field">
                    <span class="label">Prosecution Assessment</span>
                    <div class="content">{esc(pros_assessment)}</div>
                </div>
                """, unsafe_allow_html=True)
            if def_assessment:
                st.markdown(f"""
                <div class="verdict-field">
                    <span class="label">Defense Assessment</span>
                    <div class="content">{esc(def_assessment)}</div>
                </div>
                """, unsafe_allow_html=True)
            if probable_punishment:
                st.markdown(f"""
                <div class="verdict-field">
                    <span class="label">Probable Punishment</span>
                    <div class="content">{esc(probable_punishment)}</div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        if sections_applied_list:
            pills = "".join(f'<span class="sections-pill">{esc(s)}</span>' for s in sections_applied_list)
            st.markdown(f"""
            <div class="verdict-reasoning">
                <span class="label">⚖️ Sections Applied</span>
                <div class="sections-pill-row">{pills}</div>
            </div>
            """, unsafe_allow_html=True)
        if reasoning:
            st.markdown(f"""
            <div class="verdict-reasoning">
                <span class="label">📜 Reasoning</span>
                <div class="content">{esc(reasoning)}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        full_reasoning = st.session_state.case_state.get("verdict", "")
        if full_reasoning and "Error" not in full_reasoning:
            st.markdown(f"""
            <div class="verdict-reasoning">
                <span class="label">📜 Full Verdict &amp; Reasoning</span>
                <div class="content">{esc(full_reasoning)}</div>
            </div>
            """, unsafe_allow_html=True)
        elif verdict_short:
            st.markdown(f"""
            <div class="verdict-reasoning">
                <span class="label">📜 Verdict Summary</span>
                <div class="content">{esc(verdict_short)}</div>
            </div>
            """, unsafe_allow_html=True)

    # ----- ROW 3: PROSECUTOR R1 | DEFENSE R1 -----
    col_pros_r1, col_def_r1 = st.columns(2, gap="large")
    with col_pros_r1:
        st.markdown("""
        <div class="debate-column">
            <div class="col-header">
                <span class="icon">⚔️</span>
                <h3>Prosecution</h3>
                <span class="sub">Round 1 — Opening</span>
            </div>
        """, unsafe_allow_html=True)
        r1 = st.session_state.case_state.get("pros_r1")
        if r1:
            st.markdown(f'<div class="argument-block prosecution">{esc(r1)}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="empty-state">⏳ Awaiting opening argument...</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_def_r1:
        st.markdown("""
        <div class="debate-column">
            <div class="col-header">
                <span class="icon">🛡️</span>
                <h3>Defense</h3>
                <span class="sub">Round 1 — Opening</span>
            </div>
        """, unsafe_allow_html=True)
        r1 = st.session_state.case_state.get("def_r1")
        if r1:
            st.markdown(f'<div class="argument-block defense">{esc(r1)}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="empty-state">⏳ Awaiting opening argument...</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ----- ROW 4: PROSECUTOR R2 | DEFENSE R2 -----
    col_pros_r2, col_def_r2 = st.columns(2, gap="large")
    with col_pros_r2:
        st.markdown("""
        <div class="debate-column">
            <div class="col-header">
                <span class="icon">⚔️</span>
                <h3>Prosecution</h3>
                <span class="sub">Round 2 — Closing</span>
            </div>
        """, unsafe_allow_html=True)
        r2 = st.session_state.case_state.get("pros_r2")
        if r2:
            st.markdown(f'<div class="argument-block prosecution">{esc(r2)}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="empty-state">⏳ Awaiting closing argument...</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_def_r2:
        st.markdown("""
        <div class="debate-column">
            <div class="col-header">
                <span class="icon">🛡️</span>
                <h3>Defense</h3>
                <span class="sub">Round 2 — Closing</span>
            </div>
        """, unsafe_allow_html=True)
        r2 = st.session_state.case_state.get("def_r2")
        if r2:
            st.markdown(f'<div class="argument-block defense">{esc(r2)}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="empty-state">⏳ Awaiting closing argument...</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ----- ROW 5: COURT REPORTER -----
    headline = st.session_state.case_state.get("headline")
    report = st.session_state.case_state.get("report")
    st.markdown('<div class="gold-divider"></div>', unsafe_allow_html=True)
    if headline or report:
        st.markdown("""
        <div class="reporter-card">
            <h4>📰 Court Reporter</h4>
        """, unsafe_allow_html=True)
        if headline:
            st.markdown(f'<div class="headline">📌 {esc(headline)}</div>', unsafe_allow_html=True)
        if report:
            st.markdown(f'<div class="report">{esc(report)}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="reporter-card">
            <h4>📰 Court Reporter</h4>
            <div class="empty">⏳ Preparing the case summary...</div>
        </div>
        """, unsafe_allow_html=True)

    # ----- CONSULTANT SPARROW -----
    show_consultant_panel = (
        st.session_state.case_state.get("top_consultant")
        or st.session_state.simulation_complete
        or st.session_state.case_state.get("report")
        or st.session_state.case_state.get("judge_verdict")
        or st.session_state.case_state.get("is_running")
    )
    if show_consultant_panel:
        consultant_sparrow = st.session_state.case_state.get("top_consultant")
        st.markdown("""
        <div class="top-card consultant-panel" style="margin-top: 1rem;">
            <h4>🏛️ Consultant Sparrow</h4>
        """, unsafe_allow_html=True)
        if consultant_sparrow and str(consultant_sparrow).strip():
            st.markdown(f'<div class="item"><span class="value">{esc(consultant_sparrow)}</span></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="empty">⏳ Consultant Sparrow is reviewing the full case...</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ----- STREAMING ENGINE (with error handling) -----
    if st.session_state.case_state.get("is_running") and not st.session_state.simulation_complete:
        progress_placeholder = st.empty()
        progress_placeholder.info("🔄 Streaming simulation events...")

        if st.session_state.stream_event_generator is not None:
            try:
                event_type, data = next(st.session_state.stream_event_generator)

                if event_type == "agent":
                    payload = json.loads(data)  # {node_name: partial_state_dict}

                    for node_name, partial in payload.items():
                        elapsed = time.time() - st.session_state.sim_start_time
                        st.session_state.node_times[node_name] = elapsed

                        for key, value in partial.items():
                            if value is not None:
                                st.session_state.case_state[key] = value

                    progress_placeholder.info(f"🔄 Received: {', '.join(payload.keys())}")

                elif event_type == "error":
                    error_data = json.loads(data)
                    error_msg = error_data.get("error", "Unknown error")
                    st.session_state.simulation_error = error_msg
                    st.session_state.case_state["is_running"] = False
                    st.session_state.stream_event_generator = None
                    progress_placeholder.error("❌ Simulation error")
                    st.rerun()

                elif event_type == "done":
                    st.session_state.simulation_complete = True
                    st.session_state.case_state["is_running"] = False
                    st.session_state.stream_event_generator = None
                    progress_placeholder.success("✅ Simulation completed!")

                st.rerun()

            except StopIteration:
                st.session_state.simulation_error = "Stream ended unexpectedly (no 'done' event)."
                st.session_state.case_state["is_running"] = False
                st.session_state.stream_event_generator = None
                progress_placeholder.error("❌ Simulation stopped unexpectedly.")
                st.rerun()

            except requests.exceptions.RequestException as e:
                st.session_state.simulation_error = f"API error: {e}"
                st.session_state.case_state["is_running"] = False
                st.session_state.stream_event_generator = None
                progress_placeholder.error(f"❌ API error: {e}")
                st.rerun()

            except Exception as e:
                st.session_state.simulation_error = str(e)
                st.session_state.case_state["is_running"] = False
                st.session_state.stream_event_generator = None
                progress_placeholder.error(f"❌ Unexpected error: {e}")
                st.rerun()

    # ----- IDLE / RESET & DOWNLOAD -----
    if not st.session_state.case_state.get("is_running") and not st.session_state.simulation_complete:
        if not st.session_state.case_state.get("complaint"):
            st.markdown("""
            <div class="idle-state">
                <div class="icon">🏛️</div>
                <h2>The Court Awaits</h2>
                <p>Enter a case brief above to begin the adversarial simulation.</p>
            </div>
            """, unsafe_allow_html=True)

    if st.session_state.simulation_complete:
        st.markdown('<div class="gold-divider"></div>', unsafe_allow_html=True)

        if not st.session_state.metrics_recorded:
            metrics = st.session_state.evaluator.evaluate_case(
                st.session_state.case_state,
                st.session_state.node_times
            )
            st.session_state.metrics_recorded = True
            st.session_state.last_metrics = metrics
            st.success(f"✅ Case evaluated. Quality Score: {metrics.overall_quality_score:.1f}/100")

        s = st.session_state.case_state
        report_content = _build_report_content(s)

        col_btn1, col_btn2, col_btn3 = st.columns(3)
        with col_btn1:
            st.download_button(
                label="📄 Download PDF",
                data=_build_pdf_bytes(report_content),
                file_name="courtroom_report.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        with col_btn2:
            st.download_button(
                label="📥 Download Markdown",
                data=report_content,
                file_name="courtroom_report.md",
                mime="text/markdown",
                use_container_width=True,
            )
        with col_btn3:
            if st.button("🔄 Start New Case", use_container_width=True):
                st.session_state.case_state = dict(EMPTY_CASE_STATE)
                st.session_state.simulation_complete = False
                st.session_state.stream_event_generator = None
                st.session_state.node_times = {}
                st.session_state.metrics_recorded = False
                st.session_state.last_metrics = None
                st.session_state.simulation_error = None
                st.session_state.complaint_input = ""
                st.session_state.uploaded_complaint = ""
                st.rerun()

# ============================================
# TAB 2: METRICS
# ============================================
with tab_metrics:
    show_evaluation_dashboard()