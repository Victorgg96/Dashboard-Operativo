"""Componentes de UI: tarjetas KPI, panel de alertas y tabla del turno actual."""

from __future__ import annotations

import pandas as pd
from dash import html

from .config import (
    ETIQUETA_ESTADO,
    ICONO_ESTADO,
    MAX_PARO_TURNO,
    META_CUMPLIMIENTO,
    META_SCRAP,
    STATUS,
    estado_cumplimiento,
    estado_scrap,
)


def tarjeta_kpi(titulo: str, valor: str, meta: str, estado: str | None = None,
                delta: float | None = None, sufijo_delta: str = "pp",
                delta_bueno_arriba: bool = True) -> html.Div:
    """Tarjeta de KPI: valor destacado + meta + variación vs. periodo previo."""
    hijos = [
        html.Div(titulo, className="kpi-titulo"),
        html.Div(valor, className="kpi-valor"),
    ]

    pie = []
    if delta is not None:
        mejora = (delta >= 0) if delta_bueno_arriba else (delta <= 0)
        flecha = "▲" if delta > 0 else ("▼" if delta < 0 else "■")
        clase = "kpi-delta bueno" if mejora else "kpi-delta malo"
        fmt = ",.1f" if sufijo_delta == "pp" else ",.0f"
        pie.append(html.Span(f"{flecha} {abs(delta):{fmt}} {sufijo_delta}", className=clase))
    pie.append(html.Span(meta, className="kpi-meta"))
    hijos.append(html.Div(pie, className="kpi-pie"))

    borde = STATUS[estado] if estado else "transparent"
    return html.Div(hijos, className="kpi", style={"borderTopColor": borde})


def panel_alertas(avisos: list[dict]) -> html.Div:
    """Lista de alertas ordenadas por severidad. Ícono + etiqueta, nunca color solo."""
    if not avisos:
        return html.Div(
            [html.Div("●", className="alerta-icono", style={"color": STATUS["good"]}),
             html.Div([html.Div("Sin desviaciones", className="alerta-titulo"),
                       html.Div("Todas las líneas dentro de meta en el periodo filtrado.",
                                className="alerta-detalle")])],
            className="alerta",
        )

    filas = []
    for a in avisos:
        color = STATUS[a["estado"]]
        filas.append(html.Div([
            html.Div(ICONO_ESTADO[a["estado"]], className="alerta-icono",
                     style={"color": color}),
            html.Div([
                html.Div([
                    html.Span(a["titulo"], className="alerta-titulo"),
                    html.Span(ETIQUETA_ESTADO[a["estado"]], className="chip",
                              style={"color": color, "borderColor": color}),
                ], className="alerta-encabezado"),
                html.Div(a["detalle"], className="alerta-detalle"),
            ]),
        ], className="alerta"))
    return html.Div(filas)


def tabla_turno(df_turno: pd.DataFrame) -> html.Table:
    """Detalle línea por línea del último turno, con formato condicional."""
    columnas = ["Línea", "Plan", "Fabricado", "Buenas", "Scrap", "Paro", "Cumplimiento", "Estado"]
    if df_turno.empty:
        return html.Table([html.Tbody([html.Tr([html.Td("Sin datos", colSpan=len(columnas))])])],
                          className="tabla")

    severidad = ["good", "warning", "serious", "critical"]

    filas = []
    for _, r in df_turno.sort_values("Cumplimiento").iterrows():
        est_c = estado_cumplimiento(r["Cumplimiento"])
        est_s = estado_scrap(r["Scrap"])
        est_p = "serious" if r["Paro_min"] > MAX_PARO_TURNO else "good"
        # El estado de la línea es la peor de sus tres condiciones
        est = max([est_c, est_s, est_p], key=severidad.index)
        filas.append(html.Tr([
            html.Td(r["Linea"], className="celda-etiqueta"),
            html.Td(f"{int(r['Planificado']):,}", className="num"),
            html.Td(f"{int(r['Fabricado']):,}", className="num"),
            html.Td(f"{int(r['Buenas']):,}", className="num"),
            html.Td(f"{r['Scrap']:.1f}%", className="num",
                    style={"color": STATUS[est_s] if est_s != "good" else None,
                           "fontWeight": 600 if est_s != "good" else 400}),
            html.Td(f"{int(r['Paro_min'])} min", className="num",
                    style={"color": STATUS["serious"] if r["Paro_min"] > MAX_PARO_TURNO else None,
                           "fontWeight": 600 if r["Paro_min"] > MAX_PARO_TURNO else 400}),
            html.Td(f"{r['Cumplimiento']:.1f}%", className="num",
                    style={"color": STATUS[est_c], "fontWeight": 600}),
            html.Td(html.Span(f"{ICONO_ESTADO[est]} {ETIQUETA_ESTADO[est]}",
                              className="chip",
                              style={"color": STATUS[est], "borderColor": STATUS[est]})),
        ]))

    t_plan = int(df_turno["Planificado"].sum())
    t_fab = int(df_turno["Fabricado"].sum())
    t_def = int(df_turno["Defectuosos"].sum())
    t_paro = int(df_turno["Paro_min"].sum())
    total = html.Tr([
        html.Td("Total turno", className="celda-etiqueta"),
        html.Td(f"{t_plan:,}", className="num"),
        html.Td(f"{t_fab:,}", className="num"),
        html.Td(f"{t_fab - t_def:,}", className="num"),
        html.Td(f"{t_def / t_fab * 100:.1f}%" if t_fab else "—", className="num"),
        html.Td(f"{t_paro:,} min", className="num"),
        html.Td(f"{t_fab / t_plan * 100:.1f}%" if t_plan else "—", className="num"),
        html.Td(""),
    ], className="fila-total")

    return html.Table([
        html.Thead(html.Tr([html.Th(c, className="num" if c not in ("Línea", "Estado") else "")
                            for c in columnas])),
        html.Tbody(filas),
        html.Tfoot(total),
    ], className="tabla")


def leyenda_metas() -> html.Div:
    return html.Div([
        html.Span("Metas operativas:", className="leyenda-titulo"),
        html.Span(f"cumplimiento ≥ {META_CUMPLIMIENTO:.0f}%", className="leyenda-item"),
        html.Span(f"scrap ≤ {META_SCRAP:.0f}%", className="leyenda-item"),
        html.Span(f"paro ≤ {MAX_PARO_TURNO} min/turno", className="leyenda-item"),
    ], className="leyenda")
