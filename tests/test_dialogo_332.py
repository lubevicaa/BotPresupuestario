import unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from chatbot import BudgetBot

class TestDialogo332(unittest.TestCase):
    def setUp(self):
        self.bot=BudgetBot()

    def test_destino_asignado_en_una_pregunta(self):
        r=self.bot.respond('¿Cuánto se destinó a mantenimiento? Asignado')
        self.assertEqual(r['intent'],'presupuesto_asignado')
        self.assertIn('USD 30,000.00',r['text'])

    def test_destino_ejecutado_en_una_pregunta(self):
        r=self.bot.respond('¿Cuánto se destinó a mantenimiento? Ejecutado')
        self.assertEqual(r['intent'],'presupuesto_ejecutado')
        self.assertIn('USD 21,200.00',r['text'])

    def test_secuencia_porcentaje_y_riesgo_contextual(self):
        self.bot.respond('¿Cuánto presupuesto tiene asignado capacitación?')
        self.bot.respond('¿Y cuánto se ha gastado?')
        pct=self.bot.respond('¿Qué porcentaje representa?')
        self.assertEqual(pct['intent'],'porcentaje_ejecucion')
        self.assertIn('22.50%',pct['text'])
        risk=self.bot.respond('¿Cuál es su riesgo?')
        self.assertEqual(risk['intent'],'riesgo_incumplimiento')
        self.assertIn('85.54%',risk['text'])
        self.assertEqual(risk['partida'],'PR-104')

    def test_mayor_gasto_monetario(self):
        r=self.bot.respond('¿Cuál es la partida con mayor gasto ejecutado?')
        self.assertIn('Gasto ejecutado en USD',r['text'])
        self.assertIn('USD 99,700.00',r['text'])
        self.assertLess(r['text'].index('Personal y honorarios'),r['text'].index('Logistica y distribucion'))

    def test_nueva_pregunta_interrumpe_aclaracion(self):
        self.bot.respond('¿Cuánto se destinó a mantenimiento?')
        r=self.bot.respond('¿Cómo vamos con el presupuesto?')
        self.assertEqual(r['intent'],'resumen_general')
        self.assertIn('USD 318,000.00',r['text'])

    def test_respuesta_breve_a_aclaracion(self):
        self.bot.respond('¿Cuánto se destinó a mantenimiento?')
        r=self.bot.respond('Asignado')
        self.assertIn('USD 30,000.00',r['text'])

if __name__=='__main__':unittest.main()
