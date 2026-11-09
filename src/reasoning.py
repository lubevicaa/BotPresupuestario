"""PresupuestoBot fase 1: reglas y Bayes sin red neuronal conectada todavia.
Adaptacion conceptual de src/reasoning.py de AndesBot (material docente).
Probabilidades ilustrativas NO estimadas de eventos reales.
"""
from __future__ import annotations
from dataclasses import dataclass

@dataclass
class RiskNetwork:
    prior_risk: float = 0.25
    # Observacion True/False condicionada a riesgo False y riesgo True.
    likelihoods = {
        "low_execution": ((0.80,0.20),(0.22,0.78)),
        "little_time": ((0.60,0.40),(0.30,0.70)),
        "high_pending": ((0.75,0.25),(0.35,0.65)),
    }
    def posterior(self,evidence:dict[str,bool])->dict:
        scores={False:1-self.prior_risk,True:self.prior_risk}
        for name,observed in evidence.items():
            if name not in self.likelihoods: raise ValueError('Evidencia desconocida: '+name)
            for state in (False,True):
                scores[state]*=self.likelihoods[name][int(state)][int(observed)]
        z=sum(scores.values())
        probability=scores[True]/z
        return {'probabilidad':round(probability,4),'decision':'revisar' if probability>=0.65 else 'monitorear','evidencias':evidence,'aviso':'Estimacion bajo supuestos academicos; no calibrada con datos historicos.'}

def evaluar_partida(partida:dict,meses_cerrados:int=10)->dict:
    presupuesto=partida['presupuesto_anual']; real=partida['ejecutado_acumulado']; compromiso=partida['comprometido_acumulado']
    if presupuesto<=0: raise ValueError('El presupuesto debe ser positivo')
    if real<0 or compromiso<0: raise ValueError('Los importes deben ser no negativos')
    meta=100*meses_cerrados/12
    pct=100*real/presupuesto
    pend=compromiso-real
    brecha=pct-meta
    meses_restantes=12-meses_cerrados
    evidencias={'low_execution':brecha < -15,'little_time':meses_restantes<=2,'high_pending':pend/presupuesto > 0.20}
    alertas=[]
    if real>presupuesto:alertas.append('P02: sobreejecucion')
    if evidencias['low_execution']:alertas.append('P03: baja ejecucion')
    if evidencias['high_pending']:alertas.append('P04: compromisos pendientes altos')
    if evidencias['low_execution'] and evidencias['little_time']:alertas.append('P05: revision prioritaria')
    bayes=RiskNetwork().posterior(evidencias)
    return {'partida':partida['id'],'ejecucion_pct':round(pct,2),'meta_lineal_pct':round(meta,2),'brecha_pp':round(brecha,2),'saldo_sin_ejecutar':presupuesto-real,'saldo_sin_comprometer':presupuesto-compromiso,'compromiso_pendiente':pend,'alertas':alertas,'bayes':bayes}
