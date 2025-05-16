import requests
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from collections import defaultdict
from requests.adapters import HTTPAdapter, Retry

BASE_URL     = "https://olympics-statistics.com"
SPORTS_PAGE  = "/olympic-sports"
OUTPUT_JSON  = "full_sport_by_country.json"
MEDAL_LABELS = {"1": "gold", "2": "silver", "3": "bronze"}

# --- Configuration d'une session requests avec retry ---
session = requests.Session()
retries = Retry(
    total=5,
    backoff_factor=0.5,
    status_forcelist=[500, 502, 503, 504]
)
adapter = HTTPAdapter(max_retries=retries)
session.mount("https://", adapter)
session.mount("http://", adapter)


def get_all_sports():
    """Retourne la liste des sports avec leur URL de page."""
    try:
        resp = session.get(urljoin(BASE_URL, SPORTS_PAGE))
        resp.raise_for_status()
    except Exception as e:
        print(f"⚠ Impossible de charger la liste des sports : {e}")
        return []
    soup = BeautifulSoup(resp.text, "html.parser")

    sports = []
    for a in soup.select("a.card.sport.visible"):
        name = a.select_one("div.bez").get_text(strip=True)
        href = a["href"]
        sports.append({
            "sport": name,
            "url": urljoin(BASE_URL, href)
        })
    return sports


def get_medals_by_country(sport_url):
    """Pour une page de sport, renvoie la liste des médailles par pays."""
    try:
        resp = session.get(sport_url)
        resp.raise_for_status()
    except Exception as e:
        print(f"  ⚠ Échec chargement {sport_url}: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    container = soup.select_one('div.top[data-which="n"]')
    if not container:
        return []

    result = []
    for card in container.select("div.card.nation.visible"):
        img = card.select_one("img.f")
        country = img["title"].strip() if img and img.has_attr("title") else None

        counts = {"gold": 0, "silver": 0, "bronze": 0}
        for medal_div in card.select("div.medals div.the-medal"):
            code = medal_div["data-medal"]
            medal_type = MEDAL_LABELS.get(code)
            # le <span class="mal">…</span> peut être avant ou après dans le DOM
            qty_tag = medal_div.find_previous_sibling("span.mal") or medal_div.find_next_sibling("span.mal")
            try:
                qty = int(qty_tag.get_text(strip=True))
            except Exception:
                qty = 0
            if medal_type:
                counts[medal_type] = qty

        if country:
            result.append({"country": country, **counts})
    return result


def main():
    sports = get_all_sports()
    if not sports:
        print("Aucun sport à traiter. Fin.")
        return

    # structure : { pays: { sport: {gold, silver, bronze}, ... }, ... }
    by_country_sport = defaultdict(lambda: defaultdict(lambda: {"gold": 0, "silver": 0, "bronze": 0}))

    for sp in sports:
        sport_name = sp["sport"]
        print(f"→ Traitement de {sport_name}…")
        medals_list = get_medals_by_country(sp["url"])
        for entry in medals_list:
            country = entry["country"]
            # on crée/écrase la ligne pour ce sport
            by_country_sport[country][sport_name] = {
                "gold":   entry["gold"],
                "silver": entry["silver"],
                "bronze": entry["bronze"]
            }

    # transformer en dict normal pour le JSON
    output = {country: dict(sports) for country, sports in by_country_sport.items()}

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Résultats enregistrés dans {OUTPUT_JSON}")


if __name__ == "__main__":
    main()
