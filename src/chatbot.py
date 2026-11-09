"""PresupuestoBot: orquestacion adaptada del patron de AndesBot, material del docente.
Datos exclusivamente sinteticos. No autoriza pagos ni modifica presupuestos.
"""
from __future__ import annotations
import json,re,unicodedata
from pathlib import Path
from nlp_model import IntentClassifier,normalize
from reasoning import evaluar_partida

ROOT=Path(__file__).resolve().parents[1]

def money(v): return f'USD {v:,.2f}'
def plain(t):
    return ''.join(c for c in unicodedata.normalize('NFD',t.lower()) if unicodedata.category(c)!='Mn')

class BudgetBot:
    def __init__(self):
        self.model=IntentClassifier.load(ROOT/'models'/'intent_model.pt')
        self.data=json.loads((ROOT/'data'/'presupuesto.json').read_text(encoding='utf-8'))
        self.items=self.data['partidas']
        self.pending=None
        self.last_partida=None
        self.clarification=None
        self.alias={
            'PR-101':['personal','honorarios','nomina','nómina'],
            'PR-102':['marketing','publicidad'],
            'PR-103':['tecnologia','tecnología','licencias','software'],
            'PR-104':['capacitacion','capacitación','formacion','formación','entrenamiento'],
            'PR-105':['mantenimiento'],
            'PR-106':['logistica','logística','distribucion','distribución','transporte']}

    def find_partida(self,text):
        ids=re.findall(r'\bPR[- ]?(\d{3})\b',text.upper())
        if ids:
            code='PR-'+ids[0]
            p=next((x for x in self.items if x['id']==code),None)
            return p,True
        normalized=plain(text)
        for key,aliases in self.alias.items():
            if any(re.search(r'\b'+re.escape(plain(a))+r'\b',normalized) for a in aliases):
                return next(x for x in self.items if x['id']==key),False
        return None,False

    def _totals(self):
        return {k:sum(p[k] for p in self.items) for k in ('presupuesto_anual','ejecutado_acumulado','comprometido_acumulado')}

    def _ranking_riesgo(self,conf):
        """Comparacion completa sin alterar las probabilidades del modelo original."""
        rows=[(p,evaluar_partida(p,self.data['meses_cerrados'])) for p in self.items]
        rows.sort(key=lambda row:(-row[1]['bayes']['probabilidad'],row[0]['id']))
        top=rows[0][1]['bayes']['probabilidad']
        leaders=[(p,r) for p,r in rows if abs(r['bayes']['probabilidad']-top)<0.00001]
        def factors(r):
            names={'low_execution':'baja ejecucion','little_time':'poco tiempo restante','high_pending':'compromisos pendientes altos'}
            return ', '.join(names[k] for k,v in r['bayes']['evidencias'].items() if v) or 'sin señales activas'
        heading='Mayor resultado bayesiano academico: '+ '; '.join(
            f"{p['nombre']} ({p['id']}): {r['bayes']['probabilidad']*100:.2f}%" for p,r in leaders)
        details='; '.join(f"{p['nombre']}: ejecucion {r['ejecucion_pct']:.2f}%, "
                         f"compromisos pendientes {money(r['compromiso_pendiente'])}, "
                         f"evidencias: {factors(r)}" for p,r in leaders)
        ranking=' | '.join(f"{p['id']} {r['bayes']['probabilidad']*100:.2f}%" for p,r in rows)
        msg=(heading+'. Factores: '+details+'. Clasificacion completa: '+ranking+
             '. Probabilidades hipoteticas NO calibradas con resultados historicos; no representan riesgo real.')
        self.pending=None
        return self._reply(msg,'riesgo_incumplimiento','answer',conf)

    def _partidas_mencionadas(self, text):
        """Detecta varios codigos/nombres sin cambiar el clasificador neuronal."""
        norm=plain(text)
        found=[]
        for item in self.items:
            code=item['id']
            names=self.alias[code]
            if re.search(r'\bPR[- ]?'+code[-3:]+r'\b',text.upper()) or any(
                re.search(r'\b'+re.escape(plain(a))+r'\b',norm) for a in names):
                found.append(item)
        return found

    def _money_ranking(self, field, title, conf, ascending=False):
        rows=sorted(self.items,key=lambda p:p[field],reverse=not ascending)
        description='; '.join(f"{p['nombre']} ({p['id']}): {money(p[field])}" for p in rows)
        return self._reply(title+': '+description+'.','comparacion_partidas','answer',conf)

    def _pending_ranking(self, conf):
        rows=sorted(self.items,key=lambda p:p['comprometido_acumulado']-p['ejecutado_acumulado'],reverse=True)
        description='; '.join(f"{p['nombre']} ({p['id']}): {money(p['comprometido_acumulado']-p['ejecutado_acumulado'])}" for p in rows)
        return self._reply('Compromisos pendientes, de mayor a menor: '+description+'.','compromisos_pendientes','answer',conf)

    def _compare_two(self, partidas, text, conf):
        a,b=partidas[:2]
        norm=plain(text)
        if 'porcentaje' in norm or 'tasa' in norm:
            key='porcentaje'
            va=100*a['ejecutado_acumulado']/a['presupuesto_anual']; vb=100*b['ejecutado_acumulado']/b['presupuesto_anual']
            rendered=f"{a['nombre']}: {va:.2f}%; {b['nombre']}: {vb:.2f}%; diferencia {abs(va-vb):.2f} puntos porcentuales"
        elif 'asignad' in norm or 'aprobado' in norm or 'anual' in norm:
            key='asignado';va=a['presupuesto_anual'];vb=b['presupuesto_anual']
            rendered=f"{a['nombre']}: {money(va)}; {b['nombre']}: {money(vb)}; diferencia {money(abs(va-vb))}"
        elif 'compromis' in norm or 'pendient' in norm:
            key='compromisos';va=a['comprometido_acumulado']-a['ejecutado_acumulado'];vb=b['comprometido_acumulado']-b['ejecutado_acumulado']
            rendered=f"{a['nombre']}: {money(va)}; {b['nombre']}: {money(vb)}; diferencia {money(abs(va-vb))}"
        else:
            key='ejecutado';va=a['ejecutado_acumulado'];vb=b['ejecutado_acumulado']
            rendered=f"{a['nombre']}: {money(va)}; {b['nombre']}: {money(vb)}; diferencia {money(abs(va-vb))}"
        self.pending=None
        return self._reply('Comparacion de '+key+': '+rendered+'.','comparacion_partidas','answer',conf)

    def _clarify(self, partida, conf, kind):
        self.pending=None
        self.clarification={'id':partida['id'],'kind':kind}
        if kind=='destino':
            msg=f"Para {partida['nombre']}, ¿quieres conocer el presupuesto asignado o el gasto ejecutado?"
        else:
            msg=f"Para {partida['nombre']}, ¿quieres el saldo sin ejecutar o el saldo sin comprometer?"
        return self._reply(msg,'aclaracion','request_clarification',conf,partida=partida['id'])

    def _answer_clarification(self, text):
        """Acepta solo elecciones breves, no preguntas nuevas con palabras similares.

        Por ejemplo, "¿Cómo vamos con el presupuesto?" no responde a una
        aclaracion de "asignado o ejecutado" y debe procesarse normalmente.
        """
        ctx=self.clarification
        if ctx is None:
            return None
        norm=plain(text).strip().strip(' ¿?¡!.,;:')
        # Las respuestas a un menu de dos opciones son breves. No buscar
        # 'presupuesto' o 'gasto' como subcadenas de una pregunta completa.
        norm=re.sub(r'^(quiero|prefiero|elijo|dame|muestrame|mostrar|consulta|ver|el|la|los|las)\s+', '', norm)
        norm=re.sub(r'^(el|la|los|las)\s+', '', norm).strip()
        p=next(x for x in self.items if x['id']==ctx['id'])
        if ctx['kind']=='destino':
            if norm in ('asignado','presupuesto asignado','presupuesto aprobado','aprobado','presupuesto anual'):
                intent='presupuesto_asignado'; amount=p['presupuesto_anual'];label='presupuesto asignado'
            elif norm in ('gastado','ejecutado','gasto','gasto ejecutado','presupuesto ejecutado','importe gastado'):
                intent='presupuesto_ejecutado';amount=p['ejecutado_acumulado'];label='gasto ejecutado'
            else:
                return None
        else:
            if norm in ('sin comprometer','no comprometido','saldo sin comprometer','saldo no comprometido'):
                intent='saldo_disponible';amount=p['presupuesto_anual']-p['comprometido_acumulado'];label='saldo sin comprometer'
            elif norm in ('sin ejecutar','no ejecutado','saldo sin ejecutar','saldo no ejecutado'):
                intent='saldo_disponible';amount=p['presupuesto_anual']-p['ejecutado_acumulado'];label='saldo sin ejecutar'
            else:
                return None
        self.clarification=None
        self.last_partida=p
        return self._reply(f"{p['nombre']} ({p['id']}): {label} {money(amount)}.",intent,'answer',1,partida=p['id'])

    def respond(self,text):
        t=text.strip()
        if not t: return self._reply('Escribe una consulta sobre el presupuesto.', 'fuera_alcance','fallback',0)
        normalized=plain(t).strip(' ¿?¡!.,')
        # Mantener las restricciones con independencia de la clasificacion neuronal.
        if re.search(r'\b(autoriza|autorizar|aprueba|aprobar|aprobaste|aprobe|transfiere|transferir|paga|pagar|modifica|modificar|redistribuye|redistribuir|reduce|reducir|cambia|cambiar|ejecuta un pago|haz un pago)\b',normalized) and re.search(r'\b(pago|presupuesto|transferencia|dinero|partida|monto|marketing|capacitacion)\b',normalized):
            self.pending=None;self.clarification=None
            return self._reply('No puedo aprobar pagos, transferencias ni modificar presupuestos. Solicita autorizacion al responsable financiero.','hablar_humano','handoff',1)
        if normalized in ('salir','adios','chao','hasta luego'):
            self.pending=None;self.clarification=None;self.last_partida=None
            return self._reply('Hasta pronto. Los datos de esta demostracion son ficticios.','despedida','close',1)
        p,code_present=self.find_partida(t)
        if code_present and p is None:
            self.pending=None;self.clarification=None
            return self._reply('No existe esa partida en los datos sinteticos del ejemplo. No inventare importes.','fuera_alcance','fallback',1)
        # Una solicitud de aclaracion conserva la partida hasta recibir la eleccion.
        if self.clarification:
            clarified=self._answer_clarification(t)
            if clarified is not None:return clarified
            self.clarification=None
        # Preguntas fuera de la base: no solicitar una partida innecesariamente.
        if ('utilidad' in normalized or 'ganancia neta' in normalized or 'ingresos netos' in normalized) and ('diciembre' in normalized or 'predic' in normalized or 'sera' in normalized):
            return self._reply('No cuento con datos de ingresos, costos ni proyecciones para estimar utilidades. No inventare un pronostico.','fuera_alcance','fallback',1)
        # Intenciones frecuentes inequívocas de gestion, sin modificar los pesos del modelo.
        if re.search(r'\b(como vamos|como va|estado general|resumen general)\b',normalized) and ('presupuesto' in normalized or 'ejecucion' in normalized):
            return self._overall('resumen_general',1)
        partidas=self._partidas_mencionadas(t)
        if len(partidas)>=2 and any(x in normalized for x in ('compara','comparar','diferencia','versus',' vs ')):
            return self._compare_two(partidas,t,1)
        if ('compromis' in normalized and 'pendient' in normalized and any(x in normalized for x in ('mayor','mayores','ranking','orden','cuales','todas'))) and not partidas:
            return self._pending_ranking(1)
        # Comparaciones en unidades monetarias: 'mayor gasto ejecutado' no es
        # equivalente a 'mayor porcentaje de ejecucion'.
        asks_money_rank = bool(re.search(
            r'\b(mayor|mas|mayores)\s+(?:gasto|importe|monto|dinero|dolares)\b'
            r'|\b(gasto|importe|monto)\s+(?:total\s+)?(?:ejecutado\s+)?(?:mas\s+alto|mayor)\b',
            normalized))
        if not partidas and asks_money_rank:
            return self._money_ranking('ejecutado_acumulado','Gasto ejecutado en USD, de mayor a menor',1)
        # Respuestas explicitas en un solo mensaje: 'se destino ... asignado'.
        if p and ('se destino' in normalized or 'se ha destinado' in normalized):
            assigned=bool(re.search(r'\b(asignado|asignada|aprobado|aprobada)\b', normalized))
            spent=bool(re.search(r'\b(ejecutado|ejecutada|gastado|gastada)\b', normalized))
            if assigned != spent:
                self.pending=None;self.clarification=None;self.last_partida=p
                if assigned:
                    return self._reply(f"{p['nombre']} ({p['id']}): presupuesto asignado {money(p['presupuesto_anual'])}.",'presupuesto_asignado','answer',1,partida=p['id'])
                return self._reply(f"{p['nombre']} ({p['id']}): gasto acumulado a octubre {money(p['ejecutado_acumulado'])}.",'presupuesto_ejecutado','answer',1,partida=p['id'])
        if p and ('se destino' in normalized or 'se ha destinado' in normalized) and not any(x in normalized for x in ('gastado','ejecutado','asignado','aprobado')):
            return self._clarify(p,1,'destino')
        if p and ('cuanto dinero queda' in normalized or 'se esta acabando la plata' in normalized or 'se nos esta acabando la plata' in normalized or 'cuanta plata queda' in normalized):
            return self._clarify(p,1,'saldo')
        # Referencias anaforicas breves a la ultima partida: no anular una
        # consulta nueva y explicita a otra partida. Evita mandar 'su riesgo'
        # al ranking global o pedir de nuevo un codigo.
        followup_intent=None
        if p is None and self.last_partida and len(normalized.split())<=9:
            if re.search(r'^(?:y )?(?:que porcentaje (?:representa|tiene|es)|cual es (?:su|el) porcentaje|que porcentaje de ejecucion)',normalized):
                p=self.last_partida;followup_intent='porcentaje_ejecucion'
            elif re.search(r'^(?:y )?(?:cual es su riesgo|que riesgo tiene|y su riesgo|cual es el riesgo de (?:esa partida|ella))\b',normalized):
                p=self.last_partida;followup_intent='riesgo_incumplimiento'
            elif re.search(r'^(?:y )?(?:cuanto|y cuanto|y el gasto)',normalized):
                if any(x in normalized for x in ('gastado','ejecutado','gasto')):
                    p=self.last_partida;followup_intent='presupuesto_ejecutado'
                elif any(x in normalized for x in ('asignado','aprobado')):
                    p=self.last_partida;followup_intent='presupuesto_asignado'
        if p and ('que tan atrasad' in normalized or 'cuanto atras' in normalized):
            r=evaluar_partida(p,self.data['meses_cerrados'])
            self.last_partida=p
            return self._reply(f"{p['nombre']} ({p['id']}): ejecucion {r['ejecucion_pct']:.2f}%, referencia lineal {r['meta_lineal_pct']:.2f}%, brecha {r['brecha_pp']:.2f} puntos porcentuales. Referencia academica no estacional.",'baja_ejecucion','answer',1,partida=p['id'])
        if ('que deberia revisar' in normalized or 'para reducir el riesgo' in normalized):
            return self._reply('Revisa el cronograma de gastos, compromisos pendientes, desviaciones frente a metas mensuales y actividades no ejecutadas. La decision corresponde al responsable financiero.','alertas','answer',1)
        prediction=self.model.predict(t)
        intent=prediction['intent']; conf=prediction['confidence']
        if followup_intent is not None:
            intent=followup_intent
        if 'porcentaje' in normalized and ('ejecutado' in normalized or 'ejecucion' in normalized):
            intent='porcentaje_ejecucion'
        if p is not None and p is self.last_partida and re.search(r'^(y )?(cuanto|y cuanto)',normalized):
            if 'gastado' in normalized or 'ejecutado' in normalized: intent='presupuesto_ejecutado'
            elif 'asignado' in normalized: intent='presupuesto_asignado'
        if p and ('se esta acabando' in normalized or 'cuanto queda' in normalized) and not self.clarification:
            return self._clarify(p,conf,'saldo')
        # Preguntas comparativas de riesgo: evaluar todas las partidas, sin pedir un slot.
        normalized=plain(t)
        asks_risk=bool(re.search(r'\b(riesgo|incumplimiento|probabilidad)\b',normalized))
        asks_ranking=bool(re.search(r'\b(mayor|mas|alta|alto|ranking|orden|compar|todas|cuales|cual|priorizar)\b',normalized))
        if p is None and asks_risk and asks_ranking:
            return self._ranking_riesgo(conf)
        # Reconocer continuaciones cortas de un slot solicitado.
        if self.pending and p and (len(normalize(t).split())<=4 or intent in ('saludo','fuera_alcance')):
            intent=self.pending
        if intent=='hablar_humano':
            self.pending=None
            return self._reply('Se recomienda consultar con el responsable financiero. Esta demostracion no realiza derivaciones reales.','hablar_humano','handoff',conf)
        if intent=='saludo':
            return self._reply('Hola. Puedo consultar presupuesto, gastos, porcentajes, saldos, alertas y riesgos academicos. Corte: octubre de 2026.','saludo','answer',conf)
        if intent=='fuera_alcance':
            return self._reply('No puedo resolver esa solicitud con certeza. Pregunta por una partida, ejecucion, alertas o resumen. Si hay una duda importante, consulta con finanzas.','fuera_alcance','fallback',conf)
        single={'presupuesto_asignado','presupuesto_ejecutado','porcentaje_ejecucion','saldo_disponible','compromisos_pendientes','riesgo_incumplimiento'}
        if intent in single and p is None and not self.pending:
            # El presupuesto total y consultas globales pueden responderse sin una partida.
            if any(z in plain(t) for z in ['total','empresa','general','todas','global','conjunto']):
                return self._overall(intent,conf)
            self.pending=intent
            return self._reply('¿A que partida te refieres? Indica, por ejemplo, PR-104 o capacitacion.',''+intent,'request_slot',conf)
        if intent in single and p is None:
            return self._reply('No pude identificar una partida. Usa un codigo PR-101 a PR-106.',''+intent,'request_slot',conf)
        self.pending=None
        if p: self.last_partida=p
        if intent in single:
            r=evaluar_partida(p,self.data['meses_cerrados']); name=p['nombre']; prefix=f"{name} ({p['id']}): "
            if intent=='presupuesto_asignado': answer=prefix+f"presupuesto anual {money(p['presupuesto_anual'])}."
            elif intent=='presupuesto_ejecutado': answer=prefix+f"gasto acumulado a octubre {money(p['ejecutado_acumulado'])}."
            elif intent=='porcentaje_ejecucion': answer=prefix+f"ejecucion {r['ejecucion_pct']:.2f}% de la asignacion anual; referencia lineal {r['meta_lineal_pct']:.2f}%."
            elif intent=='saldo_disponible': answer=prefix+f"saldo sin comprometer {money(r['saldo_sin_comprometer'])}; saldo sin ejecutar {money(r['saldo_sin_ejecutar'])}. Son conceptos distintos."
            elif intent=='compromisos_pendientes': answer=prefix+f"comprometido total {money(p['comprometido_acumulado'])}, de los cuales {money(r['compromiso_pendiente'])} estan pendientes de ejecutar."
            else: answer=prefix+f"resultado Bayes academico {r['bayes']['probabilidad']*100:.2f}%, accion sugerida: {r['bayes']['decision']}. Probabilidades hipoteticas, no calibradas con datos historicos."
            return self._reply(answer,intent,'answer',conf,partida=p['id'])
        if intent=='resumen_general': return self._overall(intent,conf)
        if intent=='comparacion_partidas':
            ranked=sorted(self.items,key=lambda x:x['ejecutado_acumulado']/x['presupuesto_anual'],reverse=True)
            return self._reply('Ejecucion porcentual, de mayor a menor: '+ '; '.join(f"{x['nombre']} {100*x['ejecutado_acumulado']/x['presupuesto_anual']:.2f}%" for x in ranked)+'.','comparacion_partidas','answer',conf)
        if intent in ('baja_ejecucion','alertas'):
            selected=[(x,evaluar_partida(x,self.data['meses_cerrados'])) for x in self.items]
            if intent=='baja_ejecucion':
                selected=[(x,r) for x,r in selected if 'P03: baja ejecucion' in r['alertas']]
                msg='Partidas bajo el umbral academico: '+('; '.join(f"{x['nombre']} ({r['ejecucion_pct']:.2f}%)" for x,r in selected) or 'ninguna')+'.'
            else:
                selected=[(x,r) for x,r in selected if r['alertas']]
                msg='Alertas de control: '+('; '.join(f"{x['nombre']}: {', '.join(r['alertas'])}" for x,r in selected) or 'ninguna')+'.'
            return self._reply(msg,intent,'answer',conf)
        return self._reply('No tengo una respuesta aprobada para esa solicitud.','fuera_alcance','fallback',conf)

    def _overall(self,intent,conf):
        totals=self._totals(); bud=totals['presupuesto_anual']; real=totals['ejecutado_acumulado']; com=totals['comprometido_acumulado']
        if intent=='presupuesto_asignado': msg=f'Presupuesto anual total: {money(bud)}.'
        elif intent=='presupuesto_ejecutado': msg=f'Gasto ejecutado acumulado: {money(real)}.'
        elif intent=='porcentaje_ejecucion': msg=f'Ejecucion global: {100*real/bud:.2f}%.'
        elif intent=='saldo_disponible': msg=f'Saldo sin comprometer: {money(bud-com)}. Saldo sin ejecutar: {money(bud-real)}.'
        elif intent=='compromisos_pendientes': msg=f'Compromisos pendientes globales: {money(com-real)}.'
        elif intent=='riesgo_incumplimiento': msg='El modelo bayesiano se aplica a partidas individuales; indica una partida para obtener la estimacion academica.'
        else: msg=f'Resumen al corte octubre de 2026: presupuesto {money(bud)}, ejecutado {money(real)} ({100*real/bud:.2f}%), comprometido {money(com)}, pendiente de ejecutar de compromisos {money(com-real)}.'
        return self._reply(msg,intent,'answer',conf)

    def _reply(self,msg,intent,action,conf,partida=None):
        return {'text':msg,'intent':intent,'action':action,'confidence':conf,'partida':partida,'source':'data/presupuesto.json; reglas academicas version 0.1','periodo':'2026-10'}
