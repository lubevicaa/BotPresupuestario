# PresupuestoBot EC 

Proyecto académico de chatbot presupuestario para Comercial Delta S.A. (**empresa ficticia, datos 100 % sintéticos**).

**Origen y atribución:** `nlp_model.py` y el flujo de entrenamiento derivan de *AndesBot*. `reasoning.py`, corpus, datos, orquestación y la interfaz se adaptaron al caso presupuestario. 

## Cómo iniciar

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Interfaz alternativa de consola: `python src/cli.py`.

## Evaluar / reproducir

```bash
OMP_NUM_THREADS=1 python -m unittest discover -s tests -v
OMP_NUM_THREADS=1 python tests/run_acceptance.py
OMP_NUM_THREADS=1 python experiments/validation_models.py
OMP_NUM_THREADS=1 python src/train.py
```



## Resultados reales reportados

| Indicador | Fase 2 | Fase 3 |
|---|---:|---:|
| Prueba NLP: exactitud | 75,00 % | 84,62 % (44/52) |
| Prueba NLP: F1 macro | 0,7425 | 0,8437 |
| Escenarios de aceptación | 23/24 | 23/24 |
| Pruebas unitarias | 12/12 | 12/12 |


**Error funcional documentado:** T14, «cuánto se destinó a mantenimiento», se interpretó como presupuesto ejecutado en lugar de asignado. Es una consulta semánticamente ambigua; antes de un despliegue real conviene solicitar aclaración ante formulaciones de este tipo. No se alteró el caso esperado ni el conjunto de prueba para simular mejora.

**Avisos:** la puntuación softmax no equivale a confianza probabilística calibrada. Bayes usa probabilidades hipotéticas, no mide un riesgo empírico de incumplimiento. El prototipo no ejecuta acciones económicas reales.

Ver `docs/manual_streamlit.md` para guía de uso y `resultados/` para evidencias reproducibles.

## Actualizacion: comparacion de riesgo (Fase 3.1)
- `src/chatbot.py`: se agrega una ruta de comparacion global para consultas de mayor riesgo o ranking, conservando la red bayesiana original y sin reentrenar el clasificador.
- El resultado identifica empates, muestra ejecucion, compromisos pendientes y evidencias activas por partida; aclara que las probabilidades son hipoteticas.
- `tests/test_chatbot.py`: dos pruebas unitarias adicionales para riesgo global y ranking completo.
- Verificacion local: 14/14 pruebas unitarias. Suite de aceptacion original: 23/24 (persiste ambiguedad en la consulta de presupuesto asignado de mantenimiento).

## Version 3.3 - 
Se corrigieron comparaciones por importes, ranking de compromisos pendientes, preguntas ambiguas (se solicita aclaracion), seguimiento corto de una partida, resumen global con lenguaje cotidiano y rechazo de modificaciones. Suite de aceptacion original: 24/24 Vease `docs/cambios_fase3_3.md` para diferencias, pruebas y limitaciones.



