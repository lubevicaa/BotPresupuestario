"""24 escenarios heredados con expectativa T14 actualizada para la aclaracion de 3.3.
Los 23/24 historicos de 3.2 se mantienen en la entrega 3.2, sin reescribir."""
import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from chatbot import BudgetBot
scenarios=[
 ('Hola presupuesto bot','saludo','answer'),
 ('cuál es el presupuesto aprobado de marketing','presupuesto_asignado','answer'),
 ('gasto ejecutado de capacitación','presupuesto_ejecutado','answer'),
 ('qué porcentaje de ejecución tiene capacitación','porcentaje_ejecucion','answer'),
 ('saldo no comprometido para personal','saldo_disponible','answer'),
 ('qué partida ha ejecutado más','comparacion_partidas','answer'),
 ('cuáles partidas están atrasadas','baja_ejecucion','answer'),
 ('compromisos pendientes de marketing','compromisos_pendientes','answer'),
 ('qué alertas hay en el presupuesto','alertas','answer'),
 ('evalúa riesgo presupuestario de capacitación','riesgo_incumplimiento','answer'),
 ('dame un resumen del presupuesto','resumen_general','answer'),
 ('quiero hablar con finanzas','hablar_humano','handoff'),
 ('cuéntame un chiste','fuera_alcance','fallback'),
 ('cuánto se destinó a mantenimiento','aclaracion','request_clarification'),
 ('cuánto hemos ejecutado en porcentaje','porcentaje_ejecucion','request_slot'),
 ('PR-103','porcentaje_ejecucion','answer'),
 ('importe gastado a octubre','presupuesto_ejecutado','request_slot'),
 ('PR-106','presupuesto_ejecutado','answer'),
 ('total de gastos reconocidos','presupuesto_ejecutado','answer'),
 ('consulta del presupuesto anual','presupuesto_asignado','request_slot'),
 ('PR-104','presupuesto_asignado','answer'),
 ('autoriza un pago de 500','hablar_humano','handoff'),
 ('presupuesto de PR-999','fuera_alcance','fallback'),
 ('salir','despedida','close'),
]
bot=BudgetBot(); rows=[]
for i,(text,intent,action) in enumerate(scenarios,1):
    if i not in (16,18,21):
        bot.pending=None
        bot.clarification=None
        bot.last_partida=None
    result=bot.respond(text)
    ok=result['intent']==intent and result['action']==action
    rows.append({'id':f'T{i:02d}','entrada':text,'intencion_esperada':intent,'accion_esperada':action,'intencion_obtenida':result['intent'],'accion_obtenida':result['action'],'respuesta':result['text'],'cumple':ok})
report={'n':len(rows),'superadas':sum(x['cumple'] for x in rows),'tasa':round(sum(x['cumple'] for x in rows)/len(rows),4),'escenarios':rows}
(ROOT/'resultados'/'aceptacion.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('ACEPTACION',report['superadas'],'/',report['n'])
for x in rows:
 if not x['cumple']:print(x['id'],x['entrada'],'=>',x['intencion_obtenida'],x['accion_obtenida'],'expected',x['intencion_esperada'],x['accion_esperada'])
