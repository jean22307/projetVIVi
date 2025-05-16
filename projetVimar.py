import requests  # bibliothèque pour faire des requêtes HTTP
from bs4 import BeautifulSoup  # bibliothèque pour parser le HTML
import json  # pour encoder et décoder des données JSON
from collections import defaultdict  # pour créer des dictionnaires avec valeurs par défaut
from concurrent.futures import ThreadPoolExecutor, as_completed  # pour exécuter des tâches en parallèle
import random  # pour sélectionner des éléments de façon aléatoire
import time  # pour gérer les délais d'attente
import os  # pour interagir avec le système de fichiers

BASE     = "https://olympics-statistics.com"  # URL de base du site à scraper
ALPHABET = [*"abcdefghijklmnopqrstuvwxyz", "special"]  # liste des pages alphabétiques à parcourir

# —————————————————————————————————————————
# Chargement et formatage des proxies
proxy_file = "proxies.txt"  # chemin vers le fichier contenant les proxies
if not os.path.isfile(proxy_file):  # vérifie que le fichier existe
    raise FileNotFoundError(f"Le fichier de proxies est introuvable : {proxy_file}")  # erreur si manquant

PROXIES = []  # liste pour stocker les URL de proxy
with open(proxy_file, encoding="utf-8") as f:  # ouvre le fichier en lecture
    for line in f:  # parcourt chaque ligne
        ip, port, user, pwd = line.strip().split(",")  # décompose la ligne en IP, port, user et mot de passe
        PROXIES.append(f"http://{user}:{pwd}@{ip}:{port}")  # construit l'URL de proxy et l'ajoute à la liste

def get_proxy():
    """Retourne une URL de proxy aléatoire, déjà au format attendu par requests."""
    proxy_url = random.choice(PROXIES)  # choisit un proxy au hasard
    print(f"→ Utilisation du proxy : {proxy_url}")  # affiche pour debug
    return proxy_url  # retourne l'URL sélectionnée

# —————————————————————————————————————————
# Parsing des médailles d'une page athlète
def parse_medals(soup):
    medals = []  # liste pour stocker les médailles trouvées
    for m in soup.select("div.top.m div.medaille.visible"):  # sélectionne les blocs de médailles visibles
        kind       = m.select_one("div.the-medal")["data-medal"]  # récupère le type numérique de la médaille
        medal_type = {"1":"gold","2":"silver","3":"bronze"}.get(kind,"unknown")  # convertit en chaîne
        sport      = m.select_one("div.m-sport").get_text(strip=True)  # sport associé
        ev         = m.select_one("a.m-event")  # conteneur de l'événement
        event      = ev.select_one("div.m-eventname").get_text(strip=True) if ev else None  # nom de l'épreuve
        date       = ev.select_one("div.m-event-am").get_text(strip=True)  if ev else None  # date de l'épreuve
        place      = ev.select_one("div.m-event-stadt").get_text(strip=True) if ev else None  # lieu de l'épreuve
        country    = m.select_one("img.f")["title"]  # pays de l'athlète pour la médaille
        medals.append({  # ajoute un dictionnaire pour chaque médaille
            "type":    medal_type,
            "sport":   sport,
            "event":   event,
            "date":    date,
            "place":   place,
            "country": country
        })
    return medals  # retourne la liste des médailles

# —————————————————————————————————————————
# Parsing d'une fiche athlète
def parse_athlete(url):
    proxy = get_proxy()  # obtient un proxy aléatoire
    proxies = {"http": proxy, "https": proxy}  # configure le proxy pour HTTP et HTTPS
    resp = requests.get(url, proxies=proxies, timeout=10)  # envoie la requête GET
    resp.raise_for_status()  # lève une erreur si le statut n'est pas 200
    soup = BeautifulSoup(resp.text, "html.parser")  # parse le HTML reçu

    fn = soup.select_one("div.vn")  # sélectionne le prénom
    ln = soup.select_one("div.nn")  # sélectionne le nom de famille
    name = {
        "first": fn.get_text(strip=True) if fn else None,  # extrait le texte du prénom
        "last":  ln.get_text(strip=True) if ln else None   # extrait le texte du nom
    }

    flag = soup.select_one("div.legende img")  # sélectionne l'image du drapeau
    country = flag["title"] if flag and flag.has_attr("title") else None  # récupère le pays

    return {
        "name":    name,  # retourne le nom complet
        "country": country,  # retourne le pays
        "medals":  parse_medals(soup)  # retourne la liste des médailles
    }

# —————————————————————————————————————————
# Récupération de toutes les URLs d'athlètes
def gather_links():
    links = []  # liste pour stocker les URLs
    for letter in ALPHABET:  # parcourt chaque lettre (et "special")
        page_url = f"{BASE}/olympic-athletes/{letter}"  # construit l'URL de la page
        proxy = get_proxy()  # sélectionne un proxy
        proxies = {"http": proxy, "https": proxy}  # configure le proxy
        r = requests.get(page_url, proxies=proxies, timeout=10)  # requête pour la page de lettres
        r.raise_for_status()  # vérifie le succès
        s = BeautifulSoup(r.text, "html.parser")  # parse le HTML
        for a in s.select("a.card.athlet.visible[href]"):  # sélectionne les liens d'athlètes visibles
            links.append(BASE + a["href"])  # ajoute l'URL complète à la liste
        time.sleep(0.5)  # pause pour éviter de surcharger le serveur
    return links  # retourne la liste de toutes les URLs

# —————————————————————————————————————————
# Fonction principale
def main():
    athlete_links = gather_links()  # récupère tous les liens d'athlètes
    print(f"Total athletes: {len(athlete_links)}")  # affiche le nombre total

    athletes   = []  # liste pour stocker les données des athlètes
    by_country = defaultdict(lambda: {"gold":0,"silver":0,"bronze":0})  # compte des médailles par pays
    by_c_sport = defaultdict(lambda: defaultdict(lambda: {"gold":0,"silver":0,"bronze":0}))  # compte par pays et sport

    # exécution parallèle des requêtes des athlètes
    with ThreadPoolExecutor(max_workers=10) as exe:
        futures = {exe.submit(parse_athlete, url): url for url in athlete_links}  # soumet les tâches
        for i, future in enumerate(as_completed(futures), 1):  # itère au fur et à mesure
            url = futures[future]  # URL liée à cette tâche
            try:
                ath = future.result()  # récupère le résultat
                athletes.append(ath)  # ajoute aux athlètes
                for m in ath["medals"]:  # pour chaque médaille
                    c  = m["country"]  # pays
                    t  = m["type"]  # type de médaille
                    sp = m["sport"]  # sport
                    by_country[c][t] += 1  # incrémente le compteur global
                    by_c_sport[c][sp][t] += 1  # incrémente le compteur par sport
                print(f"Processed {i}/{len(athlete_links)}  ({url})")  # statut
            except Exception as e:
                print(f"Failed {url}: {e}")  # affiche l'erreur

    output = {
        "athletes":             athletes,  # données complètes
        "by_country":           by_country,  # médailles par pays
        "by_country_and_sport": by_c_sport  # médailles par pays et sport
    }
    with open("full_stats.json", "w", encoding="utf-8") as f:  # ouvre le fichier de sortie
        json.dump(output, f, ensure_ascii=False, indent=2)  # écrit les données en JSON formaté
    print("Terminé → full_stats.json")  # message de fin

if __name__ == "__main__":
    main()  # lance la fonction principale si le script est exécuté directement

