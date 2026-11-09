"""Interfaz de consola de PresupuestoBot (datos sintéticos)."""
from chatbot import BudgetBot

def main():
    bot=BudgetBot()
    print('PresupuestoBot EC | Comercial Delta S.A. (FICTICIA) | Corte: octubre 2026')
    print('No autoriza pagos ni decisiones financieras. Escribe salir para cerrar.')
    while True:
        try: question=input('\nUsuario: ')
        except (EOFError,KeyboardInterrupt): break
        response=bot.respond(question)
        print('Bot:',response['text'])
        print(f"[intencion={response['intent']} | accion={response['action']} | confianza_no_calibrada={response['confidence']}]")
        if response['action']=='close': break
if __name__=='__main__': main()
