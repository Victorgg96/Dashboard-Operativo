"""Carga del CSV y cálculo de los indicadores operativos."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import (
    MAX_PARO_TURNO,
    META_CUMPLIMIENTO,
    META_DISPONIBILIDAD,
    META_SCRAP,
    MINUTOS_POR_TURNO,
    ORDEN_TURNOS,
    estado_cumplimiento,
    estado_disponibilidad,
    estado_scrap,
    estado_oee,
)

RUTA_CSV = Path(__file__).resolve().parents[1] / "data" / "produccion.csv"


def cargar(ruta: Path | str = RUTA_CSV) -> pd.DataFrame:
    """Lee produccion.csv y agrega las columnas derivadas por registro."""
    df = pd.read_csv(ruta, encoding="latin-1")
    df.columns = [c.strip() for c in df.columns]
    df = df.rename(columns={"Máquina": "Linea", "Maquina": "Linea",
                            "TiempoParada_min": "Paro_min"})

    df["Fecha"] = pd.to_datetime(df["Fecha"])
    df["Turno"] = pd.Categorical(df["Turno"], categories=ORDEN_TURNOS, ordered=True)
    df = df.sort_values(["Fecha", "Turno", "Linea"]).reset_index(drop=True)

    df["Buenas"] = df["Fabricado"] - df["Defectuosos"]
    df["Cumplimiento"] = df["Fabricado"] / df["Planificado"] * 100
    df["Scrap"] = df["Defectuosos"] / df["Fabricado"].replace(0, pd.NA) * 100
    df["Disponibilidad"] = (MINUTOS_POR_TURNO - df["Paro_min"]) / MINUTOS_POR_TURNO * 100
    df["Calidad"] = df["Buenas"] / df["Fabricado"].replace(0, pd.NA) * 100
    df["OEE"] = df["Disponibilidad"] * df["Cumplimiento"] / 100 * df["Calidad"] / 100
    df["Semana"] = df["Fecha"].dt.isocalendar().week.astype(int)
    return df


# --------------------------------------------------------------------------
# Agregaciones
# --------------------------------------------------------------------------
def _resumen(g: pd.DataFrame) -> pd.Series:
    plan = g["Planificado"].sum()
    fab = g["Fabricado"].sum()
    defe = g["Defectuosos"].sum()
    paro = g["Paro_min"].sum()
    turnos = len(g)
    disponible = turnos * MINUTOS_POR_TURNO

    cumplimiento = fab / plan * 100 if plan else 0.0
    scrap = defe / fab * 100 if fab else 0.0
    disponibilidad = (disponible - paro) / disponible * 100 if disponible else 0.0
    calidad = 100 - scrap
    return pd.Series({
        "Planificado": plan,
        "Fabricado": fab,
        "Defectuosos": defe,
        "Buenas": fab - defe,
        "Paro_min": paro,
        "Registros": turnos,
        "Cumplimiento": cumplimiento,
        "Scrap": scrap,
        "Disponibilidad": disponibilidad,
        "Calidad": calidad,
        "OEE": disponibilidad * cumplimiento * calidad / 10_000,
    })


def kpis(df: pd.DataFrame) -> dict:
    """Indicadores globales del subconjunto filtrado."""
    if df.empty:
        return {k: 0 for k in ("Planificado", "Fabricado", "Defectuosos", "Buenas",
                               "Paro_min", "Registros", "Cumplimiento", "Scrap",
                               "Disponibilidad", "Calidad", "OEE")}
    return _resumen(df).to_dict()


def agrupar(df: pd.DataFrame, por: str | list[str]) -> pd.DataFrame:
    """Resumen por una o varias dimensiones (Fecha, Turno, Linea...)."""
    if df.empty:
        return pd.DataFrame()
    llaves = [por] if isinstance(por, str) else list(por)
    out = (df.groupby(llaves, observed=True)
             .agg(Planificado=("Planificado", "sum"),
                  Fabricado=("Fabricado", "sum"),
                  Defectuosos=("Defectuosos", "sum"),
                  Paro_min=("Paro_min", "sum"),
                  Registros=("Fabricado", "size"))
             .reset_index())

    disponible = out["Registros"] * MINUTOS_POR_TURNO
    out["Buenas"] = out["Fabricado"] - out["Defectuosos"]
    out["Cumplimiento"] = out["Fabricado"] / out["Planificado"] * 100
    out["Scrap"] = out["Defectuosos"] / out["Fabricado"] * 100
    out["Disponibilidad"] = (disponible - out["Paro_min"]) / disponible * 100
    out["Calidad"] = 100 - out["Scrap"]
    out["OEE"] = out["Disponibilidad"] * out["Cumplimiento"] * out["Calidad"] / 10_000
    return out


def turno_actual(df: pd.DataFrame) -> pd.DataFrame:
    """Último (Fecha, Turno) presente en los datos: la vista de 'ahora mismo'."""
    if df.empty:
        return df
    ultimo = df.sort_values(["Fecha", "Turno"]).iloc[-1]
    return df[(df["Fecha"] == ultimo["Fecha"]) & (df["Turno"] == ultimo["Turno"])].copy()


def periodo_previo(df_total: pd.DataFrame, df_filtrado: pd.DataFrame) -> pd.DataFrame:
    """Mismo número de días inmediatamente anteriores, para calcular la variación."""
    if df_filtrado.empty:
        return df_filtrado
    ini, fin = df_filtrado["Fecha"].min(), df_filtrado["Fecha"].max()
    dias = (fin - ini).days + 1
    prev_fin = ini - pd.Timedelta(days=1)
    prev_ini = prev_fin - pd.Timedelta(days=dias - 1)
    mask = df_total["Fecha"].between(prev_ini, prev_fin)
    mask &= df_total["Turno"].isin(df_filtrado["Turno"].unique())
    mask &= df_total["Linea"].isin(df_filtrado["Linea"].unique())
    return df_total[mask]


# --------------------------------------------------------------------------
# Alertas: el corazón operativo (corto plazo, accionable)
# --------------------------------------------------------------------------
def alertas(df: pd.DataFrame, limite: int = 6) -> list[dict]:
    """Genera alertas del último turno + desviaciones del periodo filtrado."""
    if df.empty:
        return []

    avisos: list[dict] = []
    actual = turno_actual(df)
    etiqueta_turno = ""
    if not actual.empty:
        fila = actual.iloc[0]
        etiqueta_turno = f"{fila['Fecha']:%d/%m} · turno {fila['Turno']}"

    # 1. Desviaciones del último turno, línea por línea
    for _, r in actual.sort_values("Cumplimiento").iterrows():
        if r["Cumplimiento"] < META_CUMPLIMIENTO:
            avisos.append({
                "estado": estado_cumplimiento(r["Cumplimiento"]),
                "titulo": f"{r['Linea']} bajo plan",
                "detalle": (f"{r['Cumplimiento']:.1f}% de cumplimiento "
                            f"({int(r['Fabricado'])}/{int(r['Planificado'])} u) · {etiqueta_turno}"),
                "orden": META_CUMPLIMIENTO - r["Cumplimiento"],
            })
        if r["Paro_min"] > MAX_PARO_TURNO:
            avisos.append({
                "estado": "critical" if r["Paro_min"] > MAX_PARO_TURNO + 10 else "serious",
                "titulo": f"Paro prolongado en {r['Linea']}",
                "detalle": (f"{int(r['Paro_min'])} min detenida "
                            f"(umbral {MAX_PARO_TURNO} min) · {etiqueta_turno}"),
                "orden": r["Paro_min"],
            })
        if r["Scrap"] > META_SCRAP:
            avisos.append({
                "estado": estado_scrap(r["Scrap"]),
                "titulo": f"Scrap alto en {r['Linea']}",
                "detalle": (f"{r['Scrap']:.1f}% de defectuosos "
                            f"({int(r['Defectuosos'])} u) · {etiqueta_turno}"),
                "orden": r["Scrap"],
            })

    # 2. Línea con peor desempeño acumulado en el periodo
    por_linea = agrupar(df, "Linea")
    if not por_linea.empty:
        peor = por_linea.sort_values("Cumplimiento").iloc[0]
        if peor["Cumplimiento"] < META_CUMPLIMIENTO:
            avisos.append({
                "estado": estado_cumplimiento(peor["Cumplimiento"]),
                "titulo": f"{peor['Linea']}: peor cumplimiento del periodo",
                "detalle": (f"{peor['Cumplimiento']:.1f}% acumulado · "
                            f"{int(peor['Paro_min'])} min de paro"),
                "orden": 0.5,
            })

    # 3. Turno con menor disponibilidad
    por_turno = agrupar(df, "Turno")
    if not por_turno.empty:
        peor_t = por_turno.sort_values("Disponibilidad").iloc[0]
        if peor_t["Disponibilidad"] < META_DISPONIBILIDAD:
            avisos.append({
                "estado": estado_disponibilidad(peor_t["Disponibilidad"]),
                "titulo": f"Turno {peor_t['Turno']}: menor disponibilidad",
                "detalle": (f"{peor_t['Disponibilidad']:.1f}% de disponibilidad · "
                            f"{int(peor_t['Paro_min'])} min de paro acumulado"),
                "orden": 0.4,
            })

    prioridad = {"critical": 0, "serious": 1, "warning": 2, "good": 3}
    avisos.sort(key=lambda a: (prioridad[a["estado"]], -a["orden"]))
    return avisos[:limite]
