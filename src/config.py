"""Configuración central: metas operativas, paleta y plantilla de Plotly.

La paleta sigue el método de la guía de visualización:
color asignado por función (categórico / secuencial / estado), nunca por gusto.
"""

from __future__ import annotations

import plotly.graph_objects as go
import plotly.io as pio

# --------------------------------------------------------------------------
# Parámetros del proceso
# --------------------------------------------------------------------------
MINUTOS_POR_TURNO = 480          # 8 h por turno
ORDEN_TURNOS = ["Mañana", "Tarde", "Noche"]

# Metas operativas (umbrales de semáforo)
META_CUMPLIMIENTO = 95.0         # % del plan
META_SCRAP = 3.0                 # % máximo de defectuosos
META_DISPONIBILIDAD = 90.0       # % del tiempo de turno
META_OEE = 85.0                  # %
MAX_PARO_TURNO = 45              # min, umbral de alerta por turno

# --------------------------------------------------------------------------
# Superficies y tinta
# --------------------------------------------------------------------------
SURFACE = "#fcfcfb"              # superficie de las gráficas
PLANE = "#f9f9f7"                # plano de la página
INK_PRIMARY = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
BORDER = "rgba(11,11,11,0.10)"

# --------------------------------------------------------------------------
# Categórico: orden fijo de slots (nunca se cicla ni se reordena por ranking)
# --------------------------------------------------------------------------
CATEGORICAL = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]

# Turnos: identidad estable en todo el dashboard (slots 1-3, seguros a todos los pares)
COLOR_TURNO = {
    "Mañana": CATEGORICAL[0],
    "Tarde": CATEGORICAL[1],
    "Noche": CATEGORICAL[2],
}

# Secuencial: un solo tono, claro -> oscuro (magnitud continua)
SEQ_BLUE = [
    "#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec",
    "#5598e7", "#3987e5", "#2a78d6", "#256abf", "#1c5cab",
]

# Estado: reservado, nunca se usa como "serie 4"
STATUS = {
    "good": "#0ca30c",
    "warning": "#fab219",
    "serious": "#ec835a",
    "critical": "#d03b3b",
}
ICONO_ESTADO = {"good": "●", "warning": "▲", "serious": "▲", "critical": "■"}
ETIQUETA_ESTADO = {
    "good": "En meta",
    "warning": "Atención",
    "serious": "Riesgo",
    "critical": "Crítico",
}

FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'


def _plantilla() -> go.layout.Template:
    """Plantilla común: cuadrícula discreta, sin ruido, tinta de texto."""
    return go.layout.Template(
        layout=go.Layout(
            font=dict(family=FONT, size=12, color=INK_SECONDARY),
            paper_bgcolor=SURFACE,
            plot_bgcolor=SURFACE,
            colorway=CATEGORICAL,
            margin=dict(l=56, r=20, t=16, b=40),
            hoverlabel=dict(
                bgcolor="#ffffff",
                bordercolor=AXIS,
                font=dict(family=FONT, size=12, color=INK_PRIMARY),
            ),
            xaxis=dict(
                showgrid=False,
                zeroline=False,
                linecolor=AXIS,
                ticks="outside",
                tickcolor=AXIS,
                ticklen=4,
                tickfont=dict(color=INK_MUTED, size=11),
            ),
            yaxis=dict(
                gridcolor=GRID,
                gridwidth=1,
                zeroline=False,
                showline=False,
                ticks="",
                tickfont=dict(color=INK_MUTED, size=11),
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                x=0,
                font=dict(color=INK_SECONDARY, size=11),
                itemsizing="constant",
            ),
        )
    )


pio.templates["operativo"] = _plantilla()
pio.templates.default = "operativo"


def estado_cumplimiento(valor: float) -> str:
    if valor >= META_CUMPLIMIENTO:
        return "good"
    if valor >= META_CUMPLIMIENTO - 5:
        return "warning"
    if valor >= META_CUMPLIMIENTO - 10:
        return "serious"
    return "critical"


def estado_scrap(valor: float) -> str:
    if valor <= META_SCRAP:
        return "good"
    if valor <= META_SCRAP + 1.5:
        return "warning"
    if valor <= META_SCRAP + 3:
        return "serious"
    return "critical"


def estado_disponibilidad(valor: float) -> str:
    if valor >= META_DISPONIBILIDAD:
        return "good"
    if valor >= META_DISPONIBILIDAD - 5:
        return "warning"
    if valor >= META_DISPONIBILIDAD - 10:
        return "serious"
    return "critical"


def estado_oee(valor: float) -> str:
    if valor >= META_OEE:
        return "good"
    if valor >= META_OEE - 5:
        return "warning"
    if valor >= META_OEE - 12:
        return "serious"
    return "critical"
