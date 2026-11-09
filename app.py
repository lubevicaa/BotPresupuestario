"""Interfaz de demostracion Streamlit de PresupuestoBot EC.
Ejecutar desde la raiz: streamlit run app.py
"""
from __future__ import annotations
import sys
from pathlib import Path
import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'src'))
from chatbot import BudgetBot

st.set_page_config(page_title='PresupuestoBot EC', page_icon='📊', layout='wide')
st.title('📊 PresupuestoBot EC')
st.caption('Prototipo académico · Comercial Delta S.A. (ficticia) · Corte: octubre 2026')
st.info('Datos sintéticos. Indicadores y alertas académicos, no decisiones financieras ni pronósticos validados.')

if 'bot' not in st.session_state:
    st.session_state.bot = BudgetBot()
if 'history' not in st.session_state:
    st.session_state.history = []

with st.sidebar:
    st.header('Datos de referencia')
    data = st.session_state.bot.data
    partidas = data['partidas']
    total = sum(p['presupuesto_anual'] for p in partidas)
    ejecutado = sum(p['ejecutado_acumulado'] for p in partidas)
    comprometido = sum(p['comprometido_acumulado'] for p in partidas)
    st.metric('Presupuesto anual', f'USD {total:,.0f}')
    st.metric('Ejecutado a octubre', f'USD {ejecutado:,.0f}')
    st.metric('Porcentaje de ejecución', f'{ejecutado / total * 100:.2f}%')
    st.metric('Compromisos pendientes', f'USD {comprometido-ejecutado:,.0f}')
    st.markdown('**Preguntas de ejemplo**')
    examples = [
        'Dame un resumen del presupuesto',
        '¿Qué partidas tienen baja ejecución?',
        '¿Cuánto se asignó a capacitación?',
        '¿Qué riesgo tiene marketing?',
        '¿Cuánto queda sin comprometer en logística?',
    ]
    for i, e in enumerate(examples):
        if st.button(e, use_container_width=True, key=f'example_{i}'):
            st.session_state.pending_prompt = e
    if st.button('Nueva conversación', use_container_width=True):
        st.session_state.bot = BudgetBot()
        st.session_state.history = []
        st.session_state.pop('pending_prompt', None)
        st.rerun()
    st.markdown('**Alcance**: 6 partidas y períodos enero-octubre de 2026. Sin conexión a ERP ni aprobación de pagos.')

for m in st.session_state.history:
    with st.chat_message(m['role']):
        st.write(m['content'])
        if m['role'] == 'assistant' and 'details' in m:
            with st.expander('Datos de decisión'):
                st.json(m['details'])

prompt = st.chat_input('Pregunta por un presupuesto, gasto, saldo o alerta...')
if not prompt:
    prompt = st.session_state.pop('pending_prompt', None)
if prompt:
    st.session_state.history.append({'role':'user','content':prompt})
    try:
        result = st.session_state.bot.respond(prompt)
        response = result['text']
    except Exception as exc:
        result = None
        response = 'No pude procesar la consulta. Revisa que el modelo y los datos estén disponibles.'
        st.error(f'Error técnico local: {type(exc).__name__}')
    msg = {'role':'assistant','content':response}
    if result:
        msg['details'] = {'intención':result['intent'],'acción':result['action'],
                          'score_softmax_no_calibrado':result['confidence'],
                          'partida':result['partida'],'periodo':result['periodo'],
                          'fuente':result['source']}
    st.session_state.history.append(msg)
    st.rerun()
