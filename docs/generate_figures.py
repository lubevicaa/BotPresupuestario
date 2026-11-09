"""Regenera figuras verificables desde resultados/metricas_nlp.json.

Ejecutar desde cualquier carpeta: python docs/generate_figures.py
No reentrena ni modifica metricas. Falla con mensaje si faltan archivos.
"""
from __future__ import annotations
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'resultados' / 'metricas_nlp.json'
OUT = ROOT / 'docs' / 'figuras'

def write_figures():
    if not SOURCE.exists():
        raise FileNotFoundError(f'No se encontraron las metricas: {SOURCE}')
    m = json.loads(SOURCE.read_text(encoding='utf-8'))
    labels = m['confusion_matrix_test']['labels']
    matrix = m['confusion_matrix_test']['matrix']
    OUT.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(12, 10))
    ax.imshow(matrix, cmap='Blues')
    ax.set(xticks=range(len(labels)),yticks=range(len(labels)),xticklabels=labels,yticklabels=labels,
           xlabel='Intencion predicha',ylabel='Intencion real',title='Matriz de confusion - prueba NLP (52 frases)')
    plt.setp(ax.get_xticklabels(),rotation=65,ha='right',fontsize=8)
    plt.setp(ax.get_yticklabels(),fontsize=8)
    for i,row in enumerate(matrix):
        for j,n in enumerate(row):
            if n: ax.text(j,i,str(n),ha='center',va='center',fontsize=8)
    fig.tight_layout();fig.savefig(OUT/'matriz_confusion.png',dpi=180);plt.close(fig)

    rep=m['classification_report_test']
    vals=[rep[l]['f1-score'] for l in labels]
    fig,ax=plt.subplots(figsize=(12,5));ax.bar(range(len(labels)),vals)
    ax.set(xticks=range(len(labels)),xticklabels=labels,ylim=(0,1.05),ylabel='F1',title='F1 por intencion (conjunto de prueba)')
    plt.setp(ax.get_xticklabels(),rotation=60,ha='right',fontsize=8)
    fig.tight_layout();fig.savefig(OUT/'f1_por_intencion.png',dpi=180);plt.close(fig)

    hist=m.get('history',[])
    if not hist:
        raise ValueError('El archivo de metricas no contiene historial de entrenamiento')
    fig,ax=plt.subplots(figsize=(9,5));ax.plot([r['epoch'] for r in hist],[r['train_loss'] for r in hist],label='Entrenamiento')
    ax.plot([r['epoch'] for r in hist],[r['val_loss'] for r in hist],label='Validacion')
    ax.set(xlabel='Epoca',ylabel='Perdida',title='Curva de perdida del modelo NLP (Fase 3)')
    ax.legend();fig.tight_layout();fig.savefig(OUT/'curva_entrenamiento.png',dpi=180);plt.close(fig)

    def diagram(name,title,items,footnote):
        fig,ax=plt.subplots(figsize=(11,7));ax.set_xlim(0,10);ax.set_ylim(0,10);ax.axis('off')
        ax.set_title(title,fontsize=16,pad=15)
        ys=[8.1,6.45,4.8,3.15,1.5]
        for idx,(item,y) in enumerate(zip(items,ys)):
            ax.add_patch(FancyBboxPatch((1.4,y),7.2,1.05,boxstyle='round,pad=0.12',facecolor='#e7f0f7',edgecolor='#496b83'))
            ax.text(5,y+.525,item,ha='center',va='center',fontsize=11)
            if idx<4:
                ax.add_patch(FancyArrowPatch((5,y-.02),(5,ys[idx+1]+1.16),arrowstyle='->',mutation_scale=13,lw=1.4))
        fig.text(.5,.03,footnote,ha='center',fontsize=9,color='#555555')
        fig.tight_layout(rect=(0,.06,1,1));fig.savefig(OUT/name,dpi=180);plt.close(fig)

    diagram('arquitectura.png','Arquitectura funcional de PresupuestoBot',[
        'Usuario / Streamlit o CLI',
        'Clasificador NLP: embeddings + TF-IDF + MLP',
        'Gestor de dialogo: contexto, aclaraciones y consultas',
        'Base presupuestaria + reglas + razonamiento bayesiano',
        'Respuesta + indicador financiero + advertencia',
    ], 'Diagrama conceptual de los modulos reales; no representa el flujo de llamadas exacto.')
    # Red bayesiana: tres evidencias paralelas sobre un nodo de riesgo, NO cadena secuencial.
    fig,ax=plt.subplots(figsize=(10,6));ax.set_xlim(0,10);ax.set_ylim(0,7);ax.axis('off')
    ax.set_title('Red bayesiana ingenua - esquema conceptual',fontsize=16)
    boxes=[(1,4.6,'Baja ejecucion'),(3.8,4.6,'Poco tiempo'),(6.6,4.6,'Pendientes altos')]
    for x,y,label in boxes:
        ax.add_patch(FancyBboxPatch((x,y),2.4,1.05,boxstyle='round,pad=0.1',fc='#e7f0f7',ec='#496b83'))
        ax.text(x+1.2,y+.53,label,ha='center',va='center',fontsize=10)
        ax.add_patch(FancyArrowPatch((x+1.2,y),(5,2.65),arrowstyle='->',mutation_scale=15,lw=1.5))
    ax.add_patch(FancyBboxPatch((3.7,1.6),2.6,1.05,boxstyle='round,pad=0.1',fc='#f0e7d7',ec='#b28d55'))
    ax.text(5,2.125,'Resultado P(R | e)',ha='center',va='center',fontsize=11)
    fig.text(.5,.035,'Parametros hipoteticos; no calibrados con resultados empresariales.',ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.07,1,1));fig.savefig(OUT/'red_bayesiana.png',dpi=180);plt.close(fig)
    return [str(p.relative_to(ROOT)) for p in sorted(OUT.glob('*.png'))]

if __name__=='__main__':
    for path in write_figures():print('GENERADA:',path)
