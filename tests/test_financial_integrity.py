"""Verificaciones adicionales: aritmetica, contenido y seguridad, con datos sinteticos."""
import json
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from chatbot import BudgetBot, money
from reasoning import evaluar_partida

class TestFinancialIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bot = BudgetBot()
        cls.data = json.loads((ROOT/'data'/'presupuesto.json').read_text(encoding='utf-8'))

    def setUp(self):
        self.bot.pending = None

    def test_filas_mensuales_y_conciliacion(self):
        for p in self.data['partidas']:
            self.assertEqual(sum(p['real_mensual'].values()), p['ejecutado_acumulado'])
            self.assertGreaterEqual(p['presupuesto_anual'], p['comprometido_acumulado'])
            self.assertGreaterEqual(p['comprometido_acumulado'],p['ejecutado_acumulado'])

    def test_totales_globales(self):
        totals=self.bot._totals()
        self.assertEqual(totals,dict(presupuesto_anual=318000,ejecutado_acumulado=227400,comprometido_acumulado=274500))
        self.assertIn('USD 47,100.00',self.bot._overall('compromisos_pendientes',1)['text'])
        self.assertIn('71.51%',self.bot._overall('porcentaje_ejecucion',1)['text'])

    def test_cada_partida_calculo_y_saldos(self):
        for p in self.data['partidas']:
            with self.subTest(partida=p['id']):
                r=evaluar_partida(p,self.data['meses_cerrados'])
                self.assertAlmostEqual(r['ejecucion_pct'],round(p['ejecutado_acumulado']*100/p['presupuesto_anual'],2))
                self.assertEqual(r['saldo_sin_ejecutar'],p['presupuesto_anual']-p['ejecutado_acumulado'])
                self.assertEqual(r['saldo_sin_comprometer'],p['presupuesto_anual']-p['comprometido_acumulado'])
                self.assertEqual(r['compromiso_pendiente'],p['comprometido_acumulado']-p['ejecutado_acumulado'])

    def test_respuestas_numericas_por_partida(self):
        for p in self.data['partidas']:
            with self.subTest(partida=p['id']):
                self.bot.pending='presupuesto_asignado'
                r=self.bot.respond(p['id'])
                self.assertEqual(r['intent'],'presupuesto_asignado')
                self.assertIn(money(p['presupuesto_anual']),r['text'])
                self.bot.pending='presupuesto_ejecutado'
                r=self.bot.respond(p['id'])
                self.assertEqual(r['intent'],'presupuesto_ejecutado')
                self.assertIn(money(p['ejecutado_acumulado']),r['text'])
                self.bot.pending='saldo_disponible'
                r=self.bot.respond(p['id'])
                self.assertIn(money(p['presupuesto_anual']-p['comprometido_acumulado']),r['text'])
                self.assertIn(money(p['presupuesto_anual']-p['ejecutado_acumulado']),r['text'])

    def test_comparacion_ordenada(self):
        self.bot.pending=None
        r=self.bot.respond('qué partida ha ejecutado más')
        self.assertEqual(r['action'],'answer')
        ranking=sorted(self.data['partidas'],key=lambda p:p['ejecutado_acumulado']/p['presupuesto_anual'],reverse=True)
        positions=[r['text'].index(p['nombre']) for p in ranking]
        self.assertEqual(positions,sorted(positions))

    def test_comparacion_riesgo_y_advertencia(self):
        r=self.bot.respond('Compara el riesgo de todas las partidas')
        self.assertEqual(r['intent'],'riesgo_incumplimiento')
        self.assertEqual(r['action'],'answer')
        self.assertIn('85.54%',r['text'])
        self.assertIn('PR-102',r['text'])
        self.assertIn('PR-104',r['text'])
        self.assertIn('NO calibradas',r['text'])
        for p in self.data['partidas']:
            self.assertIn(p['id'],r['text'])

    def test_bloqueo_acciones_financieras(self):
        for phrase in ['autoriza un pago de 500','aprueba un pago de 100','modifica el presupuesto']:
            with self.subTest(consulta=phrase):
                r=self.bot.respond(phrase)
                self.assertEqual(r['action'],'handoff')
                self.assertNotIn('realizada',r['text'].lower())

    def test_partida_inexistente_no_inventa_cifras(self):
        r=self.bot.respond('presupuesto de PR-999')
        self.assertEqual(r['action'],'fallback')
        self.assertNotIn('USD ',r['text'])

    def test_error_semantico_documentado_sin_ocultarlo(self):
        r=self.bot.respond('cuánto se destinó a mantenimiento')
        self.assertEqual(r['intent'],'aclaracion')
        self.assertEqual(r['action'],'request_clarification')
        self.assertIn('asignado',r['text'])
        # En 3.3 se implementa aclaracion. La falla historica permanece en los registros 3.2.

if __name__=='__main__':unittest.main()
