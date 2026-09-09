"""Figuras de Plotly del dashboard operativo.

Reglas aplicadas: un solo eje por gráfica (nunca doble eje), color asignado por
función, marcas delgadas con extremos redondeados, cuadrícula discreta,
etiquetas directas selectivas y tooltip en todas las marcas.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from .config import (
    AXIS,
    COLOR_TURNO,
    GRID,
    INK_MUTED,
    INK_PRIMARY,
    INK_SECONDARY,
    META_CUMPLIMIENTO,
    META_SCRAP,
    SEQ_BLUE,
    STATUS,
    SURFACE,
    CATEGORICAL,
    estado_cumplimiento,
)
from .datos import agrupar

VACIA_MSG = "Sin datos para los filtros seleccionados"


def _vacia() -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text=VACIA_MSG, showarrow=False,
                       font=dict(color=INK_MUTED, size=13))
    fig.update_layout(xaxis=dict(visible=False), yaxis=dict(visible=False),
                      height=260)
    return fig


# --------------------------------------------------------------------------
# 1. Producción diaria: fabricado vs. planificado (misma unidad, un solo eje)
# --------------------------------------------------------------------------
def produccion_diaria(df: pd.DataFrame) -> go.Figure:
    d = agrupar(df, "Fecha")
    if d.empty:
        return _vacia()

    fig = go.Figure()
    fig.add_bar(
        x=d["Fecha"], y=d["Fabricado"], name="Fabricado",
        marker=dict(color=CATEGORICAL[0], cornerradius=4,
                    line=dict(width=0)),
        hovertemplate="<b>%{x|%d %b}</b><br>Fabricado: %{y:,.0f} u<extra></extra>",
    )
    fig.add_scatter(
        x=d["Fecha"], y=d["Planificado"], name="Planificado",
        mode="lines", line=dict(color=INK_PRIMARY, width=2, dash="dot"),
        hovertemplate="Planificado: %{y:,.0f} u<extra></extra>",
    )
    fig.update_layout(
        height=300, bargap=0.35, hovermode="x unified",
        yaxis=dict(title=dict(text="unidades", font=dict(size=11, color=INK_MUTED))),
        margin=dict(l=60, r=16, t=28, b=36),
    )
    return fig


# --------------------------------------------------------------------------
# 2. Cumplimiento diario del plan (serie única -> sin leyenda, meta anotada)
# --------------------------------------------------------------------------
def cumplimiento_diario(df: pd.DataFrame) -> go.Figure:
    d = agrupar(df, "Fecha")
    if d.empty:
        return _vacia()

    fig = go.Figure()
    fig.add_hrect(y0=META_CUMPLIMIENTO, y1=max(105, d["Cumplimiento"].max() + 2),
                  fillcolor=STATUS["good"], opacity=0.06, line_width=0, layer="below")
    fig.add_scatter(
        x=d["Fecha"], y=d["Cumplimiento"], mode="lines",
        line=dict(color=CATEGORICAL[0], width=2, shape="spline", smoothing=0.4),
        hovertemplate="<b>%{x|%d %b}</b><br>Cumplimiento: %{y:.1f}%<extra></extra>",
        showlegend=False,
    )
    bajos = d[d["Cumplimiento"] < META_CUMPLIMIENTO]
    if not bajos.empty:
        fig.add_scatter(
            x=bajos["Fecha"], y=bajos["Cumplimiento"], mode="markers",
            marker=dict(color=STATUS["critical"], size=8,
                        line=dict(color=SURFACE, width=2)),
            hovertemplate="<b>%{x|%d %b}</b><br>Bajo meta: %{y:.1f}%<extra></extra>",
            showlegend=False,
        )
    fig.add_hline(y=META_CUMPLIMIENTO, line=dict(color=AXIS, width=1, dash="dash"),
                  annotation_text=f"meta {META_CUMPLIMIENTO:.0f}%",
                  annotation_position="top left",
                  annotation_font=dict(size=11, color=INK_MUTED))
    fig.update_layout(
        height=300,
        yaxis=dict(ticksuffix="%",
                   title=dict(text="cumplimiento", font=dict(size=11, color=INK_MUTED))),
        margin=dict(l=60, r=16, t=28, b=36),
    )
    return fig


# --------------------------------------------------------------------------
# 3. Cumplimiento por línea (semáforo + etiqueta directa)
# --------------------------------------------------------------------------
def cumplimiento_por_linea(df: pd.DataFrame) -> go.Figure:
    d = agrupar(df, "Linea").sort_values("Cumplimiento")
    if d.empty:
        return _vacia()

    # Gráfica de puntos (no de barras): las diferencias entre líneas son de
    # pocos puntos porcentuales y una barra desde 0 las volvería indistinguibles.
    # Al no ser un área, el eje puede no arrancar en cero sin engañar.
    colores = [STATUS[estado_cumplimiento(v)] for v in d["Cumplimiento"]]
    lo = min(d["Cumplimiento"].min(), META_CUMPLIMIENTO) - 2
    hi = max(d["Cumplimiento"].max(), META_CUMPLIMIENTO) + 1

    fig = go.Figure()
    # Conector fino desde el borde izquierdo hasta el punto (referencia visual)
    for _, r in d.iterrows():
        fig.add_shape(type="line", x0=lo, x1=r["Cumplimiento"], y0=r["Linea"], y1=r["Linea"],
                      line=dict(color=GRID, width=2), layer="below")
    fig.add_scatter(
        x=d["Cumplimiento"], y=d["Linea"], mode="markers+text", orientation="h",
        marker=dict(color=colores, size=13, line=dict(color=SURFACE, width=2)),
        text=[f"{v:.1f}%" for v in d["Cumplimiento"]],
        textposition="middle right", textfont=dict(color=INK_SECONDARY, size=11.5),
        cliponaxis=False,
        customdata=d[["Fabricado", "Planificado", "Paro_min"]].to_numpy(),
        hovertemplate=("<b>%{y}</b><br>Cumplimiento: %{x:.1f}%<br>"
                       "Fabricado: %{customdata[0]:,.0f} / %{customdata[1]:,.0f} u<br>"
                       "Paro: %{customdata[2]:,.0f} min<extra></extra>"),
        showlegend=False,
    )
    fig.add_vline(x=META_CUMPLIMIENTO, line=dict(color=INK_PRIMARY, width=1, dash="dash"),
                  annotation_text=f"meta {META_CUMPLIMIENTO:.0f}%",
                  annotation_position="top",
                  annotation_font=dict(size=11, color=INK_MUTED))
    fig.update_layout(
        height=300,
        xaxis=dict(ticksuffix="%", showgrid=True, gridcolor=GRID, range=[lo, hi]),
        yaxis=dict(showgrid=False, tickfont=dict(color=INK_SECONDARY, size=12)),
        margin=dict(l=76, r=32, t=32, b=36),
    )
    return fig


# --------------------------------------------------------------------------
# 4. Mapa de calor Línea x Turno: tasa de defectos (secuencial, un solo tono)
# --------------------------------------------------------------------------
def heatmap_scrap(df: pd.DataFrame) -> go.Figure:
    d = agrupar(df, ["Linea", "Turno"])
    if d.empty:
        return _vacia()

    tabla = d.pivot(index="Linea", columns="Turno", values="Scrap").sort_index(ascending=False)
    fig = go.Figure(go.Heatmap(
        z=tabla.to_numpy(),
        x=[str(c) for c in tabla.columns],
        y=list(tabla.index),
        colorscale=[[i / (len(SEQ_BLUE) - 1), c] for i, c in enumerate(SEQ_BLUE)],
        xgap=2, ygap=2,
        colorbar=dict(title=dict(text="% scrap", font=dict(size=11, color=INK_MUTED)),
                      ticksuffix="%", thickness=10, outlinewidth=0,
                      tickfont=dict(size=10, color=INK_MUTED)),
        hovertemplate="<b>%{y} · %{x}</b><br>Scrap: %{z:.2f}%<extra></extra>",
    ))
    # Etiqueta directa en cada celda: el valor nunca depende solo del color
    for i, linea in enumerate(tabla.index):
        for j, turno in enumerate(tabla.columns):
            v = tabla.iloc[i, j]
            fig.add_annotation(
                x=str(turno), y=linea, text=f"{v:.1f}%", showarrow=False,
                font=dict(size=11, color="#ffffff" if v >= tabla.to_numpy().mean() else INK_PRIMARY),
            )
    fig.update_layout(
        height=300,
        xaxis=dict(showgrid=False, tickfont=dict(color=INK_SECONDARY, size=12), ticks=""),
        yaxis=dict(showgrid=False, tickfont=dict(color=INK_SECONDARY, size=12)),
        margin=dict(l=76, r=16, t=28, b=36),
    )
    return fig


# --------------------------------------------------------------------------
# 5. Tiempo de paro por línea y turno (categórico: identidad del turno)
# --------------------------------------------------------------------------
def paro_por_linea_turno(df: pd.DataFrame) -> go.Figure:
    d = agrupar(df, ["Linea", "Turno"])
    if d.empty:
        return _vacia()

    fig = go.Figure()
    for turno in [t for t in COLOR_TURNO if t in set(d["Turno"].astype(str))]:
        s = d[d["Turno"].astype(str) == turno]
        fig.add_bar(
            x=s["Linea"], y=s["Paro_min"], name=turno,
            marker=dict(color=COLOR_TURNO[turno], cornerradius=4),
            hovertemplate=f"<b>%{{x}} · {turno}</b><br>Paro: %{{y:,.0f}} min<extra></extra>",
        )
    fig.update_layout(
        height=300, barmode="group", bargap=0.3, bargroupgap=0.06,
        yaxis=dict(title=dict(text="minutos de paro", font=dict(size=11, color=INK_MUTED))),
        xaxis=dict(tickfont=dict(color=INK_SECONDARY, size=12)),
        margin=dict(l=64, r=16, t=28, b=36),
    )
    return fig


# --------------------------------------------------------------------------
# 6. Relación paro vs. cumplimiento (dispersión, <= 3 series a todos los pares)
# --------------------------------------------------------------------------
def paro_vs_cumplimiento(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return _vacia()

    fig = go.Figure()
    for turno in [t for t in COLOR_TURNO if t in set(df["Turno"].astype(str))]:
        s = df[df["Turno"].astype(str) == turno]
        fig.add_scatter(
            x=s["Paro_min"], y=s["Cumplimiento"], mode="markers", name=turno,
            marker=dict(color=COLOR_TURNO[turno], size=8, opacity=0.75,
                        line=dict(color=SURFACE, width=2)),
            customdata=s[["Linea"]].to_numpy(),
            hovertemplate=(f"<b>%{{customdata[0]}} · {turno}</b><br>"
                           "Paro: %{x:,.0f} min<br>Cumplimiento: %{y:.1f}%<extra></extra>"),
        )
    fig.add_hline(y=META_CUMPLIMIENTO, line=dict(color=AXIS, width=1, dash="dash"),
                  annotation_text=f"meta {META_CUMPLIMIENTO:.0f}%",
                  annotation_position="bottom left",
                  annotation_font=dict(size=11, color=INK_MUTED))
    fig.update_layout(
        height=300,
        xaxis=dict(title=dict(text="minutos de paro en el turno",
                              font=dict(size=11, color=INK_MUTED))),
        yaxis=dict(ticksuffix="%",
                   title=dict(text="cumplimiento", font=dict(size=11, color=INK_MUTED))),
        margin=dict(l=60, r=16, t=28, b=48),
    )
    return fig
