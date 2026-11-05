"""Copyright (C) 2025 Pierre Marrec
SPDX-License-Identifier: GPL-3.0-or-later
"""

import streamlit as st
from streamlit.logger import get_logger

from utils.auth_state import init_session_state
from utils.config import load_config, redact
from utils.formatting import set_locale
from utils.home_assets import HOME_FEATURE_ART
from utils.styling import apply_theme

logger = get_logger(__name__)

FEATURE_PAGES = {
    "Activities": st.Page("pages/Activities.py", title="Activities"),
    "Activity details": st.Page("pages/Activity.py", title="Activity"),
    "Dashboard": st.Page("pages/Dashboard.py", title="Dashboard"),
    "Analytics": st.Page("pages/Analytics.py", title="Analytics"),
    "Race Pacing": st.Page("pages/RacePacing.py", title="Race Pacing"),
    "Athlete": st.Page("pages/Athlete.py", title="Athlete"),
    "Settings": st.Page("pages/Settings.py", title="Settings"),
}

HOME_CARD_CSS = """
<style>
[class*="st-key-home-feature-card-"] {
    background: rgba(8, 14, 24, 0.42);
    border-radius: 14px;
}

[class*="st-key-home-feature-card-"] [data-testid="stCode"],
[class*="st-key-home-feature-card-"] [data-testid="stCode"] pre,
[class*="st-key-home-feature-card-"] [data-testid="stCode"] code {
    background: transparent !important;
    color: #fff !important;
    border: 0 !important;
    box-shadow: none !important;
    font-weight: 600;
}

[class*="st-key-home-feature-card-"] [data-testid="stPageLink"] a {
    color: #f8fafc !important;
}

[class*="st-key-home-feature-card-"] [data-testid="stPageLink"] a:hover {
    color: #fff !important;
}

[class*="st-key-home-feature-card-"] [data-testid="stPageLink"] p {
    color: #fff !important;
}
</style>
"""


def render_home() -> None:
    cfg = st.session_state["app_config"]
    st.title("Running Manager")
    st.caption("Your running workspace, with quick access to every feature.")
    st.markdown(HOME_CARD_CSS, unsafe_allow_html=True)

    features = [
        (
            "Activities",
            "Browse your activity feed, review sessions, and link completed workouts.",
        ),
        (
            "Activity details",
            "Inspect a selected activity, its metrics, heart-rate zones, and route.",
        ),
        (
            "Dashboard",
            "See training load, fitness trends, and activity performance at a glance.",
        ),
        (
            "Analytics",
            "Compare planned and completed training across dates and activity types.",
        ),
        (
            "Race Pacing",
            "Build and review a pacing plan for a race course.",
        ),
        (
            "Athlete",
            "Manage athlete profiles and training thresholds.",
        ),
        (
            "Settings",
            "Configure integrations, metrics, and application preferences.",
        ),
    ]

    for row_start in range(0, len(features), 3):
        columns = st.columns(3)
        for card_index, (column, (title, description)) in enumerate(
            zip(columns, features[row_start : row_start + 3])
        ):
            with column:
                with st.container(
                    border=True, key=f"home-feature-card-{row_start + card_index}"
                ):
                    st.code(HOME_FEATURE_ART[title], language=None)
                    st.subheader(title)
                    st.write(description)
                    st.page_link(FEATURE_PAGES[title], label=f"Open {title}")

    with st.expander("Environment (sanitized)", expanded=False):
        st.write(
            {
                "DATA_DIR": str(cfg.data_dir),
                "STRAVA_CLIENT_ID": redact(cfg.strava_client_id),
                "STRAVA_REDIRECT_URI": cfg.strava_redirect_uri or "",
            }
        )


def main():
    st.set_page_config(page_title="Running Manager", layout="wide")
    # load_dotenv()
    cfg = load_config()
    # if cfg.mapbox_token:
    #     os.environ.setdefault("MAPBOX_API_KEY", cfg.mapbox_token)
    #     os.environ.setdefault("MAPBOX_TOKEN", cfg.mapbox_token)
    set_locale("fr_FR")
    init_session_state()
    apply_theme()
    st.session_state.setdefault("app_config", cfg)
    st.session_state.setdefault("mapbox_token", cfg.mapbox_token)
    logger.debug("cfg.mapbox: %s", cfg.mapbox_token)

    pages = [st.Page(render_home, title="Running Manager"), *FEATURE_PAGES.values()]
    st.navigation(pages).run()


if __name__ == "__main__":
    main()
