import os
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# --- Constantes ---
BASE_URL      = "https://olympics-statistics.com"
NATIONS_FILE  = "nations.html"           # Optionnel : si présent, on lira ce fichier
NATIONS_PAGE  = "/nations"                # Sinon on fera une requête HTTP
JSON_OUTPUT   = "fullStat_nation.json"
MEDAL_LABELS  = {"1": "gold", "2": "silver", "3": "bronze"}

def load_soup(path, remote_path):
    """
    Essaie de charger le HTML depuis `path` local.
    Si le fichier n'existe pas, fait une requête GET sur remote_path.
    """
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as f:
            return BeautifulSoup(f.read(), "html.parser")
    else:
        url = urljoin(BASE_URL, remote_path)
        resp = requests.get(url)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "html.parser")

def get_countries(soup):
    """Extrait la liste (nom, URL absolue) pour chaque nation."""
    countries = []
    for a in soup.select("a.card.nation.visible"):
        name = a.select_one("div.bez").get_text(strip=True)
        href = a.get("href")
        countries.append((name, urljoin(BASE_URL, href)))
    return countries

def get_medal_counts(country_url):
    """Scrape les totaux gold/silver/bronze pour un pays donné."""
    resp = requests.get(country_url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    counts = {"gold": 0, "silver": 0, "bronze": 0}
    teaser = soup.select_one("div.rnd.teaser")
    if teaser:
        for block in teaser.select("div:has(div.the-medal)"):
            medal_div = block.select_one("div.the-medal")
            code      = medal_div["data-medal"]
            key       = MEDAL_LABELS.get(code)
            try:
                qty = int(block.select_one("span.mal").get_text(strip=True))
            except Exception:
                qty = 0
            if key:
                counts[key] = qty
    return counts

def main():
    # 1) Charge nations depuis fichier local ou HTTP
    soup = load_soup(NATIONS_FILE, NATIONS_PAGE)

    # 2) Extrait la liste des pays
    countries = get_countries(soup)
    if not countries:
        print("⚠ Aucun bloc de nation trouvé.")
        return

    # 3) Scraping pour chaque pays
    results = []
    for name, url in countries:
        try:
            counts = get_medal_counts(url)
        except Exception as e:
            print(f"⚠ Échec pour {name} ({url}): {e}")
            counts = {"gold": 0, "silver": 0, "bronze": 0}
        entry = {"country": name, **counts}
        results.append(entry)
        print(f"✔ {name}: {counts}")

    # 4) Écriture du JSON
    with open(JSON_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n✅ Données enregistrées dans « {JSON_OUTPUT} »")

if __name__ == "__main__":
    main()
