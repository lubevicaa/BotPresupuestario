# PresupuestoBot EC — Fase 3: mejora de NLP e interfaz web

Proyecto académico de chatbot presupuestario para Comercial Delta S.A. (**empresa ficticia, datos 100 % sintéticos**).

**Origen y atribución:** `nlp_model.py` y el flujo de entrenamiento derivan de *AndesBot*, ejemplo entregado por el docente. `reasoning.py`, corpus, datos, orquestación y la interfaz se adaptaron al caso presupuestario. Registrar esta reutilización en el informe y validar su uso académico con el docente.

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

Al reentrenar se sobrescriben `models/intent_model.pt`, `metricas_nlp.json` y `predicciones_test.json`. Mantener respaldo de las versiones antes de ejecutar. Las diferencias de software/hardware pueden variar resultados ligeramente.

## Cambios frente a Fase 2

- En validación se compararon TF-IDF de palabras, fragmentos de palabras (`char_wb`) y su combinación. La combinación fue la mejor entre las evaluadas con validación, sin elegirla a partir de prueba (archivo `resultados/experimentos_validacion.json`).
- Modelo final híbrido: embeddings 32d + proyección TF-IDF palabra/carácter 4022d + MLP residual + ruta lineal logística congelada. **No es exclusivamente deep learning**: la predicción incluye explícitamente ML lineal y componente neuronal.
- Interfaz de chat Streamlit en `app.py`: KPIs, preguntas de ejemplo, conversación de varios turnos, diagnóstico de decisiones y reinicio. **Código sintácticamente validado, interfaz no ejecutada en navegador en este entorno**.
- Conserva las reglas presupuestarias y Bayes sobre supuestos de Fase 2.

## Resultados reales reportados

| Indicador | Fase 2 | Fase 3 |
|---|---:|---:|
| Prueba NLP: exactitud | 75,00 % | 84,62 % (44/52) |
| Prueba NLP: F1 macro | 0,7425 | 0,8437 |
| Escenarios de aceptación | 23/24 | 23/24 |
| Pruebas unitarias | 12/12 | 12/12 |

Prueba independiente del clasificador contiene solamente 52 frases (4 por clase) y comparte proceso de autoría sintética con entrenamiento. Se requiere corpus ampliado y validación externa para estimar generalización; **no** hay validación con datos empresariales.

**Error funcional documentado:** T14, «cuánto se destinó a mantenimiento», se interpretó como presupuesto ejecutado en lugar de asignado. Es una consulta semánticamente ambigua; antes de un despliegue real conviene solicitar aclaración ante formulaciones de este tipo. No se alteró el caso esperado ni el conjunto de prueba para simular mejora.

**Avisos:** la puntuación softmax no equivale a confianza probabilística calibrada. Bayes usa probabilidades hipotéticas, no mide un riesgo empírico de incumplimiento. El prototipo no ejecuta acciones económicas reales.

Ver `docs/manual_streamlit.md` para guía de uso y `resultados/` para evidencias reproducibles.

## Actualizacion: comparacion de riesgo (Fase 3.1)
- `src/chatbot.py`: se agrega una ruta de comparacion global para consultas de mayor riesgo o ranking, conservando la red bayesiana original y sin reentrenar el clasificador.
- El resultado identifica empates, muestra ejecucion, compromisos pendientes y evidencias activas por partida; aclara que las probabilidades son hipoteticas.
- `tests/test_chatbot.py`: dos pruebas unitarias adicionales para riesgo global y ranking completo.
- Verificacion local: 14/14 pruebas unitarias. Suite de aceptacion original: 23/24 (persiste ambiguedad en la consulta de presupuesto asignado de mantenimiento).
- Para actualizar un proyecto Fase 3 existente, reemplazar `src/chatbot.py` con el de esta version. No se requiere volver a instalar dependencias ni reentrenar.

## Version 3.3 - mejoras del dialogo sin reentrenamiento
Se corrigieron comparaciones por importes, ranking de compromisos pendientes, preguntas ambiguas (se solicita aclaracion), seguimiento corto de una partida, resumen global con lenguaje cotidiano y rechazo de modificaciones. Vease `docs/cambios_fase3_3.md` para diferencias, pruebas y limitaciones. Las metricas NLP permanecen sin cambios.

## Generacion automatica de figuras y capturas para la entrega

El docente puede reproducir evidencias en su computador sin recibir imagenes prehechas.
Desde la carpeta que contiene `app.py`:

```powershell
python -m pip install -r requirements.txt
python -m pip install playwright
python -m playwright install chromium
python docs/generate_evidence.py
```

- `docs/generate_figures.py` regenera cinco figuras desde `resultados/metricas_nlp.json` y la arquitectura documentada.
- `docs/generate_captures.py` inicia Streamlit en un puerto libre, realiza preguntas automaticas a traves de Chromium y guarda tres capturas reales de pantalla. Cierra el servidor al terminar.
- Resultados: `docs/figuras/*.png` y `docs/capturas/*.png`.
- Solo figuras: `python docs/generate_evidence.py --solo-figuras`.
- Solo capturas: `python docs/generate_evidence.py --solo-capturas`.

El proceso no reentrena el modelo. Requiere instalar navegador de automatizacion con el paso `playwright install chromium` (una sola vez).
