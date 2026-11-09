"""Suite independiente complementaria: intencion, accion y contenido numerico."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from chatbot import BudgetBot
bot=BudgetBot()
scenarios=[
('E01','¿Cuál es el presupuesto total de la empresa?','presupuesto_asignado','answer',['USD 318,000.00']),
('E02','¿Qué partidas tienen baja ejecución?','baja_ejecucion','answer',['Marketing','Capacitacion','52.50%','22.50%']),
('E03','¿Cuánto se ha ejecutado en capacitación?','presupuesto_ejecutado','answer',['USD 5,400.00']),
('E04','¿Qué partida tiene mayor riesgo de incumplimiento?','riesgo_incumplimiento','answer',['PR-102','PR-104','85.54%','NO calibradas']),
('E05','Compara el riesgo de todas las partidas','riesgo_incumplimiento','answer',['PR-101','PR-102','PR-103','PR-104','PR-105','PR-106']),
('E06','¿Cuál es el riesgo de capacitación?','riesgo_incumplimiento','answer',['85.54%','hipoteticas']),
('E07','¿Cuánto saldo sin comprometer tiene mantenimiento?','saldo_disponible','answer',['USD 3,500.00','USD 8,800.00']),
('E08','¿Cuánto tiene comprometido pendiente marketing?','compromisos_pendientes','answer',['USD 9,800.00']),
('E09','autoriza un pago de 500','hablar_humano','handoff',['No puedo aprobar']),
('E10','presupuesto de PR-999','fuera_alcance','fallback',['No existe']),
]
rows=[]
for case,text,intent,action,parts in scenarios:
    bot.pending=None
    r=bot.respond(text)
    checks={'intencion':r['intent']==intent,'accion':r['action']==action,'contenido':all(x.casefold() in r['text'].casefold() for x in parts)}
    rows.append({'id':case,'entrada':text,'esperado':{'intencion':intent,'accion':action,'fragmentos':parts},'obtenido':r,'verificaciones':checks,'cumple':all(checks.values())})
report={'tipo':'prueba ampliada con aserciones de contenido, no prueba de generalizacion independiente','n':len(rows),'superadas':sum(r['cumple'] for r in rows),'escenarios':rows}
out=ROOT/'resultados'/'aceptacion_ampliada.json'
out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('ACEPTACION AMPLIADA',report['superadas'],'/',report['n'])
for r in rows:
    if not r['cumple']:print(r['id'],r['verificaciones'],r['obtenido']['text'])
if report['superadas']!=report['n']:sys.exit(1)
