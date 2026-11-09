# PresupuestoBot 3.3 - cambios focalizados y verificaciones

## Alcance
Se partio de PresupuestoBot 3.2. No se modificaron `src/nlp_model.py`, `src/train.py`, `src/reasoning.py`, `data/corpus.json`, `data/presupuesto.json` ni `models/intent_model.pt`. El modelo NLP conserva 338 frases y las metricas historicas (exactitud 84,62 %, F1 macro 0,8437). La red bayesiana conserva los parametros hipoteticos originales.

## Cambios de produccion
- `src/chatbot.py`: deteccion de dos partidas y comparacion de gasto, presupuesto, porcentajes y compromisos; ranking monetario de gasto; ranking de compromisos pendientes; aclaracion de preguntas ambiguas de destino y saldo; resumen ante "como vamos"; referencia a la ultima partida en seguimiento corto; calculo de brecha porcentual en preguntas de atraso; rechazo explicito de modificaciones, pagos y transferencias; fallback ante prediccion de utilidad neta sin datos.
- `app.py`: sin modificaciones. El aspecto web se mantiene, pero muestra las respuestas mejoradas del motor.

## Pruebas
- `tests/test_dialogo_33.py`: 12 pruebas focalizadas nuevas.
- `tests/test_financial_integrity.py`: la prueba historica T14 se transforma en verificacion de solicitud de aclaracion. No se oculta el fallo de la version 3.2.
- `tests/run_acceptance.py`: modifica la expectativa de T14 para 3.3 y reinicia la memoria entre casos independientes, pero conserva las continuaciones previstas T16, T18 y T21.
- `tests/run_manual_30_33.py`: reproduce las 30 consultas exploratorias y exporta las respuestas; esto no es validacion por usuarios independientes ni garantia de exactitud.

## Evidencias ejecutadas en 3.3
- `python -m unittest discover -s tests -v`: 35/35 superadas.
- `python tests/run_acceptance_extended.py`: 10/10 superadas.
- `python tests/run_acceptance.py`: 24/24 con expectativas 3.3 (T14 ahora espera aclaracion).
- `python tests/run_manual_30_33.py`: 30 respuestas exportadas. La valoracion humana debe hacerse de nuevo contra criterios definidos antes de la prueba.

## Interpretacion correcta
La mejora es del motor de dialogo, NO de la capacidad estadistica del clasificador neuronal. No afirmar que la exactitud NLP subio ni comparar 24/24 de 3.3 con 23/24 de 3.2 sin indicar el cambio de expectativa. No son pruebas de una instalacion empresarial ni con datos reales.

## Probar en Windows
1. Cerrar el servidor con Ctrl+C en PowerShell.
2. Descomprimir el ZIP 3.3 en carpeta nueva y abrir PowerShell alli.
3. Ejecutar `python -m streamlit run app.py` (dependencias instaladas previamente).
4. Probar preguntas 7, 9, 10, 16-20, 23-24, 27, 29 y 30. Si solicita aclaracion, contestar "presupuesto asignado", "gasto ejecutado", "sin ejecutar" o "sin comprometer".

## Atribucion
Adaptacion a partir del ejemplo docente AndesBot autorizado por el profesor. Se conserva el componente neuronal original y se amplia el motor conversacional del proyecto de control presupuestario. El equipo debe validar el codigo y las afirmaciones antes de su entrega.
