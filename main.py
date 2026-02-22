import requests
import time
import threading
from flask import Flask
import os

# 🔐 Variáveis de ambiente
API_KEY = "0bde7c32f5msh1fdb43748126136p187dadjsn1ee65d62f516"  # X-RapidAPI-Key
CHAT_ID = "2055716345"  # Seu chat Telegram
TOKEN = "8536239572:AAEVHNxSnys_FYeXqL9P4ONsFPW7ZKr_faU"      # Seu token Telegram

LIVE_API = "https://api-football-v1.p.rapidapi.com/v3/fixtures?live=all"

app = Flask(__name__)

# 🔹 Lista global para acompanhar jogos ao vivo
jogos_ativos = []

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

    home_shots = stats.get("home_shots_on_goal", 0)
    away_shots = stats.get("away_shots_on_goal", 0)
    home_possession = stats.get("home_possession", 50)
    away_possession = stats.get("away_possession", 50)
    home_attacks = stats.get("home_attacks", 0)
    away_attacks = stats.get("away_attacks", 0)

    if minute >= 70 and total == 0 and (home_attacks + away_attacks) >= 10:
        return "⚽ ENTRADA: OVER 0.5 FT - oportunidades em ambos"

    if 55 <= minute <= 65 and total == 1 and (home_attacks + away_attacks) >= 15:
        return "⚽ ENTRADA: OVER 1.5 FT - ataque forte"

    if 60 <= minute <= 80 and total <= 2:
        if (home_shots + home_attacks) > (away_shots + away_attacks) and home_goals < 2:
            return "⚽ ENTRADA: OVER 2.5 FT - pressão HOME"
        elif (away_shots + away_attacks) > (home_shots + home_attacks) and away_goals < 2:
            return "⚽ ENTRADA: OVER 2.5 FT - pressão AWAY"

    if total == 1 and (home_possession >= 60 or away_possession >= 60):
        return "⚽ ENTRADA: OVER 1.5 FT - posse alta"

    return None

def monitorar():
    enviados = set()
    global jogos_ativos
    print("🔥 Monitoramento API-Football iniciado...")

    while True:
        try:
            headers = {
                "X-RapidAPI-Key": API_KEY,
                "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
            }

            response = requests.get(LIVE_API, headers=headers, timeout=15)
            data = response.json()

            jogos_ativos = []  # limpa lista a cada rodada

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

                # Adiciona à lista de jogos ativos
                jogos_ativos.append(f"{home} x {away} ({minute}')")

                stats = {}
                if jogo.get("statistics"):
                    for stat in jogo["statistics"]:
                        team_id = stat["team"]["id"]
                        if team_id == jogo["teams"]["home"]["id"]:
                            stats["home_attacks"] = stat.get("attacks", 0)
                            stats["home_shots_on_goal"] = stat.get("shots_on_goal", 0)
                            stats["home_possession"] = stat.get("possession", 50)
                        else:
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

def status_periodico():
    global jogos_ativos
    while True:
        mensagem = f"📊 Bot ativo! {len(jogos_ativos)} jogo(s) ao vivo:\n"
        if jogos_ativos:
            mensagem += "\n".join(jogos_ativos)
        else:
            mensagem += "Nenhum jogo no momento."
        enviar_sinal(mensagem)
        time.sleep(900)  # 15 minutos

if __name__ == "__main__":
    thread_monitor = threading.Thread(target=monitorar)
    thread_monitor.daemon = True
    thread_monitor.start()

    thread_status = threading.Thread(target=status_periodico)
    thread_status.daemon = True
    thread_status.start()

    # Mensagem inicial
    enviar_sinal("🤖 Bot de Football iniciado e online! 🚀")

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
