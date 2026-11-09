"""Generar figuras y capturas automaticamente desde el proyecto.

python docs/generate_evidence.py
python docs/generate_evidence.py --solo-figuras
python docs/generate_evidence.py --solo-capturas
"""
from __future__ import annotations
import argparse
from generate_figures import write_figures
from generate_captures import run_captures

def main():
    p=argparse.ArgumentParser(description='Reproducir evidencias de PresupuestoBot')
    group=p.add_mutually_exclusive_group()
    group.add_argument('--solo-figuras',action='store_true')
    group.add_argument('--solo-capturas',action='store_true')
    args=p.parse_args()
    if not args.solo_capturas:
        print('Generando figuras desde resultados guardados...')
        for f in write_figures():print('GENERADA:',f)
    if not args.solo_figuras:
        print('Iniciando Streamlit y navegador automatico para capturas...')
        for f in run_captures():print('CAPTURA REAL:',f)
    print('Evidencias disponibles en docs/figuras y docs/capturas')

if __name__=='__main__':main()
