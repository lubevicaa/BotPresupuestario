"""Genera capturas REALES del chatbot web mediante Playwright+Chromium.

Ejecuta Streamlit temporalmente; no altera datos, codigo, ni el modelo.
Requiere: pip install playwright y python -m playwright install chromium.
"""
from __future__ import annotations
import os, shutil, socket, subprocess, sys, time
from pathlib import Path
from urllib.request import urlopen
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs'/'capturas'

def free_port():
    with socket.socket() as s:
        s.bind(('127.0.0.1',0))
        return s.getsockname()[1]

def run_captures():
    try:from playwright.sync_api import sync_playwright
    except ImportError as e:raise RuntimeError('Falta Playwright: python -m pip install playwright') from e
    OUT.mkdir(parents=True,exist_ok=True)
    port=free_port();address=f'http://127.0.0.1:{port}'
    cmd=[sys.executable,'-m','streamlit','run',str(ROOT/'app.py'),'--server.headless=true',
         f'--server.port={port}','--server.address=127.0.0.1','--browser.gatherUsageStats=false']
    logfile=OUT/'servidor_capturas.log'
    with logfile.open('w',encoding='utf-8') as log:
        server=subprocess.Popen(cmd,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
        try:
            deadline=time.monotonic()+90
            while time.monotonic()<deadline:
                if server.poll() is not None:
                    raise RuntimeError(f'Streamlit no inicio. Revisar {logfile}')
                try:
                    with urlopen(address+'/_stcore/health',timeout=2) as r:
                        if r.status==200:break
                except Exception:time.sleep(.5)
            else:raise RuntimeError(f'Streamlit no respondio en 90 segundos. Revisar {logfile}')
            with sync_playwright() as p:
                # Windows: playwright instala su propio Chromium. Linux: opcional Chromium de sistema.
                opts={'headless':True}
                if sys.platform.startswith('linux') and shutil.which('chromium'):
                    opts['executable_path']=shutil.which('chromium')
                browser=p.chromium.launch(**opts)
                page=browser.new_page(viewport={'width':1500,'height':980},device_scale_factor=1)
                page.goto(address,wait_until='domcontentloaded',timeout=60000)
                page.get_by_text('PresupuestoBot EC').first.wait_for(timeout=60000)
                def ask(q):
                    inp=page.locator('[data-testid="stChatInput"] textarea')
                    inp.wait_for(timeout=45000)
                    n=page.locator('[data-testid="stChatMessage"]').count()
                    inp.fill(q)
                    inp.press('Enter')
                    page.wait_for_function('(old)=>document.querySelectorAll("[data-testid=stChatMessage]").length>=old+2',arg=n,timeout=60000)
                    page.wait_for_timeout(850)
                ask('¿Cuál es el presupuesto anual total de la empresa?')
                ask('¿Cuánto hemos gastado en capacitación hasta octubre?')
                page.screenshot(path=str(OUT/'01_consultas_basicas.png'),full_page=True)
                page.reload(wait_until='domcontentloaded')
                page.locator('[data-testid="stChatInput"] textarea').wait_for(timeout=60000)
                ask('¿Qué partida tiene mayor riesgo?')
                page.screenshot(path=str(OUT/'02_riesgo_bayesiano.png'),full_page=True)
                page.reload(wait_until='domcontentloaded')
                page.locator('[data-testid="stChatInput"] textarea').wait_for(timeout=60000)
                ask('¿Cuánto presupuesto tiene asignado capacitación?')
                ask('¿Qué porcentaje representa?')
                ask('¿Cuál es su riesgo?')
                page.screenshot(path=str(OUT/'03_contexto_conversacional.png'),full_page=True)
                browser.close()
        finally:
            server.terminate()
            try:server.wait(timeout=8)
            except subprocess.TimeoutExpired:server.kill();server.wait()
    return [str(x.relative_to(ROOT)) for x in sorted(OUT.glob('*.png'))]

if __name__=='__main__':
    for path in run_captures():print('CAPTURA REAL:',path)
