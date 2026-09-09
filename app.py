"""Dashboard Operativo de Producción — Dash + Plotly.

Público: supervisores de piso. Horizonte: turno / día / semana en curso.
Ejecutar:  python app.py   ->   http://127.0.0.1:8050
"""

from __future__ import annotations

import pandas as pd
from dash import Dash, Input, Output, dcc, html

from src import graficas as gr
from src.componentes import leyenda_metas, panel_alertas, tabla_turno, tarjeta_kpi
from src.config import (
    META_CUMPLIMIENTO,
    META_DISPONIBILIDAD,
    META_OEE,
    META_SCRAP,
    ORDEN_TURNOS,
    estado_cumplimiento,
    estado_disponibilidad,
    estado_oee,
    estado_scrap,
)
from src.datos import alertas, cargar, kpis, periodo_previo, turno_actual

DF = cargar()
LINEAS = sorted(DF["Linea"].unique())
FECHA_MIN, FECHA_MAX = DF["Fecha"].min(), DF["Fecha"].max()

CONFIG_GRAFICA = {"displayModeBar": False, "responsive": True}

app = Dash(__name__, title="Dashboard Operativo · Producción")
server = app.server


# --------------------------------------------------------------------------
# Layout
# --------------------------------------------------------------------------
def bloque(titulo: str, subtitulo: str, hijo) -> html.Div:
    return html.Div([
        html.Div([html.H3(titulo), html.P(subtitulo)], className="bloque-encabezado"),
        hijo,
    ], className="tarjeta")


app.layout = html.Div([
    # ---------------- Encabezado ----------------
    html.Header([
        html.Div([
            html.Div("Planta Norte · Producción", className="eyebrow"),
            html.H1("Dashboard Operativo"),
            html.P("Seguimiento de turno para supervisión de piso · "
                   "cumplimiento del plan, calidad y paros de línea",
                   className="subtitulo"),
        ]),
        html.Div(id="sello-actualizacion", className="sello"),
    ], className="encabezado"),

    # ---------------- Filtros ----------------
    html.Div([
        html.Div([
            html.Label("Periodo", htmlFor="f-fechas"),
            dcc.DatePickerRange(
                id="f-fechas",
                min_date_allowed=FECHA_MIN, max_date_allowed=FECHA_MAX,
                start_date=(FECHA_MAX - pd.Timedelta(days=13)).date(),
                end_date=FECHA_MAX.date(),
                display_format="DD/MM/YYYY", first_day_of_week=1,
            ),
        ], className="filtro"),
        html.Div([
            html.Label("Rango rápido", htmlFor="f-rango"),
            dcc.RadioItems(
                id="f-rango", value=14, className="segmentado",
                options=[{"label": "7 días", "value": 7},
                         {"label": "14 días", "value": 14},
                         {"label": "30 días", "value": 30},
                         {"label": "Todo", "value": 0}],
            ),
        ], className="filtro"),
        html.Div([
            html.Label("Turno", htmlFor="f-turno"),
            dcc.Dropdown(id="f-turno", options=ORDEN_TURNOS, value=ORDEN_TURNOS,
                         multi=True, placeholder="Todos los turnos", clearable=False),
        ], className="filtro ancho"),
        html.Div([
            html.Label("Línea", htmlFor="f-linea"),
            dcc.Dropdown(id="f-linea", options=LINEAS, value=LINEAS,
                         multi=True, placeholder="Todas las líneas", clearable=False),
        ], className="filtro ancho"),
    ], className="barra-filtros"),

    # ---------------- KPIs ----------------
    html.Div(id="fila-kpis", className="grid-kpis"),
    leyenda_metas(),

    # ---------------- Estado actual ----------------
    html.Div([
        html.Div([
            html.Div([html.H3("Alertas activas"),
                      html.P("Ordenadas por severidad · acción inmediata del supervisor")],
                     className="bloque-encabezado"),
            html.Div(id="panel-alertas"),
        ], className="tarjeta"),
        html.Div([
            html.Div([html.H3("Último turno registrado"),
                      html.P(id="subtitulo-turno")], className="bloque-encabezado"),
            html.Div(id="tabla-turno", className="scroll-x"),
        ], className="tarjeta"),
    ], className="grid-2 desigual"),

    # ---------------- Tendencia ----------------
    html.H2("Tendencia del periodo", className="seccion"),
    html.Div([
        bloque("Producción diaria", "Unidades fabricadas frente al plan",
               dcc.Graph(id="g-produccion", config=CONFIG_GRAFICA, style={"height": "300px"})),
        bloque("Cumplimiento del plan", "Porcentaje diario; los puntos marcan días bajo meta",
               dcc.Graph(id="g-cumplimiento", config=CONFIG_GRAFICA, style={"height": "300px"})),
    ], className="grid-2"),

    # ---------------- Detalle ----------------
    html.H2("Desempeño por línea y turno", className="seccion"),
    html.Div([
        bloque("Cumplimiento por línea", "Acumulado del periodo contra la meta",
               dcc.Graph(id="g-lineas", config=CONFIG_GRAFICA, style={"height": "300px"})),
        bloque("Tasa de defectos", "Scrap por línea y turno (valor en cada celda)",
               dcc.Graph(id="g-heatmap", config=CONFIG_GRAFICA, style={"height": "300px"})),
        bloque("Tiempo de paro", "Minutos detenidos acumulados por línea y turno",
               dcc.Graph(id="g-paro", config=CONFIG_GRAFICA, style={"height": "300px"})),
        bloque("Paro vs. cumplimiento", "Cada punto es un turno de una línea",
               dcc.Graph(id="g-dispersion", config=CONFIG_GRAFICA, style={"height": "300px"})),
    ], className="grid-2"),

    html.Footer([
        html.Span("Fuente: produccion.csv · 1 350 registros (90 días × 3 turnos × 5 líneas)"),
        html.Span("Dashboard operativo · Visualización de datos"),
    ], className="pie"),
], className="pagina")


# --------------------------------------------------------------------------
# Callbacks
# --------------------------------------------------------------------------
@app.callback(
    Output("f-fechas", "start_date"),
    Output("f-fechas", "end_date"),
    Input("f-rango", "value"),
    prevent_initial_call=True,
)
def aplicar_rango(dias):
    if not dias:
        return FECHA_MIN.date(), FECHA_MAX.date()
    return (FECHA_MAX - pd.Timedelta(days=dias - 1)).date(), FECHA_MAX.date()


@app.callback(
    Output("fila-kpis", "children"),
    Output("panel-alertas", "children"),
    Output("tabla-turno", "children"),
    Output("subtitulo-turno", "children"),
    Output("sello-actualizacion", "children"),
    Output("g-produccion", "figure"),
    Output("g-cumplimiento", "figure"),
    Output("g-lineas", "figure"),
    Output("g-heatmap", "figure"),
    Output("g-paro", "figure"),
    Output("g-dispersion", "figure"),
    Input("f-fechas", "start_date"),
    Input("f-fechas", "end_date"),
    Input("f-turno", "value"),
    Input("f-linea", "value"),
)
def actualizar(inicio, fin, turnos, lineas):
    turnos = turnos or ORDEN_TURNOS
    lineas = lineas or LINEAS

    d = DF[
        DF["Fecha"].between(pd.to_datetime(inicio), pd.to_datetime(fin))
        & DF["Turno"].isin(turnos)
        & DF["Linea"].isin(lineas)
    ]

    k = kpis(d)
    prev = kpis(periodo_previo(DF, d))

    def delta(campo):
        if not prev.get("Registros"):
            return None
        return k[campo] - prev[campo]

    tarjetas = [
        tarjeta_kpi("Cumplimiento del plan", f"{k['Cumplimiento']:.1f}%",
                    f"meta {META_CUMPLIMIENTO:.0f}%",
                    estado_cumplimiento(k["Cumplimiento"]), delta("Cumplimiento")),
        tarjeta_kpi("Unidades buenas", f"{k['Buenas']:,.0f}",
                    f"de {k['Planificado']:,.0f} planificadas", None,
                    delta("Buenas"), "u"),
        tarjeta_kpi("Tasa de defectos", f"{k['Scrap']:.1f}%",
                    f"meta ≤ {META_SCRAP:.0f}%", estado_scrap(k["Scrap"]),
                    delta("Scrap"), "pp", delta_bueno_arriba=False),
        tarjeta_kpi("Disponibilidad", f"{k['Disponibilidad']:.1f}%",
                    f"meta ≥ {META_DISPONIBILIDAD:.0f}%",
                    estado_disponibilidad(k["Disponibilidad"]), delta("Disponibilidad")),
        tarjeta_kpi("OEE", f"{k['OEE']:.1f}%", f"meta ≥ {META_OEE:.0f}%",
                    estado_oee(k["OEE"]), delta("OEE")),
        tarjeta_kpi("Tiempo de paro", f"{k['Paro_min']:,.0f} min",
                    f"{k['Registros']:,.0f} turnos-línea", None,
                    delta("Paro_min"), "min", delta_bueno_arriba=False),
    ]

    actual = turno_actual(d)
    if actual.empty:
        sub_turno, sello = "Sin datos en el filtro", "Sin datos"
    else:
        f = actual.iloc[0]
        sub_turno = f"{f['Fecha']:%d/%m/%Y} · turno {f['Turno']} · {len(actual)} líneas"
        sello = f"Último dato: {f['Fecha']:%d/%m/%Y} · turno {f['Turno']}"

    return (
        tarjetas,
        panel_alertas(alertas(d)),
        tabla_turno(actual),
        sub_turno,
        sello,
        gr.produccion_diaria(d),
        gr.cumplimiento_diario(d),
        gr.cumplimiento_por_linea(d),
        gr.heatmap_scrap(d),
        gr.paro_por_linea_turno(d),
        gr.paro_vs_cumplimiento(d),
    )


if __name__ == "__main__":
    app.run(debug=True, port=8050)
