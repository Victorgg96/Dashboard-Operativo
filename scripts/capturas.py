"""Toma las capturas del dashboard en ejecución (para el reporte).

Uso:  1) python app.py       2) python scripts/capturas.py
"""

from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8050/"
SALIDA = Path(__file__).resolve().parents[1] / "screenshots"
SALIDA.mkdir(exist_ok=True)


def main() -> None:
    with sync_playwright() as p:
        nav = p.chromium.launch()
        pag = nav.new_page(viewport={"width": 1600, "height": 1000},
                           device_scale_factor=2)
        pag.goto(URL, wait_until="networkidle")
        pag.wait_for_timeout(3500)

        pag.screenshot(path=SALIDA / "02_vista_superior.png")

        # Plotly redimensiona sus gráficas al viewport: para la captura completa
        # agrandamos el viewport en lugar de usar full_page (que las colapsa).
        alto = pag.evaluate("document.querySelector('.pagina').scrollHeight")
        pag.set_viewport_size({"width": 1600, "height": int(alto) + 40})
        pag.wait_for_timeout(2500)
        pag.screenshot(path=SALIDA / "01_dashboard_completo.png")
        pag.set_viewport_size({"width": 1600, "height": 1000})
        pag.wait_for_timeout(1500)

        for nombre, selector in [
            ("03_kpis", ".grid-kpis"),
            ("04_alertas_y_turno", ".grid-2.desigual"),
            ("05_tendencia", ".grid-2:not(.desigual)"),
        ]:
            el = pag.query_selector(selector)
            if el:
                el.screenshot(path=SALIDA / f"{nombre}.png")

        # Bloque de gráficas por línea y turno
        el = pag.query_selector_all(".grid-2:not(.desigual)")
        if len(el) > 1:
            el[1].scroll_into_view_if_needed()
            pag.wait_for_timeout(1200)
            el[1].screenshot(path=SALIDA / "06_detalle.png")
        nav.close()
    print(f"Capturas guardadas en {SALIDA}")


if __name__ == "__main__":
    main()
