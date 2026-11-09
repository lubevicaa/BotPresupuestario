# PresupuestoBot 3.2 - Verificacion tecnica complementaria

**Base reutilizada:** PresupuestoBot 3.1, a su vez adaptado de AndesBot (material docente). Los resultados corresponden a datos sinteticos.

## Ejecucion reproducida

- `python -m unittest discover -s tests -v`: **23/23 pruebas superadas**. Evidencia: `resultados/pruebas_unitarias_fase3_2.log`.
- `python tests/run_acceptance.py`: **23/24 escenarios superados**. Evidencia: `resultados/aceptacion_original_fase3_2.log` y `resultados/aceptacion.json`.
- `python tests/run_acceptance_extended.py`: **10/10 escenarios superados**, verificando intencion, accion y fragmentos concretos de respuesta. Evidencia: `resultados/aceptacion_ampliada.json`.

## Archivos nuevos

- `tests/test_financial_integrity.py`: nueve pruebas adicionales que comprueban conciliacion mensual, totales, formulas por partida, importes, comparaciones, evidencia de riesgo, bloqueo de operaciones, IDs inexistentes y el registro del error semantico.
- `tests/run_acceptance_extended.py`: diez escenarios adicionales con verificaciones de contenido, incluyendo riesgo global, comparacion, saldos, compromisos y seguridad.
- `resultados/pruebas_unitarias_fase3_2.log`, `resultados/aceptacion_original_fase3_2.log`, `resultados/aceptacion_ampliada.json`: evidencia producida por ejecucion local.

## Limitaciones importantes

1. **T14 no corregido:** 'cuanto se destino a mantenimiento' es interpretado como gasto ejecutado, aunque la expectativa era presupuesto asignado. Una prueba nueva registra el error observado; no implica que ese comportamiento sea correcto.
2. Las diez pruebas ampliadas son pruebas de regresion funcional con contenido esperado. **No son una evaluacion independiente de generalizacion del clasificador NLP.**
3. Las pruebas adicionales comprueban cifras representativas y formulas de las seis partidas, pero no certifican exhaustivamente la correccion de cualquier consulta libre.
4. No se modificaron ni reentrenaron `src/nlp_model.py`, `src/train.py`, `models/intent_model.pt` ni las probabilidades del razonamiento bayesiano.
5. El informe academico debe actualizar la afirmacion anterior de 12 pruebas acreditadas / 14 implementadas a 23 pruebas unitarias ejecutadas y acreditadas en esta version; conservar el registro historico sin sobrescribirlo.

## Comandos

```powershell
python -m unittest discover -s tests -v
python tests/run_acceptance.py
python tests/run_acceptance_extended.py
python -m streamlit run app.py
```

**Integridad academica:** declarar la reutilizacion de AndesBot y la asistencia tecnica de IA conforme a la politica docente. El prototipo no autoriza transacciones financieras ni predice riesgos calibrados.
