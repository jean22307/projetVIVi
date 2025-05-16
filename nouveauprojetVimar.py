import requests
from bs4 import BeautifulSoup
import json
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import random
import time
import os

BASE     = "https://olympics-statistics.com"
ALPHABET = [*"abcdefghijklmnopqrstuvwxyz", "special"]

# —————————————————————————————————————————
# Chargement et formatage des proxies
proxy_file = "proxies.txt"
if not os.path.isfile(proxy_file):
    raise FileNotFoundError(f"Le fichier de proxies est introuvable : {proxy_file}")

PROXIES = []
with open(proxy_file, encoding="utf-8") as f:
    for line in f:
        ip, port, user, pwd = line.strip().split(",")
        PROXIES.append(f"http://{user}:{pwd}@{ip}:{port}")

def get_proxy():
    """Tire un proxy valide au hasard, ou None si plus aucun proxy ne fonctionne."""
    while PROXIES:
        proxy = random.choice(PROXIES)
        proxies = {"http": proxy, "https": proxy}
        try:
            # Test rapide : simple HEAD sur la page d'accueil
            resp = requests.head(BASE, proxies=proxies, timeout=5)
            resp.raise_for_status()
            return proxy
        except Exception as e:
            print(f"→ Proxy invalide ou rejeté ({e}), suppression de la liste : {proxy}")
            PROXIES.remove(proxy)
    print("→ Aucun proxy valide, on va essayer en direct.")
    return None

# —————————————————————————————————————————
# Parsing des médailles d'une page athlète
def parse_medals(soup):
    medals = []
    for m in soup.select("div.top.m div.medaille.visible"):
        kind       = m.select_one("div.the-medal")["data-medal"]
        medal_type = {"1":"gold","2":"silver","3":"bronze"}.get(kind,"unknown")
        sport      = m.select_one("div.m-sport").get_text(strip=True)
        ev         = m.select_one("a.m-event")
        event      = ev.select_one("div.m-eventname").get_text(strip=True) if ev else None
        date       = ev.select_one("div.m-event-am").get_text(strip=True)  if ev else None
        place      = ev.select_one("div.m-event-stadt").get_text(strip=True) if ev else None
        country    = m.select_one("img.f")["title"]
        medals.append({
            "type":    medal_type,
            "sport":   sport,
            "event":   event,
            "date":    date,
            "place":   place,
            "country": country
        })
    return medals

# —————————————————————————————————————————
# Parsing d'une fiche athlète avec retry/fallback proxy
def parse_athlete(url, max_retries=3):
    for attempt in range(max_retries):
        proxy = get_proxy()
        proxies = {"http": proxy, "https": proxy} if proxy else None
        try:
            print(f"→ Tentative #{attempt+1} pour {url} via {proxy or 'direct'}")
            resp = requests.get(url, proxies=proxies, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            fn = soup.select_one("div.vn")
            ln = soup.select_one("div.nn")
            name = {
                "first": fn.get_text(strip=True) if fn else None,
                "last":  ln.get_text(strip=True) if ln else None
            }
            flag = soup.select_one("div.legende img")
            country = flag["title"] if flag and flag.has_attr("title") else None
            return {
                "name":    name,
                "country": country,
                "medals":  parse_medals(soup)
            }
        except requests.exceptions.ProxyError as e:
            print(f"→ Erreur proxy : {e}. On retire ce proxy et on réessaie.")
            if proxy in PROXIES:
                PROXIES.remove(proxy)
        except Exception as e:
            # pour d’autres erreurs (timeout, 5xx…), on réessaie quand même
            print(f"→ Erreur ({e}), retry...")
        time.sleep(1)
    # Si toutes les tentatives échouent, on lève l’erreur
    raise RuntimeError(f"Impossible de récupérer la fiche {url}")

# —————————————————————————————————————————
# Récupération de toutes les URLs d'athlètes (même logique de retry)
def gather_links():
    links = []
    for letter in ALPHABET:
        page_url = f"{BASE}/olympic-athletes/{letter}"
        for attempt in range(3):
            proxy = get_proxy()
            proxies = {"http": proxy, "https": proxy} if proxy else None
            try:
                print(f"→ Fetch {page_url} (lettre '{letter}'), essai #{attempt+1}")
                r = requests.get(page_url, proxies=proxies, timeout=10)
                r.raise_for_status()
                s = BeautifulSoup(r.text, "html.parser")
                for a in s.select("a.card.athlet.visible[href]"):
                    links.append(BASE + a["href"])
                break
            except requests.exceptions.ProxyError as e:
                print(f"→ ProxyError: {e}, on retire le proxy et réessaie.")
                if proxy in PROXIES:
                    PROXIES.remove(proxy)
            except Exception as e:
                print(f"→ Erreur lors du fetch de {page_url} : {e}")
            time.sleep(0.5)
        else:
            print(f"⚠️ Échec pour la page {page_url}, passage à la lettre suivante.")
    return links

# —————————————————————————————————————————
# Fonction principale
def main():
    athlete_links = gather_links()
    print(f"Total athletes: {len(athlete_links)}")

    athletes   = []
    by_country = defaultdict(lambda: {"gold":0,"silver":0,"bronze":0})
    by_c_sport = defaultdict(lambda: defaultdict(lambda: {"gold":0,"silver":0,"bronze":0}))

    with ThreadPoolExecutor(max_workers=10) as exe:
        futures = {exe.submit(parse_athlete, url): url for url in athlete_links}
        for i, future in enumerate(as_completed(futures), 1):
            url = futures[future]
            try:
                ath = future.result()
                athletes.append(ath)
                for m in ath["medals"]:
                    c  = m["country"]
                    t  = m["type"]
                    sp = m["sport"]
                    by_country[c][t] += 1
                    by_c_sport[c][sp][t] += 1
                print(f"Processed {i}/{len(athlete_links)}  ({url})")
            except Exception as e:
                print(f"Failed {url}: {e}")

    output = {
        "athletes":             athletes,
        "by_country":           by_country,
        "by_country_and_sport": by_c_sport
    }
    with open("full_statsnew.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print("Terminé → full_statsnew.json")

if __name__ == "__main__":
    main()
