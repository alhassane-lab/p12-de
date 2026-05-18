# Choix techniques

## Pourquoi PostgreSQL

PostgreSQL suffit pour un POC, s'intègre bien avec dbt et un outil BI comme Tableau, et simplifie la démonstration locale.

## Pourquoi Redpanda

Redpanda apporte un vrai pattern streaming compatible Kafka, mais plus léger à exécuter localement qu'une stack Kafka complète.

## Pourquoi YAML pour les règles

Le YAML est plus lisible et plus naturel qu'un CSV pour du paramétrage métier. Dans ce projet, `business_rules.yaml` est la source de vérité, puis un loader Python charge ces règles dans PostgreSQL pour que dbt puisse les consommer proprement en SQL.

## Pourquoi dbt

dbt impose une séparation saine :
- Python pour l'ingestion et la collecte ;
- SQL versionné pour les règles métier et la transformation ;
- tests intégrés et documentation des modèles.

## Pourquoi Bronze / Silver / Gold

Cette structuration répond directement au besoin de :
- traçabilité ;
- qualité ;
- auditabilité ;
- rejeu historique lors d'un changement des règles RH.

## Pourquoi un géocodage simulé

Le cas métier demande une règle de distance, mais aucune API géographique n'est imposée. Pour garder un POC autonome et reproductible, les coordonnées domicile sont dérivées de manière déterministe depuis l'adresse. Le mécanisme est documenté et facilement remplaçable.
