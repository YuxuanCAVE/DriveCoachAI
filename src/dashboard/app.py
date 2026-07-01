from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import BinaryIO

import pandas as pd
import streamlit as st

from src.analysis.behaviour_metrics import compute_behaviour_metrics
from src.analysis.event_detector import detect_events
from src.analysis.physiological_metrics import compute_physiological_metrics
from src.dashboard.charts import AMBER, BLUE, GREEN, RED, TEAL, heart_rate_chart, line_chart
from src.dashboard.reporting import build_coaching_report
from src.dashboard.styles import apply_dashboard_style
from src.data.loader import load_heart_rate, load_vehicle_log
from src.data.synchronizer import synchronize_to_1hz
from src.data.validator import validate_heart_rate_data, validate_vehicle_data


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_VEHICLE = PROJECT_ROOT / "data" / "sample_vehicle_log.csv"
SAMPLE_HEART_RATE = PROJECT_ROOT / "data" / "sample_heart_rate.csv"


@dataclass(frozen=True)
class AnalysisResult:
    vehicle: pd.DataFrame
    heart_rate: pd.DataFrame
    synchronized: pd.DataFrame
    behaviour_metrics: dict[str, float]
    physiological_metrics: dict[str, object]
    events: list[dict[str, object]]
    source_label: str


def _load_uploaded_or_sample(
    vehicle_file: BinaryIO | None,
    heart_rate_file: BinaryIO | None,
) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    if vehicle_file is None and heart_rate_file is None:
        return load_vehicle_log(SAMPLE_VEHICLE), load_heart_rate(SAMPLE_HEART_RATE), "Sample session"
    if vehicle_file is None or heart_rate_file is None:
        raise ValueError("Upload both vehicle_log.csv and heart_rate.csv, or leave both empty to use sample data.")

    with NamedTemporaryFile(suffix=".csv", delete=False) as vehicle_tmp:
        vehicle_tmp.write(vehicle_file.getbuffer())
        vehicle_path = Path(vehicle_tmp.name)
    with NamedTemporaryFile(suffix=".csv", delete=False) as heart_tmp:
        heart_tmp.write(heart_rate_file.getbuffer())
        heart_rate_path = Path(heart_tmp.name)

    try:
        return load_vehicle_log(vehicle_path), load_heart_rate(heart_rate_path), "Uploaded session"
    finally:
        vehicle_path.unlink(missing_ok=True)
        heart_rate_path.unlink(missing_ok=True)


@st.cache_data(show_spinner=False)
def _run_analysis_cached(
    vehicle_bytes: bytes | None,
    heart_rate_bytes: bytes | None,
    vehicle_name: str | None,
    heart_rate_name: str | None,
) -> AnalysisResult:
    vehicle_file = _BytesUpload(vehicle_bytes, vehicle_name) if vehicle_bytes else None
    heart_rate_file = _BytesUpload(heart_rate_bytes, heart_rate_name) if heart_rate_bytes else None
    vehicle_raw, heart_rate_raw, source_label = _load_uploaded_or_sample(vehicle_file, heart_rate_file)

    vehicle = validate_vehicle_data(vehicle_raw)
    heart_rate = validate_heart_rate_data(heart_rate_raw)
    synchronized = synchronize_to_1hz(vehicle, heart_rate)
    behaviour_metrics = compute_behaviour_metrics(synchronized)
    physiological_metrics = compute_physiological_metrics(synchronized, rolling_window=30)
    synchronized = synchronized.copy()
    synchronized["rolling_hr_mean"] = physiological_metrics["rolling_hr_mean"]
    synchronized["rolling_hr_std"] = physiological_metrics["rolling_hr_std"]
    events = detect_events(synchronized, baseline_hr=float(physiological_metrics["baseline_hr"]))

    return AnalysisResult(
        vehicle=vehicle,
        heart_rate=heart_rate,
        synchronized=synchronized,
        behaviour_metrics=behaviour_metrics,
        physiological_metrics=physiological_metrics,
        events=events,
        source_label=source_label,
    )


class _BytesUpload:
    def __init__(self, data: bytes | None, name: str | None) -> None:
        self._data = data or b""
        self.name = name or "uploaded.csv"

    def getbuffer(self) -> memoryview:
        return memoryview(self._data)


def _format_seconds(seconds: float) -> str:
    minutes = int(seconds // 60)
    remaining = int(seconds % 60)
    return f"{minutes:02d}:{remaining:02d}"


def _metric_card(label: str, value: str, unit: str, note: str) -> None:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}<span class="metric-unit">{unit}</span></div>
            <div class="metric-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _panel_title(title: str, detail: str) -> None:
    st.markdown(
        f"""
        <div class="panel-title">
            <strong>{title}</strong>
            <span>{detail}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _score_average(result: AnalysisResult) -> float:
    physiological_score = max(
        0.0,
        100.0 - min(abs(float(result.physiological_metrics["hr_delta_percent"])) * 2.5, 100.0),
    )
    return (
        result.behaviour_metrics["lateral_stability_score"]
        + result.behaviour_metrics["longitudinal_smoothness_score"]
        + physiological_score
    ) / 3.0


def _severity_counts(events: list[dict[str, object]]) -> dict[str, int]:
    return {
        "low": sum(1 for event in events if event.get("severity") == "low"),
        "medium": sum(1 for event in events if event.get("severity") == "medium"),
        "high": sum(1 for event in events if event.get("severity") == "high"),
    }


def _render_sidebar() -> tuple[bytes | None, bytes | None, str | None, str | None, bool]:
    with st.sidebar:
        st.markdown(
            """
            <div class="eyebrow">ADAS analysis suite</div>
            <h2 style="margin-top:0;color:#e5ecf6;">Human-Centred AI Driving Coach</h2>
            <p class="muted">Offline telemetry and physiological-state review for driver monitoring studies.</p>
            """,
            unsafe_allow_html=True,
        )
        st.divider()

        vehicle_file = st.file_uploader("Upload vehicle_log.csv", type=["csv"])
        heart_rate_file = st.file_uploader("Upload heart_rate.csv", type=["csv"])

        st.markdown("#### Session metadata")
        session_id = st.text_input("Session ID", value="ADAS-SESSION-001")
        driver_group = st.selectbox("Driver group", ["Test driver", "Participant", "Engineer review"])
        road_context = st.selectbox("Road context", ["Mixed route", "Urban", "Highway", "Closed track"])
        notes = st.text_area("Notes", value="Sample deterministic analysis run.", height=86)

        run_clicked = st.button("Run Analysis")
        use_initial = "analysis_has_run" not in st.session_state
        should_run = run_clicked or use_initial
        if should_run:
            st.session_state["analysis_has_run"] = True

        status = "Ready to analyse uploaded CSVs" if vehicle_file and heart_rate_file else "Using generated sample data"
        st.markdown(
            f"""
            <div class="panel" style="margin-top:1rem;">
                <div class="metric-label">Analysis status</div>
                <div style="color:#20d6a2;font-weight:700;margin-top:.35rem;">{status}</div>
                <div class="metric-note">{session_id} · {driver_group} · {road_context}</div>
                <div class="metric-note">{notes}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        vehicle_bytes = vehicle_file.getvalue() if vehicle_file else None
        heart_rate_bytes = heart_rate_file.getvalue() if heart_rate_file else None
        vehicle_name = vehicle_file.name if vehicle_file else None
        heart_rate_name = heart_rate_file.name if heart_rate_file else None
        return vehicle_bytes, heart_rate_bytes, vehicle_name, heart_rate_name, should_run


def _render_header(result: AnalysisResult) -> None:
    duration = result.synchronized["timestamp"].max() - result.synchronized["timestamp"].min()
    st.markdown(
        f"""
        <div class="hero-shell">
            <div class="eyebrow">Connected-vehicle analytics · deterministic foundation</div>
            <h1>Human-Centred AI Driving Coach Agent</h1>
            <div class="muted">Driving behaviour, vehicle dynamics, and heart-rate activation reviewed in one engineering dashboard.</div>
            <div class="session-strip">
                <span class="session-pill">{result.source_label}</span>
                <span class="session-pill">{len(result.synchronized):,} synchronized samples at 1 Hz</span>
                <span class="session-pill">Duration {_format_seconds(duration)}</span>
                <span class="session-pill">No LLM generation in this milestone</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_overview(result: AnalysisResult) -> None:
    behaviour = result.behaviour_metrics
    physiology = result.physiological_metrics
    severity = _severity_counts(result.events)
    overall = _score_average(result)
    activation = float(physiology["hr_delta_percent"])

    cols = st.columns(5)
    with cols[0]:
        _metric_card("Overall smoothness", f"{overall:.0f}", "/100", "Average of lateral, longitudinal, and activation indicators")
    with cols[1]:
        _metric_card("Lateral stability", f"{behaviour['lateral_stability_score']:.0f}", "/100", f"Max |ay| {behaviour['max_abs_ay']:.2f} m/s^2")
    with cols[2]:
        _metric_card("Longitudinal smoothness", f"{behaviour['longitudinal_smoothness_score']:.0f}", "/100", f"Max |ax| {behaviour['max_abs_ax']:.2f} m/s^2")
    with cols[3]:
        _metric_card("Physio activation", f"{activation:+.1f}", "%", f"Baseline {float(physiology['baseline_hr']):.1f} bpm")
    with cols[4]:
        _metric_card("Risk events", str(len(result.events)), "", f"{severity['high']} high · {severity['medium']} medium · {severity['low']} low")


def _render_behaviour(result: AnalysisResult) -> None:
    st.markdown("## Behaviour Analysis")
    top_left, top_right = st.columns(2)
    with top_left:
        _panel_title("Speed over time", "m/s · event context")
        st.plotly_chart(
            line_chart(result.synchronized, "speed", "Speed", "m/s", BLUE, result.events, set()),
            use_container_width=True,
            config={"displayModeBar": False},
        )
    with top_right:
        _panel_title("Longitudinal acceleration", "harsh braking / acceleration")
        st.plotly_chart(
            line_chart(
                result.synchronized,
                "ax",
                "Longitudinal acceleration",
                "m/s^2",
                TEAL,
                result.events,
                {"harsh_braking", "harsh_acceleration"},
            ),
            use_container_width=True,
            config={"displayModeBar": False},
        )

    bottom_left, bottom_right = st.columns(2)
    with bottom_left:
        _panel_title("Lateral acceleration", "cornering and lateral demand")
        st.plotly_chart(
            line_chart(
                result.synchronized,
                "ay",
                "Lateral acceleration",
                "m/s^2",
                AMBER,
                result.events,
                {"high_lateral_acceleration"},
            ),
            use_container_width=True,
            config={"displayModeBar": False},
        )
    with bottom_right:
        _panel_title("Yaw rate", "sharp yaw motion")
        st.plotly_chart(
            line_chart(
                result.synchronized,
                "yaw_rate",
                "Yaw rate",
                "rad/s",
                RED,
                result.events,
                {"sharp_yaw_motion"},
            ),
            use_container_width=True,
            config={"displayModeBar": False},
        )


def _render_driver_state(result: AnalysisResult) -> None:
    st.markdown("## Driver State")
    left, right = st.columns([1.35, 0.65])
    with left:
        _panel_title("Heart rate and rolling activation trend", "baseline comparison · bpm")
        st.plotly_chart(
            heart_rate_chart(
                result.synchronized,
                float(result.physiological_metrics["baseline_hr"]),
                result.events,
            ),
            use_container_width=True,
            config={"displayModeBar": False},
        )
    with right:
        physiology = result.physiological_metrics
        rows = [
            ("Mean HR", f"{float(physiology['mean_hr']):.1f} bpm"),
            ("Max HR", f"{float(physiology['max_hr']):.1f} bpm"),
            ("Min HR", f"{float(physiology['min_hr']):.1f} bpm"),
            ("Std HR", f"{float(physiology['std_hr']):.1f} bpm"),
            ("RMSSD", "not available" if physiology["rmssd"] is None else f"{float(physiology['rmssd']):.3f} s"),
        ]
        row_html = "".join(
            f"""
            <div style="display:flex;justify-content:space-between;border-bottom:1px solid rgba(148,163,184,.12);padding:.55rem 0;">
                <span class="muted">{label}</span>
                <strong style="color:#e5ecf6;">{value}</strong>
            </div>
            """
            for label, value in rows
        )
        st.markdown(
            f"""
            <div class="panel">
                <div class="panel-title">
                    <strong>Physiological indicators</strong>
                    <span>activation signals only</span>
                </div>
                {row_html}
                <p class="metric-note">Heart-rate features are indicators of physiological activation and are not medical claims.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_events(result: AnalysisResult) -> None:
    st.markdown("## Risk Event Timeline")
    if not result.events:
        st.info("No rule-based risk events detected for the current thresholds.")
        return

    left, right = st.columns([0.72, 0.28])
    with left:
        for event in result.events:
            evidence = event["evidence"]
            event_type = str(event["type"]).replace("_", " ")
            severity = str(event["severity"])
            st.markdown(
                f"""
                <div class="event-row">
                    <div class="event-time">{_format_seconds(float(event["start_time"]))}</div>
                    <div>
                        <div class="event-type">{event_type}</div>
                        <div class="event-evidence">
                            {evidence["column"]}: peak {float(evidence["peak_value"]):.2f}, threshold {float(evidence["threshold"]):.2f}
                        </div>
                    </div>
                    <div class="severity {severity}">{severity}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    with right:
        event_table = pd.DataFrame(
            [
                {
                    "time": _format_seconds(float(event["start_time"])),
                    "type": str(event["type"]).replace("_", " "),
                    "severity": event["severity"],
                }
                for event in result.events
            ]
        )
        st.dataframe(event_table, use_container_width=True, hide_index=True)


def _render_report(result: AnalysisResult) -> None:
    st.markdown("## AI Coaching Report")
    st.markdown(
        '<p class="muted">Deterministic report draft for the future AI coaching layer. No LLM, LangGraph, or RAG is used here.</p>',
        unsafe_allow_html=True,
    )
    report = build_coaching_report(result.behaviour_metrics, result.physiological_metrics, result.events)
    cols = st.columns([1, 1, 1])
    sections = list(report.items())
    for index, (title, bullets) in enumerate(sections):
        with cols[index % 3]:
            bullet_html = "".join(f"<li>{bullet}</li>" for bullet in bullets)
            st.markdown(
                f"""
                <div class="report-card">
                    <h3>{title}</h3>
                    <ul>{bullet_html}</ul>
                </div>
                """,
                unsafe_allow_html=True,
            )


def _run_analysis_from_sidebar() -> AnalysisResult | None:
    vehicle_bytes, heart_rate_bytes, vehicle_name, heart_rate_name, should_run = _render_sidebar()
    if not should_run and "last_analysis" in st.session_state:
        return st.session_state["last_analysis"]
    try:
        result = _run_analysis_cached(vehicle_bytes, heart_rate_bytes, vehicle_name, heart_rate_name)
        st.session_state["last_analysis"] = result
        return result
    except Exception as exc:
        st.error(f"Analysis failed: {exc}")
        return None


def run_dashboard() -> None:
    st.set_page_config(
        page_title="Human-Centred AI Driving Coach",
        page_icon="H",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    apply_dashboard_style()
    result = _run_analysis_from_sidebar()
    if result is None:
        return

    _render_header(result)
    _render_overview(result)
    _render_behaviour(result)
    _render_driver_state(result)
    _render_events(result)
    _render_report(result)
