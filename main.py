import requests
import time
import threading
from flask import Flask
import os

# 🔐 Seu token e chat id fixos
TOKEN = "8536239572:AAEVHNxSnys_FYeXqL9P4ONsFPW7ZKr_faU"
CHAT_ID = "2055716345"

LIVE_API = "https://www.thesportsdb.com/api/v1/json/3/livescore.php?s=Soccer"

app = Flask(__name__)


@app.route("/")
def home():
    return "🔥 Football Bot Online 🚀"


def enviar_sinal(mensagem):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": mensagem
    }
    try:
        requests.post(url, data=payload, timeout=10)
    except:
        pass


def analisar_jogo(minute, home_goals, away_goals):
    total = home_goals + away_goals

    if minute >= 70 and total == 0:
        return "⚽ ENTRADA: OVER 0.5 FT"

    if 55 <= minute <= 65 and total == 1:
        return "⚽ ENTRADA: OVER 1.5 FT"

    return None


def extrair_minuto(status_str):
    if not status_str:
        return None
    if "'" in status_str:
        try:
            return int(status_str.replace("'", "").strip())
        except:
            return None
    return None


def monitorar():
    enviados = set()
    print("🔥 Monitoramento iniciado...")

    while True:
        try:
            response = requests.get(LIVE_API, timeout=15)
            data = response.json()

            if not data or not data.get("events"):
                time.sleep(60)
                continue

            for jogo in data["events"]:
                jogo_id = jogo["idEvent"]
                home = jogo["strHomeTeam"]
                away = jogo["strAwayTeam"]
                home_goals = int(jogo.get("intHomeScore") or 0)
                away_goals = int(jogo.get("intAwayScore") or 0)
                status = jogo.get("strStatus")

                minute = extrair_minuto(status)
                if minute is None:
                    continue

                sinal = analisar_jogo(minute, home_goals, away_goals)

                if sinal and jogo_id not in enviados:
                    mensagem = (
                        f"{sinal}\n"
                        f"{home} x {away}\n"
                        f"Minuto: {minute}'\n"
                        f"Placar: {home_goals}x{away_goals}"
                    )
                    enviar_sinal(mensagem)
                    enviados.add(jogo_id)

        except Exception as e:
            print("Erro:", e)

        time.sleep(60)


if __name__ == "__main__":
    # 🔥 roda bot em thread separada
    thread = threading.Thread(target=monitorar)
    thread.daemon = True
    thread.start()

    # 🔥 abre porta correta do Render
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
