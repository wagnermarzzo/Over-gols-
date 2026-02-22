import requests
import time
import threading
from flask import Flask
import os

# 🔐 Variáveis de ambiente
API_FOOTBALL_KEY = "1447e13cd8b5ee372726a0da627fd4f1"
LIVE_API_FOOTBALL = "https://v3.football.api-sports.io/fixtures?live=all"

SPORTDB_KEY = "k8eo2oAyRRCdJPfS1W9wp10JI3iHaxvixbMk0VcY"
SPORTDB_BASE = "https://www.thesportsdb.com/api/v1/json"

CHAT_ID = "2055716345"
TOKEN = "8536239572:AAEVHNxSnys_FYeXqL9P4ONsFPW7ZKr_faU"

app = Flask(__name__)
jogos_ativos = []

@app.route("/")
def home():
    return "🔥 Football Bot Online 🚀"

def enviar_sinal(mensagem):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensagem, "parse_mode": "HTML"}
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

    # Lógica de sinais (igual antes)
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

def buscar_info_sportdb(time):
    try:
        url = f"{SPORTDB_BASE}/{SPORTDB_KEY}/searchteams.php?t={time}"
        data = requests.get(url, timeout=10).json()
        if "teams" in data and data["teams"]:
            t = data["teams"][0]
            return {
                "nome": t.get("strTeam", time),
                "estadio": t.get("strStadium", "N/D"),
                "logo": t.get("strTeamBadge", ""),
                "website": t.get("strWebsite", "N/D"),
                "ultimos_resultados": t.get("strForm", "N/D")
            }
        return {"nome": time, "estadio": "N/D", "logo": "", "website": "N/D", "ultimos_resultados": "N/D"}
    except:
        return {"nome": time, "estadio": "N/D", "logo": "", "website": "N/D", "ultimos_resultados": "N/D"}

def enviar_sinal_inicial():
    """Busca o primeiro jogo disponível e envia sinal de aposta real"""
    try:
        headers = {"x-apisports-key": API_FOOTBALL_KEY}
        response = requests.get(LIVE_API_FOOTBALL, headers=headers, timeout=10)
        data = response.json()

        if "response" in data and data["response"]:
            jogo = data["response"][0]  # pega o primeiro jogo ao vivo
            minute = jogo["fixture"]["status"]["elapsed"] or 0
            home = jogo["teams"]["home"]["name"]
            away = jogo["teams"]["away"]["name"]
            home_goals = jogo["goals"]["home"] or 0
            away_goals = jogo["goals"]["away"] or 0

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

            home_info = buscar_info_sportdb(home)
            away_info = buscar_info_sportdb(away)

            sinal = analisar_jogo(minute, home_goals, away_goals, stats)
            if not sinal:
                sinal = "⚽ ENTRADA: OVER 1.5 FT - sinal inicial automático (teste real)"

            mensagem = (
                f"{sinal}\n"
                f"<b>{home_info['nome']} x {away_info['nome']}</b>\n"
                f"Minuto: {minute}' | Placar: {home_goals}x{away_goals}\n\n"
                f"🏟 Estádio Home: {home_info['estadio']} | 🌐 {home_info['website']}\n"
                f"🏟 Estádio Away: {away_info['estadio']} | 🌐 {away_info['website']}\n\n"
                f"📊 Últimos resultados:\n"
                f"{home_info['ultimos_resultados']} | {away_info['ultimos_resultados']}\n"
                f"🖼 Logos: {home_info['logo']} | {away_info['logo']}"
            )
            enviar_sinal(mensagem)
        else:
            # Nenhum jogo ao vivo, envia sinal de teste fixo
            enviar_sinal(
                "⚽ ENTRADA: OVER 1.5 FT - nenhum jogo ao vivo disponível, sinal inicial de teste."
            )
    except Exception as e:
        print("Erro ao enviar sinal inicial:", e)
        enviar_sinal(
            "⚽ ENTRADA: OVER 1.5 FT - erro ao buscar jogos, sinal inicial de teste."
        )

def monitorar():
    enviados = set()
    global jogos_ativos
    print("🔥 Monitoramento iniciado (2º tempo)")

    while True:
        try:
            headers = {"x-apisports-key": API_FOOTBALL_KEY}
            response = requests.get(LIVE_API_FOOTBALL, headers=headers, timeout=15)
            data = response.json()
            jogos_ativos = []

            if "response" not in data or not data["response"]:
                print("Nenhum jogo ao vivo no momento")
                time.sleep(15)
                continue

            for jogo in data["response"]:
                minute = jogo["fixture"]["status"]["elapsed"] or 0
                if minute < 45:
                    continue  # só 2º tempo

                jogo_id = jogo["fixture"]["id"]
                home = jogo["teams"]["home"]["name"]
                away = jogo["teams"]["away"]["name"]
                home_goals = jogo["goals"]["home"] or 0
                away_goals = jogo["goals"]["away"] or 0

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

                home_info = buscar_info_sportdb(home)
                away_info = buscar_info_sportdb(away)

                sinal = analisar_jogo(minute, home_goals, away_goals, stats)
                if sinal and jogo_id not in enviados:
                    mensagem = (
                        f"{sinal}\n"
                        f"<b>{home_info['nome']} x {away_info['nome']}</b>\n"
                        f"Minuto: {minute}' | Placar: {home_goals}x{away_goals}\n\n"
                        f"🏟 Estádio Home: {home_info['estadio']} | 🌐 {home_info['website']}\n"
                        f"🏟 Estádio Away: {away_info['estadio']} | 🌐 {away_info['website']}\n\n"
                        f"📊 Últimos resultados:\n"
                        f"{home_info['ultimos_resultados']} | {away_info['ultimos_resultados']}\n"
                        f"🖼 Logos: {home_info['logo']} | {away_info['logo']}"
                    )
                    enviar_sinal(mensagem)
                    enviados.add(jogo_id)

                jogos_ativos.append(f"{home} x {away} ({minute}') Placar {home_goals}x{away_goals}")

            time.sleep(15)

        except Exception as e:
            print("Erro:", e)
            time.sleep(15)

def status_periodico():
    global jogos_ativos
    while True:
        mensagem = f"📊 Bot ativo! {len(jogos_ativos)} jogo(s) do 2º tempo:\n"
        if jogos_ativos:
            mensagem += "\n".join(jogos_ativos)
        else:
            mensagem += "Nenhum jogo no momento."
        enviar_sinal(mensagem)
        time.sleep(900)  # 15 minutos

if __name__ == "__main__":
    # 🔹 Envia sinal inicial usando um jogo real da API-Football
    enviar_sinal_inicial()

    # 🔹 Inicia threads de monitoramento e status periódico
    thread_monitor = threading.Thread(target=monitorar)
    thread_monitor.daemon = True
    thread_monitor.start()

    thread_status = threading.Thread(target=status_periodico)
    thread_status.daemon = True
    thread_status.start()

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
