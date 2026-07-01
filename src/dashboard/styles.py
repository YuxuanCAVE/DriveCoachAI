import streamlit as st


def apply_dashboard_style() -> None:
    st.markdown(
        """
        <style>
        :root {
            --bg: #0b0f14;
            --panel: #141a20;
            --panel-soft: #182029;
            --line: rgba(148, 163, 184, 0.18);
            --text: #e5ecf6;
            --muted: #8b98aa;
            --blue: #2f80ff;
            --teal: #20d6a2;
            --amber: #f5a524;
            --red: #ff5c6c;
        }

        .stApp {
            background:
                radial-gradient(circle at 80% 0%, rgba(32, 214, 162, 0.08), transparent 28%),
                radial-gradient(circle at 15% 15%, rgba(47, 128, 255, 0.10), transparent 32%),
                var(--bg);
            color: var(--text);
            font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }

        header,
        #MainMenu,
        footer,
        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        [data-testid="stStatusWidget"] {
            visibility: hidden;
            height: 0;
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0f141b 0%, #0b0f14 100%);
            border-right: 1px solid var(--line);
        }

        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
        [data-testid="stSidebar"] label {
            color: var(--muted);
        }

        .block-container {
            max-width: 1480px;
            padding-top: 1.4rem;
            padding-bottom: 3rem;
        }

        h1, h2, h3 {
            letter-spacing: 0;
        }

        h1 {
            font-size: 2rem;
            line-height: 1.15;
            margin-bottom: 0.25rem;
        }

        h2 {
            font-size: 1.05rem;
            margin-top: 1.4rem;
        }

        h3 {
            font-size: 0.95rem;
        }

        .hero-shell,
        .metric-card,
        .panel,
        .event-row,
        .report-card {
            background: linear-gradient(180deg, rgba(24, 32, 41, 0.96), rgba(18, 24, 31, 0.96));
            border: 1px solid var(--line);
            box-shadow: 0 14px 32px rgba(0, 0, 0, 0.22);
            border-radius: 18px;
        }

        .hero-shell {
            padding: 1.1rem 1.25rem;
            margin-bottom: 1rem;
        }

        .eyebrow {
            color: var(--teal);
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            margin-bottom: 0.25rem;
        }

        .muted {
            color: var(--muted);
            font-size: 0.86rem;
        }

        .session-strip {
            display: flex;
            flex-wrap: wrap;
            gap: 0.6rem;
            margin-top: 0.85rem;
        }

        .session-pill {
            background: rgba(47, 128, 255, 0.10);
            border: 1px solid rgba(47, 128, 255, 0.25);
            border-radius: 999px;
            color: #bcd3ff;
            font-size: 0.78rem;
            padding: 0.35rem 0.7rem;
        }

        .metric-card {
            padding: 0.95rem 1rem;
            min-height: 132px;
        }

        .metric-label {
            color: var(--muted);
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }

        .metric-value {
            color: var(--text);
            font-size: 1.85rem;
            font-weight: 750;
            margin-top: 0.25rem;
        }

        .metric-unit {
            color: var(--muted);
            font-size: 0.86rem;
            font-weight: 500;
            margin-left: 0.15rem;
        }

        .metric-note {
            color: var(--muted);
            font-size: 0.78rem;
            margin-top: 0.35rem;
        }

        .panel {
            padding: 1rem 1rem 0.75rem 1rem;
            margin-bottom: 1rem;
        }

        [data-testid="stPlotlyChart"] {
            background: linear-gradient(180deg, rgba(24, 32, 41, 0.96), rgba(18, 24, 31, 0.96));
            border: 1px solid var(--line);
            box-shadow: 0 14px 32px rgba(0, 0, 0, 0.22);
            border-radius: 18px;
            padding: 0.8rem 0.8rem 0.35rem 0.8rem;
        }

        .panel-title {
            display: flex;
            align-items: baseline;
            justify-content: space-between;
            gap: 1rem;
            margin: 0.2rem 0 0.5rem 0;
        }

        .panel-title strong {
            color: var(--text);
            font-size: 0.95rem;
        }

        .panel-title span {
            color: var(--muted);
            font-size: 0.76rem;
        }

        .event-row {
            display: grid;
            grid-template-columns: 86px 1fr auto;
            gap: 0.75rem;
            align-items: center;
            padding: 0.72rem 0.8rem;
            margin-bottom: 0.58rem;
        }

        .event-time {
            color: #b7c4d7;
            font-variant-numeric: tabular-nums;
            font-size: 0.82rem;
        }

        .event-type {
            color: var(--text);
            font-weight: 680;
            font-size: 0.86rem;
            text-transform: capitalize;
        }

        .event-evidence {
            color: var(--muted);
            font-size: 0.74rem;
            margin-top: 0.1rem;
        }

        .severity {
            border-radius: 999px;
            font-size: 0.7rem;
            font-weight: 800;
            letter-spacing: 0.08em;
            padding: 0.28rem 0.55rem;
            text-transform: uppercase;
        }

        .severity.low {
            background: rgba(32, 214, 162, 0.14);
            border: 1px solid rgba(32, 214, 162, 0.35);
            color: #5ff0c8;
        }

        .severity.medium {
            background: rgba(245, 165, 36, 0.14);
            border: 1px solid rgba(245, 165, 36, 0.40);
            color: #ffc66d;
        }

        .severity.high {
            background: rgba(255, 92, 108, 0.14);
            border: 1px solid rgba(255, 92, 108, 0.42);
            color: #ff9aa5;
        }

        .report-card {
            padding: 1rem;
            min-height: 168px;
        }

        .report-card ul {
            margin-bottom: 0;
            padding-left: 1.1rem;
        }

        .report-card li {
            color: #c7d1df;
            font-size: 0.86rem;
            margin-bottom: 0.38rem;
        }

        .stButton > button {
            background: linear-gradient(135deg, var(--blue), #20a8ff);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 12px;
            color: white;
            font-weight: 750;
            height: 2.75rem;
            width: 100%;
        }

        .stButton > button:hover {
            border-color: rgba(255, 255, 255, 0.32);
            color: white;
        }

        [data-testid="stFileUploader"] {
            background: rgba(255, 255, 255, 0.025);
            border: 1px solid var(--line);
            border-radius: 12px;
            padding: 0.55rem;
        }

        div[data-testid="stDataFrame"] {
            border: 1px solid var(--line);
            border-radius: 14px;
            overflow: hidden;
        }

        hr {
            border-color: var(--line);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
