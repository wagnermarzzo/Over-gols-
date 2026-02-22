import requests
import time
import threading
from flask import Flask
import os

# 🔐 Variáveis de ambiente
API_KEY = os.environ.get("0bde7c32f5msh1fdb43748126136p187dadjsn1ee65d62f516")  # X-RapidAPI-Key
CHAT_ID = os.environ.get("2055716345")  # Seu chat Telegram
TOKEN = os.environ.get("8536239572:AAEVHNxSnys_FYeXqL9P4ONsFPW7ZKr_faU")      # Seu token Telegram

LIVE_API = "https://api-football-v1.p.rapidapi.com/v3/fixtures?live=all"

app = Flask(__name__)

@app.route("/")
def home():
    return "🔥 Football Bot Online 🚀"

def enviar_sinal(mensagem):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensagem}
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print("Erro ao enviar Telegram:", e)

def analisar_jogo(minute, home_goals, away_goals, stats):
    total = home_goals + away_goals

    # Estatísticas
    home_shots = stats.get("home_shots_on_goal", 0)
    away_shots = stats.get("away_shots_on_goal", 0)
    home_possession = stats.get("home_possession", 50)
    away_possession = stats.get("away_possession", 50)
    home_attacks = stats.get("home_attacks", 0)
    away_attacks = stats.get("away_attacks", 0)

    # 🔹 Regras inteligentes
    # Over 0.5 FT se jogo parado há muito tempo
    if minute >= 70 and total == 0 and (home_attacks + away_attacks) >= 10:
        return "⚽ ENTRADA: OVER 0.5 FT - oportunidades em ambos"

    # Over 1.5 FT se 1 gol e ataque contínuo
    if 55 <= minute <= 65 and total == 1 and (home_attacks + away_attacks) >= 15:
        return "⚽ ENTRADA: OVER 1.5 FT - ataque forte"

    # Over 2.5 FT baseado em ataques e chutes
    if 60 <= minute <= 80 and total <= 2:
        # Time com maior pressão ofensiva
        if (home_shots + home_attacks) > (away_shots + away_attacks) and home_goals < 2:
            return "⚽ ENTRADA: OVER 2.5 FT - pressão HOME"
        elif (away_shots + away_attacks) > (home_shots + home_attacks) and away_goals < 2:
            return "⚽ ENTRADA: OVER 2.5 FT - pressão AWAY"

    # Possibilidade extra: posse acima de 60% + 1 gol → Over 1.5
    if total == 1 and (home_possession >= 60 or away_possession >= 60):
        return "⚽ ENTRADA: OVER 1.5 FT - posse alta"

    return None

def monitorar():
    enviados = set()
    print("🔥 Monitoramento API-Football iniciado...")

    while True:
        try:
            headers = {
                "X-RapidAPI-Key": API_KEY,
                "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
            }

            response = requests.get(LIVE_API, headers=headers, timeout=15)
            data = response.json()

            if "response" not in data:
                print("Nenhum jogo ao vivo no momento")
                time.sleep(60)
                continue

            for jogo in data["response"]:
                jogo_id = jogo["fixture"]["id"]
                minute = jogo["fixture"]["status"]["elapsed"]
                home = jogo["teams"]["home"]["name"]
                away = jogo["teams"]["away"]["name"]
                home_goals = jogo["goals"]["home"] or 0
                away_goals = jogo["goals"]["away"] or 0

                # Estatísticas avançadas
                stats = {}
                if jogo.get("statistics"):
                    for stat in jogo["statistics"]:
                        team_id = stat["team"]["id"]
                        # Home
                        if team_id == jogo["teams"]["home"]["id"]:
                            stats["home_attacks"] = stat.get("attacks", 0)
                            stats["home_shots_on_goal"] = stat.get("shots_on_goal", 0)
                            stats["home_possession"] = stat.get("possession", 50)
                        else:  # Away
                            stats["away_attacks"] = stat.get("attacks", 0)
                            stats["away_shots_on_goal"] = stat.get("shots_on_goal", 0)
                            stats["away_possession"] = stat.get("possession", 50)

                sinal = analisar_jogo(minute, home_goals, away_goals, stats)

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
