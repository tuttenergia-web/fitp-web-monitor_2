import time
import logging
import requests

from scraper import fetch_tournaments, detect_new_tournaments, format_torneo

# ---------------------------------------------------------
# LOGGING FORENSE
# ---------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logging.info(">>> AVVIO SCRIPT MAIN (PLAYWRIGHT + RENDER) <<<")

# ---------------------------------------------------------
# CONFIGURAZIONE TELEGRAM
# ---------------------------------------------------------

CHAT_ID = "6701954823"
BOT_TOKEN = "8567606681:AAECtRXD-ws0LP8kaIsgAQc9BEAjB2VewHU"

def invia_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": CHAT_ID,
            "text": msg,
            "parse_mode": "Markdown"
        }
        r = requests.post(url, json=payload, timeout=20)
        logging.info(f"Telegram status: {r.status_code}")
        return r.status_code == 200
    except Exception as e:
        logging.error(f"Errore Telegram: {e}")
        return False


# ---------------------------------------------------------
# LOOP PRINCIPALE
# ---------------------------------------------------------

POLLING_INTERVAL = 30  # secondi

def main():
    logging.info(">>> LOOP PRINCIPALE AVVIATO <<<")
    print("Avvio monitoraggio pagina FITP (Playwright)…")

    while True:
        try:
            logging.info(">>> FETCH TORNEI <<<")
            tornei = fetch_tournaments()
            logging.info(f"Tornei estratti: {len(tornei)}")

            nuovi = detect_new_tournaments(tornei)
            logging.info(f"Nuovi tornei rilevati: {len(nuovi)}")

            if nuovi:
                for t in nuovi:
                    msg = f"🎾 *Nuovo torneo rilevato*\n{format_torneo(t)}"
                    invia_telegram(msg)

        except Exception as e:
            logging.error(f"Errore nel ciclo principale: {e}")

        time.sleep(POLLING_INTERVAL)


if __name__ == "__main__":
    main()