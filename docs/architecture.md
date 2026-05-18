# Architecture du projet

Le projet suit une architecture simple de POC, avec une séparation claire entre ingestion, transformation, contrôle qualité et restitution.

## Chaîne de traitement

1. Les fichiers RH, sport et règles métier sont chargés dans PostgreSQL `raw`.
2. Les activités sportives simulées sont publiées dans Redpanda puis consommées par le pipeline.
3. dbt transforme les données en couches `bronze`, `silver` et `gold`.
4. `Great Expectations` et `dbt test` contrôlent la qualité.
5. Tableau exploite les tables métier et Grafana les vues de monitoring.

## Couches de données

### Raw

- données sources chargées sans transformation forte
- stockage des événements consommés depuis Redpanda

### Bronze

- standardisation des données brutes
- historisation des règles métier
- version courante et historique des paramètres

### Silver

- nettoyage et enrichissement des salariés et activités
- normalisation des transports
- contrôle de distance et consolidation des données

### Gold

- calcul des éligibilités
- KPI RH et finance
- timeline des avantages
- table de cartographie salariés

## Points importants

- Le géocodage domicile est simulé localement et de manière déterministe.
- Les règles métier sont versionnées pour permettre le rejeu.
- Airflow orchestre les étapes, mais la logique métier reste portée par dbt et les scripts Python.
