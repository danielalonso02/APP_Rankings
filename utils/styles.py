"""
Shared CSS styles and UI helper functions for the Liga F Analytics platform.
Centralizes all styling to avoid duplication across pages.
"""
import streamlit as st


# ==================== COLOR PALETTE ====================
COLORS = {
    "primary_dark": "#8B0000",      # Athletic dark red
    "primary": "#EE2523",           # Athletic red
    "primary_light": "#F87171",     # Light red
    "text_dark": "#1A1A1A",
    "text_medium": "#4A4A4A",
    "text_light": "#6A6A6A",
    "text_muted": "#9A9A9A",
    "bg_white": "#FFFFFF",
    "bg_light": "#FFF5F5",          # Very light red tint
    "bg_secondary": "#F5F0F0",
    "border": "#E8D8D8",
    "border_hover": "#D4C0C0",
    "success": "#16a34a",
    "success_light": "#86efac",
    "danger": "#dc2626",
}


# ==================== CSS BLOCKS ====================

SIDEBAR_CSS = """
/* Sidebar styling */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #8B0000 0%, #EE2523 100%);
    padding-top: 0;
}

[data-testid="stSidebar"] > div:first-child {
    background: transparent;
}

/* Sidebar text colors */
[data-testid="stSidebar"] .element-container {
    color: white;
}

[data-testid="stSidebar"] label {
    color: white !important;
    font-weight: 600;
}

[data-testid="stSidebar"] p {
    color: rgba(255, 255, 255, 0.9);
}

[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] h4 {
    color: white !important;
}
"""

MAIN_CONTENT_CSS = """
/* Main content padding */
.main {
    padding-top: 2rem;
}
"""

SECTION_HEADER_CSS = """
/* Section headers */
.section-header {
    color: #1A1A1A;
    font-size: 1.8rem;
    font-weight: 700;
    margin: 2rem 0 1rem 0;
    border-bottom: 3px solid #EE2523;
    padding-bottom: 0.5rem;
}

/* Sub headers */
.sub-header {
    color: #8B0000;
    font-size: 1.2rem;
    font-weight: 700;
    margin: 1.5rem 0 1rem 0;
    text-align: center;
}
"""

CARD_CSS = """
/* Feature cards */
.feature-card {
    background-color: #FFF5F5;
    border: 1px solid #E8D8D8;
    border-radius: 8px;
    padding: 1.5rem;
    margin: 1rem 0;
    transition: all 0.3s ease;
}

.feature-card:hover {
    box-shadow: 0 4px 6px rgba(238, 37, 35, 0.15);
    border-color: #D4C0C0;
}

.feature-title {
    color: #8B0000;
    font-size: 1.1rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
}

.feature-description {
    color: #4A4A4A;
    font-size: 0.95rem;
    line-height: 1.5;
}

/* Section cards */
.section-card {
    background-color: #FFF5F5;
    border: 1px solid #E8D8D8;
    border-radius: 12px;
    padding: 2rem;
    margin: 1.5rem 0;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* Info boxes */
.info-box {
    border-left: 4px solid #EE2523;
    background-color: #FFF5F5;
    padding: 1rem 1.5rem;
    margin: 1rem 0;
    border-radius: 0 8px 8px 0;
}

/* Rating cards */
.rating-card {
    background-color: white;
    border: 1px solid #E8D8D8;
    border-radius: 8px;
    padding: 1rem;
    text-align: center;
    transition: all 0.3s ease;
}

.rating-card:hover {
    box-shadow: 0 4px 6px rgba(238, 37, 35, 0.15);
}
"""

NAV_CARD_CSS = """
/* Navigation cards */
.nav-card {
    border-radius: 12px;
    padding: 2rem;
    text-align: center;
    color: white;
    margin: 1rem 0;
    min-height: 320px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    transition: all 0.3s ease;
    cursor: pointer;
}

.nav-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
}

.nav-card-content {
    flex-grow: 1;
    display: flex;
    flex-direction: column;
    justify-content: center;
}

.nav-card-icon {
    font-size: 3rem;
    margin-bottom: 1rem;
}

.nav-card-title {
    color: white;
    font-size: 1.4rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
}

.nav-card-description {
    color: rgba(255,255,255,0.9);
    font-size: 0.95rem;
    margin-bottom: 1.5rem;
    line-height: 1.5;
}

.nav-card-button {
    background-color: rgba(255, 255, 255, 0.2);
    border: 2px solid white;
    color: white;
    padding: 0.75rem 1.5rem;
    border-radius: 8px;
    font-weight: 600;
    font-size: 1rem;
    transition: all 0.3s ease;
    backdrop-filter: blur(10px);
    margin-top: 1rem;
}

.nav-card:hover .nav-card-button {
    background-color: white;
    color: #8B0000;
}
"""

METRIC_CSS = """
/* Stats metric cards */
.metric-card {
    background-color: white;
    border: 2px solid #E8D8D8;
    border-radius: 8px;
    padding: 1rem;
    text-align: center;
}
"""

DIVIDER_CSS = """
/* Divider styling */
hr {
    margin: 2rem 0;
    border: none;
    border-top: 2px solid #E8D8D8;
}
"""

REPORT_STATUS_CSS = """
/* Status indicators for report generation */
.status-running {
    color: #f59e0b;
    font-weight: 600;
}

.status-complete {
    color: #16a34a;
    font-weight: 600;
}

.status-error {
    color: #dc2626;
    font-weight: 600;
}

/* Log viewer */
.log-viewer {
    height: 300px;
    overflow-y: auto;
    border: 1px solid #e2e8f0;
    padding: 1rem;
    background-color: #1e293b;
    color: #e2e8f0;
    font-family: monospace;
    font-size: 0.85rem;
    border-radius: 8px;
}

/* Loader spinner animation */
.loader {
    border: 4px solid #E8D8D8;
    border-top: 4px solid #EE2523;
    border-radius: 50%;
    width: 16px;
    height: 16px;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

.loader-container {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    font-weight: bold;
    font-size: 16px;
    color: #1A1A1A;
}
"""

LOGIN_CSS = """
/* Hide sidebar on login page */
[data-testid="stSidebar"] {
    display: none;
    visibility: hidden;
}

/* Login form styling */
.login-header {
    text-align: center;
    margin-bottom: 2rem;
}
"""

PAGE_HEADER_CSS = """
/* Consistent page header */
.page-header {
    text-align: center;
    margin-bottom: 2rem;
}

.page-header h1 {
    color: #8B0000;
    margin-bottom: 0.5rem;
}

.page-header p {
    color: #6A6A6A;
    font-size: 1.1rem;
    margin-top: 0;
}

/* Page footer */
.page-footer {
    text-align: center;
    color: #9A9A9A;
    font-size: 0.85rem;
    padding: 2rem 0;
}

.page-footer p {
    margin: 0.25rem 0;
}
"""


# ==================== INJECTION FUNCTIONS ====================

def inject_global_css():
    """Inject the standard CSS used by all pages (sidebar + main content + headers + cards)."""
    combined = f"<style>{SIDEBAR_CSS}{MAIN_CONTENT_CSS}{SECTION_HEADER_CSS}{CARD_CSS}{PAGE_HEADER_CSS}{DIVIDER_CSS}</style>"
    st.markdown(combined, unsafe_allow_html=True)


def inject_home_css():
    """Inject CSS for the home page (includes nav cards and metrics on top of global)."""
    combined = f"<style>{SIDEBAR_CSS}{MAIN_CONTENT_CSS}{SECTION_HEADER_CSS}{CARD_CSS}{NAV_CARD_CSS}{METRIC_CSS}{PAGE_HEADER_CSS}{DIVIDER_CSS}</style>"
    st.markdown(combined, unsafe_allow_html=True)


def inject_report_css():
    """Inject CSS for report generation pages (includes status indicators + loader + log viewer)."""
    combined = f"<style>{SIDEBAR_CSS}{MAIN_CONTENT_CSS}{SECTION_HEADER_CSS}{CARD_CSS}{REPORT_STATUS_CSS}{PAGE_HEADER_CSS}{DIVIDER_CSS}</style>"
    st.markdown(combined, unsafe_allow_html=True)


def inject_login_css():
    """Inject CSS for the login page (hides sidebar)."""
    combined = f"<style>{LOGIN_CSS}</style>"
    st.markdown(combined, unsafe_allow_html=True)


# ==================== UI HELPER FUNCTIONS ====================

def feature_card(title, description):
    """Render a feature card with title and description."""
    st.markdown(f"""
        <div class='feature-card'>
            <div class='feature-title'>{title}</div>
            <div class='feature-description'>{description}</div>
        </div>
    """, unsafe_allow_html=True)


def section_header(text):
    """Render a styled section header."""
    st.markdown(f"<h2 class='section-header'>{text}</h2>", unsafe_allow_html=True)


def sub_header(text):
    """Render a styled sub-header."""
    st.markdown(f"<h3 class='sub-header'>{text}</h3>", unsafe_allow_html=True)


def metric_card(value, label):
    """Render a metric card with a large value and label."""
    st.markdown(f"""
        <div class='metric-card'>
            <h2 style='color: #EE2523; margin: 0;'>{value}</h2>
            <p style='color: #6A6A6A; margin: 0;'>{label}</p>
        </div>
    """, unsafe_allow_html=True)


def page_header(title, subtitle=None):
    """Render a consistent centered page header with optional subtitle."""
    subtitle_html = f"<p>{subtitle}</p>" if subtitle else ""
    st.markdown(f"""
        <div class='page-header'>
            <h1>{title}</h1>
            {subtitle_html}
        </div>
    """, unsafe_allow_html=True)
    st.divider()


def page_footer(text="Plataforma de Análisis Liga F", source=None):
    """Render a consistent page footer."""
    source_html = f"<p>{source}</p>" if source else ""
    st.divider()
    st.markdown(f"""
        <div class='page-footer'>
            <p>{text}</p>
            {source_html}
        </div>
    """, unsafe_allow_html=True)


def loader_display(hours, minutes, seconds):
    """Render a spinning loader with elapsed time display."""
    st.markdown(f"""
        <div class="loader-container">
            <div class="loader"></div>
            <span>Ejecutando: {hours:02}:{minutes:02}:{seconds:02}</span>
        </div>
    """, unsafe_allow_html=True)


def log_viewer(content, seconds_since_update=0):
    """Render a styled log viewer box."""
    st.caption(f"Log actualizado hace {seconds_since_update} segundos")
    content_html = content.replace('\n', '<br>')
    st.markdown(f"""
        <div class="log-viewer">
            <pre>{content_html}</pre>
        </div>
    """, unsafe_allow_html=True)
