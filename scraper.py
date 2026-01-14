import time
import re
from playwright.sync_api import sync_playwright

URL = "https://www.fitp.it/Tornei/Ricerca-tornei"
SEEN_FILE = "seen_lomb.txt"


# ---------------------------------------------------------
# Estrae il numero "LOMB. xx" dal nome del torneo
# ---------------------------------------------------------
def extract_lomb_number(nome):
    m = re.search(r"LOMB\.\s*(\d+)", nome.upper())
    return int(m.group(1)) if m else None


# ---------------------------------------------------------
# Carica i codici LOMB già visti
# ---------------------------------------------------------
def load_seen_codes():
    try:
        with open(SEEN_FILE, "r") as f:
            return set(int(line.strip()) for line in f)
    except FileNotFoundError:
        return set()


# ---------------------------------------------------------
# Salva nuovi codici LOMB
# ---------------------------------------------------------
def save_seen_codes(codes):
    with open(SEEN_FILE, "a") as f:
        for c in codes:
            f.write(str(c) + "\n")


# ---------------------------------------------------------
# Scraping dei tornei filtrati e deduplicati
# ---------------------------------------------------------
def fetch_tournaments():
    with sync_playwright() as p:
        # Chromium headless (Render-friendly)
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # Carica pagina
        page.goto(URL, wait_until="networkidle")

        # Rimuovi banner iubenda
        page.evaluate("""
            const banner = document.querySelector('#iubenda-cs-banner');
            if (banner) banner.remove();
        """)

        # Attendi filtri
        page.wait_for_selector("#select-competitionType", timeout=15000)

        # Competizione = FITP
        page.select_option("#select-competitionType", value="1")
        page.evaluate("document.querySelector('#select-competitionType').dispatchEvent(new Event('change'))")
        time.sleep(0.5)

        # Stato = In programma
        page.select_option("#select_status", value="4")
        page.evaluate("document.querySelector('#select_status').dispatchEvent(new Event('change'))")
        time.sleep(0.5)

        # Regione = Lombardia
        page.select_option("#id_regioneSearch", label="Lombardia")
        page.evaluate("document.querySelector('#id_regioneSearch').dispatchEvent(new Event('change'))")

        # Attendi popolamento provincia
        for _ in range(40):
            options = page.locator("#id_provinciaSearch option").all_inner_texts()
            if any("Milano" in o for o in options):
                break
            time.sleep(0.25)

        # Provincia = Milano
        page.select_option("#id_provinciaSearch", label="Milano")
        page.evaluate("document.querySelector('#id_provinciaSearch').dispatchEvent(new Event('change'))")

        # Attendi aggiornamento Vue
        time.sleep(2)

        # Estrai tornei da Vue
        tornei = page.evaluate("app.tornei")

        browser.close()

    # Filtra solo Milano
    tornei_milano = [t for t in tornei if t.get("sigla_provincia") == "MI"]

    # Deduplica per GUID
    seen = set()
    unici = []
    for t in tornei_milano:
        guid = t.get("guid")
        if guid not in seen:
            seen.add(guid)
            unici.append(t)

    return unici


# ---------------------------------------------------------
# Rileva i tornei nuovi basandosi sul codice LOMB. xx
# ---------------------------------------------------------
def detect_new_tournaments(tornei):
    seen_codes = load_seen_codes()
    nuovi = []
    nuovi_codici = []

    for t in tornei:
        num = extract_lomb_number(t["nome_torneo"])
        if num is None:
            continue

        if num not in seen_codes:
            nuovi.append(t)
            nuovi_codici.append(num)

    if nuovi_codici:
        save_seen_codes(nuovi_codici)

    return nuovi


# ---------------------------------------------------------
# Formattazione leggibile del torneo
# ---------------------------------------------------------
def format_torneo(t):
    return f"{t['nome_torneo']} — {t['citta']} ({t['sigla_provincia']}) dal {t['data_inizio']} al {t['data_fine']}"