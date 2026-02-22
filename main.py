import requests
import time
import os

# 🔐 Variáveis de ambiente
TOKEN = os.getenv("8536239572:AAEVHNxSnys_FYeXqL9P4ONsFPW7ZKr_faU")
CHAT_ID = os.getenv("2055716345")

LIVE_API = "https://www.thesportsdb.com/api/v1/json/3/livescore.php?s=Soccer"

def enviar_sinal(mensagem):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": mensagem
    }
    requests.post(url, data=payload)

def analisar_jogo(minute, home_goals, away_goals):
    total = home_goals + away_goals

    # Estratégia conservadora
    if minute >= 70 and total == 0:
        return "⚽ OVER 0.5 FT"

    if 55 <= minute <= 65 and total == 1:
        return "⚽ OVER 1.5 FT"

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

    while True:
        try:
            response = requests.get(LIVE_API)
            data = response.json()

            if not data or not data.get("events"):
                time.sleep(60)
                continue

            for jogo in data["events"]:
                jogo_id = jogo["idEvent"]
                home = jogo["strHomeTeam"]
                away = jogo["strAwayTeam"]
                home_goals = int(jogo["intHomeScore"] or 0)
                away_goals = int(jogo["intAwayScore"] or 0)
                status = jogo.get("strStatus")

                minute = extrair_minuto(status)

                if minute is None:
                    continue

                sinal = analisar_jogo(minute, home_goals, away_goals)

                if sinal and jogo_id not in enviados:
                    mensagem = (
                        f"{sinal}\n"
                        f"{home} x {away}\n"
                        f"Min: {minute}'\n"
                        f"Placar: {home_goals}x{away_goals}"
                    )
                    enviar_sinal(mensagem)
                    enviados.add(jogo_id)

        except Exception as e:
            print("Erro:", e)

        time.sleep(60)

if __name__ == "__main__":
    monitorar()
