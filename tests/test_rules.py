import json,unittest,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from reasoning import evaluar_partida, RiskNetwork
class TestRules(unittest.TestCase):
 @classmethod
 def setUpClass(cls): cls.data=json.loads((ROOT/'data'/'presupuesto.json').read_text(encoding='utf-8'))
 def test_sumas_y_compromisos(self):
  for p in self.data['partidas']:
   self.assertEqual(sum(p['real_mensual'].values()),p['ejecutado_acumulado'])
   self.assertGreaterEqual(p['comprometido_acumulado'],p['ejecutado_acumulado'])
   self.assertLessEqual(p['comprometido_acumulado'],p['presupuesto_anual'])
 def test_capacitacion_alerta(self):
  p=next(x for x in self.data['partidas'] if x['id']=='PR-104')
  self.assertIn('P03: baja ejecucion',evaluar_partida(p)['alertas'])
 def test_saldos_no_duplican_compromisos(self):
  for p in self.data['partidas']:
   r=evaluar_partida(p)
   self.assertEqual(r['compromiso_pendiente'],p['comprometido_acumulado']-p['ejecutado_acumulado'])
 def test_bayes_limites(self):
  for values in ((True,True,True),(False,False,False)):
   v=RiskNetwork().posterior(dict(zip(('low_execution','little_time','high_pending'),values)))['probabilidad']
   self.assertGreaterEqual(v,0);self.assertLessEqual(v,1)
 def test_presupuesto_cero(self):
  p=dict(self.data['partidas'][0],presupuesto_anual=0)
  with self.assertRaises(ValueError):evaluar_partida(p)
if __name__=='__main__':unittest.main()
