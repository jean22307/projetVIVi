# projetVIVi
projetvivi
Ce document récapitule l'ensemble des étapes réalisées dans le cadre du projet de collecte et visualisation des données des Jeux Olympiques.

1. Collecte des données (Scraping)

Gestion des proxys

Fichiers : proxies.txt, proxi100.txt

Chargement des proxys dans les scripts Python pour répartir les requêtes et éviter de surcharger le serveur, sans recourir à un grand nombre de threads.

Scraping des nations

Script : scpritNation.py

Point d'entrée : page https://olympics-statistics.com/nations

Extraction des  pour obtenir la liste des pays et leurs liens.

Génération de medals_by_country.json (total médailles par pays).

Scraping des sports

Script : scrpitsport.py

Point d'entrée : page https://olympics-statistics.com/olympic-sports

Pour chaque sport, récupération de la section Top Nations (div.top[data-which="n"]).

Extraction du nombre de médailles or/argent/bronze par pays.

Génération de full_sport_by_country.json (médailles par pays, par sport).

Scraping complet (optionnel)

Script : projetVimar.py

Extraction détaillée : athlètes, pays, sports et médailles.

Sortie globale full_stats.json (athlètes, par pays, par sport).

2. Préparation des données

Nettoyage et transformation JSON.

Consolidation des structures :

{ "pays": { "sport": { gold, silver, bronze }, ... }, ... }

{ "pays": { gold, silver, bronze } } pour certaines visualisations.

3. Visualisation

Carte choroplèthe

Fichier : index.html, script.js

Utilisation de Highcharts Maps

Affiche la répartition des médailles par pays et par type sur une carte mondiale.

Bar chart

Fichier : script2.js

Affiche le Top 4 des nations par nombre total de médailles.

Packed Bubble (Cluster Pays par Sport)

Fichier : script3.js

Configuration Highcharts Packed Bubble

Séries regroupées par sport, bulles dimensionnées par le total de médailles d’un pays dans chaque sport.

