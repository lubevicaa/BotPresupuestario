# Manual básico de usuario — PresupuestoBot EC (Fase 3)

## Requisitos
Python 3.10+, Windows/macOS/Linux; el paquete contiene el modelo entrenado `models/intent_model.pt`.

## Instalación y ejecución
Desde la carpeta del proyecto:

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Abra la dirección local que indique Streamlit (usualmente `http://localhost:8501`).
Como alternativa: `python src/cli.py` para la consola.

## Uso
- Escriba una pregunta presupuestaria en el chat o haga clic en una pregunta de ejemplo de la barra lateral.
- Para consultas de una sola partida, identifíquela por nombre o código PR-101 a PR-106. Si falta el dato, el chatbot pedirá aclaración.
- Despliegue **Datos de decisión** para ver la intención, la acción y el valor softmax **no calibrado**.
- Use **Nueva conversación** para borrar el historial y el estado de partida pendiente.

## Alcance y advertencias
- Comercial Delta S.A., empresa ficticia; importes sintéticos, corte octubre de 2026.
- No hay conexión con ERP, bancos, sistemas contables ni servicios externos.
- Los umbrales de alertas y probabilidades bayesianas son hipótesis didácticas, no pronósticos validados.
- El chat no permite efectuar pagos, reasignaciones ni autorizaciones.
- No introducir datos financieros o personales reales en la demostración.

## Capturas para el informe
Capturar con la interfaz **en ejecución**: (1) pantalla principal y KPIs, (2) consulta de resumen, (3) solicitud de partida, (4) alertas y (5) panel de datos de decisión. Las capturas no están incorporadas porque no se ha ejecutado un navegador en este entorno.
