"""R10: captura o painel (Streamlit) em PNG para docs/evidencias/R10/. Requer Playwright (`pip install playwright && playwright install chromium`).

Uso (a partir da pasta do projeto, depois de `python -m dengue_mg.pipeline`):
    PYTHONPATH=src python scripts/capturar_painel.py
"""
import os
import subprocess
import sys
import time
import urllib.request

PORTA = 8599
SAIDA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "evidencias", "R10")


def main():
    from playwright.sync_api import sync_playwright
    os.makedirs(SAIDA, exist_ok=True)
    proc = subprocess.Popen([sys.executable, "-m", "streamlit", "run", "app/painel.py", "--server.port", str(PORTA), "--server.headless", "true"])
    try:
        for _ in range(60):
            try:
                urllib.request.urlopen("http://localhost:%d/_stcore/health" % PORTA, timeout=2)
                break
            except OSError:
                time.sleep(1)
        with sync_playwright() as p:
            nav = p.chromium.launch()
            pg = nav.new_page(viewport={"width": 1400, "height": 1000}, device_scale_factor=2)
            pg.goto("http://localhost:%d" % PORTA)
            pg.wait_for_selector("text=Pressão da dengue", timeout=60000)
            time.sleep(4)  # gráficos
            pg.screenshot(path=os.path.join(SAIDA, "painel_estado.png"), full_page=True)
            nav.close()
        print("Captura em", SAIDA)
    finally:
        proc.terminate()


if __name__ == "__main__":
    main()
