from __future__ import annotations

from collections.abc import Iterable

import pandas as pd
import plotly.graph_objects as go


PLOT_TEMPLATE = "plotly_dark"
BLUE = "#4d7cff"
TEAL = "#20d6a2"
GREEN = "#9be779"
AMBER = "#f5a524"
RED = "#ff5c6c"
GRID = "rgba(148, 163, 184, 0.12)"
TEXT = "#b7c4d7"


EVENT_COLOR_BY_SEVERITY = {
    "low": "rgba(32, 214, 162, 0.24)",
    "medium": "rgba(245, 165, 36, 0.26)",
    "high": "rgba(255, 92, 108, 0.30)",
}


def _base_layout(fig: go.Figure, title: str, y_title: str, height: int = 292) -> go.Figure:
    fig.update_layout(
        template=PLOT_TEMPLATE,
        title_text="",
        height=height,
        margin=dict(l=8, r=12, t=10, b=6),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT, family="Inter, Segoe UI, sans-serif", size=12),
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(0,0,0,0)",
            font=dict(size=11),
        ),
    )
    fig.update_xaxes(
        title_text="Session time (s)",
        gridcolor=GRID,
        zerolinecolor=GRID,
        showline=False,
    )
    fig.update_yaxes(
        title_text=y_title,
        gridcolor=GRID,
        zerolinecolor=GRID,
        showline=False,
    )
    return fig


def _add_event_markers(fig: go.Figure, events: Iterable[dict[str, object]], event_types: set[str]) -> None:
    for event in events:
        if event["type"] not in event_types:
            continue
        start_time = float(event["start_time"])
        end_time = float(event["end_time"])
        if end_time <= start_time:
            end_time = start_time + 0.8
        severity = str(event.get("severity", "low"))
        fig.add_vrect(
            x0=start_time,
            x1=end_time,
            fillcolor=EVENT_COLOR_BY_SEVERITY.get(severity, EVENT_COLOR_BY_SEVERITY["low"]),
            opacity=0.42,
            line_width=0,
            layer="below",
        )


def line_chart(
    df: pd.DataFrame,
    y_column: str,
    label: str,
    y_title: str,
    color: str,
    events: list[dict[str, object]] | None = None,
    marker_event_types: set[str] | None = None,
    secondary_column: str | None = None,
    secondary_label: str | None = None,
    secondary_color: str = TEAL,
    height: int = 292,
) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["timestamp"],
            y=df[y_column],
            mode="lines",
            name=label,
            line=dict(color=color, width=2.2),
        )
    )
    if secondary_column and secondary_column in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["timestamp"],
                y=df[secondary_column],
                mode="lines",
                name=secondary_label or secondary_column,
                line=dict(color=secondary_color, width=2, dash="dot"),
            )
        )

    if events and marker_event_types:
        _add_event_markers(fig, events, marker_event_types)

    return _base_layout(fig, label, y_title, height=height)


def heart_rate_chart(
    df: pd.DataFrame,
    baseline_hr: float,
    events: list[dict[str, object]],
    rolling_column: str = "rolling_hr_mean",
) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["timestamp"],
            y=df["heart_rate"],
            mode="lines",
            name="Heart rate",
            line=dict(color=GREEN, width=2.1),
        )
    )
    if rolling_column in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["timestamp"],
                y=df[rolling_column],
                mode="lines",
                name="Rolling mean",
                line=dict(color=BLUE, width=2, dash="dot"),
            )
        )
    fig.add_hline(
        y=baseline_hr,
        line_dash="dash",
        line_color="rgba(183, 196, 215, 0.55)",
        annotation_text="baseline",
        annotation_font_color=TEXT,
    )
    _add_event_markers(fig, events, {"elevated_physiological_activation"})
    return _base_layout(fig, "Heart rate", "bpm", height=330)
