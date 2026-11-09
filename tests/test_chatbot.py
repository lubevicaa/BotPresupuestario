import unittest,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from chatbot import BudgetBot
class TestChatbot(unittest.TestCase):
 @classmethod
 def setUpClass(cls): cls.bot=BudgetBot()
 def setUp(self): self.bot.pending=None
 def test_saldos_contables(self):
  p=self.bot.items[3]; self.assertEqual(p['comprometido_acumulado']-p['ejecutado_acumulado'],p['compromiso_pendiente'])
 def test_resumen_total(self):
  r=self.bot._overall('resumen_general',1);self.assertIn('USD 318,000.00',r['text'])
 def test_bloqueo_autorizacion(self):
  r=self.bot.respond('aprueba un pago de 500');self.assertEqual(r['action'],'handoff')
 def test_codigo_inexistente(self):
  r=self.bot.respond('saldo de PR-999');self.assertEqual(r['action'],'fallback')
 def test_codigos(self):
  p,_=self.bot.find_partida('PR-104');self.assertEqual(p['nombre'],'Capacitacion')
 def test_slot_solicitud(self):
  self.bot.pending='porcentaje_ejecucion';r=self.bot.respond('PR-104');self.assertEqual(r['intent'],'porcentaje_ejecucion');self.assertIn('22.50%',r['text'])
 def test_mayor_riesgo_sin_partida(self):
  r=self.bot.respond('¿Que partida tiene mayor riesgo de incumplimiento?')
  self.assertEqual(r['action'],'answer')
  self.assertEqual(r['intent'],'riesgo_incumplimiento')
  self.assertIn('Capacitacion',r['text'])
  self.assertIn('Marketing',r['text'])
  self.assertIn('hipoteticas',r['text'])
 def test_ranking_riesgo(self):
  r=self.bot.respond('Compara el riesgo de todas las partidas')
  self.assertEqual(r['action'],'answer')
  for code in ('PR-101','PR-102','PR-103','PR-104','PR-105','PR-106'):
   self.assertIn(code,r['text'])
 def test_consulta_directa(self):
  self.bot.pending='presupuesto_asignado';r=self.bot.respond('PR-102');self.assertIn('USD 48,000.00',r['text'])
if __name__=='__main__':unittest.main()
