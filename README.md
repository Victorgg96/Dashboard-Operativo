# Dashboard Operativo de Producción

Dashboard de **nivel operativo** (supervisores de piso, horizonte de turno/día)
construido con **Python + Dash + Plotly**, con diseño propio en CSS.

## Cómo ejecutarlo

En Windows (PowerShell o Git Bash), dentro de esta carpeta:

```bash
python -m venv .venv
.venv\Scripts\activate          # Git Bash:  source .venv/Scripts/activate
pip install -r requirements.txt
python app.py
```

Abrir <http://127.0.0.1:8050> en el navegador.
Atajo: doble clic en `ejecutar.bat` (crea el entorno la primera vez).

Para volver a generar las capturas del reporte, con la app corriendo:

```bash
pip install playwright && playwright install chromium
python scripts/capturas.py
```

## Estructura

```
dashboard_datos/
├── app.py                  layout + callbacks de Dash
├── src/
│   ├── config.py           metas operativas, paleta y plantilla de Plotly
│   ├── datos.py            carga del CSV, KPIs, agregaciones y alertas
│   ├── graficas.py         las seis figuras de Plotly
│   └── componentes.py      tarjetas KPI, panel de alertas, tabla del turno
├── assets/styles.css       diseño (Dash carga /assets automáticamente)
├── data/produccion.csv     fuente de datos
├── scripts/capturas.py     capturas de pantalla con Playwright
├── screenshots/            imágenes para el reporte
└── reporte/                entregable escrito
```

## Indicadores implementados

| KPI | Fórmula | Meta |
|---|---|---|
| Cumplimiento del plan | Fabricado / Planificado | ≥ 95 % |
| Unidades buenas | Fabricado − Defectuosos | — |
| Tasa de defectos (scrap) | Defectuosos / Fabricado | ≤ 3 % |
| Disponibilidad | (480 − Paro) / 480 por turno | ≥ 90 % |
| Calidad | 1 − scrap | — |
| OEE | Disponibilidad × Rendimiento × Calidad | ≥ 85 % |
| Tiempo de paro | Suma de TiempoParada_min | ≤ 45 min/turno |

Cada KPI compara contra el **periodo inmediato anterior de igual duración** y se
colorea con semáforo (en meta / atención / riesgo / crítico).

## Criterios de diseño

- Un solo eje por gráfica: nunca doble escala.
- Color asignado por función: categórico (turno), secuencial de un solo tono
  (scrap) y estado reservado para el semáforo, siempre con ícono + etiqueta.
- El cumplimiento por línea se muestra como gráfica de puntos, no de barras:
  las diferencias son de décimas y una barra desde cero las ocultaría.
- Etiquetas directas en el mapa de calor y en la tabla: ningún valor depende
  únicamente del color.
