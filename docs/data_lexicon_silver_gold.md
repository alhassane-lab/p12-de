# Lexique des données - Couches Silver et Gold

Ce document présente le lexique des données pour les couches `silver` et `gold` du projet.

Objectifs :
- comprendre à quoi sert chaque table ;
- connaître le grain de chaque jeu de données ;
- savoir quels champs utiliser pour l'analyse métier et le dashboard ;
- faciliter la soutenance et la prise en main du modèle analytique.

## 1. Rappel de la logique des couches

### Silver

La couche `silver` contient les données nettoyées, normalisées et enrichies.

On y applique :
- le typage ;
- la gestion des doublons ;
- la validation de cohérence ;
- les enrichissements techniques et métier de base.

### Gold

La couche `gold` contient les données prêtes à être consommées par les outils de restitution.

On y trouve :
- les règles d'éligibilité ;
- les KPI ;
- les tables de pilotage ;
- les tables de qualité ;
- les sorties prêtes pour Tableau.

## 2. Lexique des tables Silver

## `sil_employees`

### Rôle

Table de référence salarié nettoyée et enrichie avec la distance domicile-bureau et les indicateurs de transport sportif.

### Grain

1 ligne = 1 salarié

### Champs principaux

- `employee_id`
  - identifiant unique du salarié
- `last_name`
  - nom du salarié
- `first_name`
  - prénom du salarié
- `full_name`
  - nom complet reconstitué
- `birth_date`
  - date de naissance typée
- `hire_date`
  - date d'embauche typée
- `business_unit`
  - unité métier ou département
- `gross_salary`
  - salaire annuel brut
- `contract_type`
  - type de contrat
- `cp_days`
  - nombre de jours de congés
- `home_address`
  - adresse domicile déclarée
- `transport_mode`
  - mode de transport normalisé
- `home_lat`
  - latitude domicile pseudo-géocodée
- `home_lon`
  - longitude domicile pseudo-géocodée
- `office_lat`
  - latitude du bureau
- `office_lon`
  - longitude du bureau
- `distance_km_to_office`
  - distance calculée domicile-bureau
- `is_transport_mode_sportive`
  - indicateur booléen : mode de transport sportif ou non
- `is_distance_rule_valid`
  - indicateur booléen : distance compatible avec les règles RH

### Utilité métier

Cette table sert de base au calcul de la prime sportive.

## `sil_sport_activities`

### Rôle

Table des activités sportives consommées depuis Redpanda, nettoyées et validées.

### Grain

1 ligne = 1 activité sportive

### Champs principaux

- `activity_id`
  - identifiant unique de l'activité
- `employee_id`
  - salarié concerné
- `activity_type`
  - type d'activité : run, ride, walk, hike, swim...
- `activity_date`
  - date de l'activité
- `distance_km`
  - distance en kilomètres
- `duration_min`
  - durée de l'activité en minutes
- `calories_burned`
  - calories estimées
- `source_system`
  - source technique de l'événement
- `event_ts`
  - timestamp d'événement
- `is_valid_activity`
  - booléen indiquant si l'activité passe les règles minimales de cohérence
- `slack_message_text`
  - message Slack simulé dérivé de l'activité

### Utilité métier

Cette table sert à :
- compter les activités sur 12 mois ;
- calculer les jours bien-être ;
- alimenter la restitution sur l'engagement sportif.

## `sil_sport_declarations`

### Rôle

Table des pratiques sportives déclaratives, dédupliquées au niveau salarié.

### Grain

1 ligne = 1 salarié

### Champs principaux

- `employee_id`
  - identifiant du salarié
- `declared_sport`
  - sport déclaré dans le fichier source

### Utilité métier

Cette table apporte une information déclarative complémentaire, utile pour l'analyse mais non déterminante seule pour l'éligibilité.

## `sil_employee_activity_yearly`

### Rôle

Table d'agrégation annuelle glissante des activités sportives.

### Grain

1 ligne = 1 salarié

### Champs principaux

- `employee_id`
  - identifiant du salarié
- `activity_year`
  - année de référence
- `activity_count_12m`
  - nombre d'activités sur les 12 derniers mois
- `sport_days_count`
  - nombre de jours distincts avec activité sportive
- `last_activity_date`
  - dernière date d'activité connue

### Utilité métier

Cette table est la base du calcul des jours bien-être.

## `sil_employee_activity_joined`

### Rôle

Table de consolidation salarié + activité + pratique déclarative.

### Grain

1 ligne = 1 salarié

### Champs principaux

- `employee_id`
  - identifiant salarié
- `full_name`
  - nom complet
- `business_unit`
  - BU
- `gross_salary`
  - salaire brut
- `transport_mode`
  - mode de transport
- `distance_km_to_office`
  - distance domicile-bureau
- `is_transport_mode_sportive`
  - booléen
- `is_distance_rule_valid`
  - booléen
- `declared_sport`
  - sport déclaré
- `activity_count_12m`
  - total d'activités sur 12 mois
- `sport_days_count`
  - nombre de jours sportifs
- `last_activity_date`
  - dernière activité connue

### Utilité métier

C'est la table pivot métier de la couche `silver`.

## 3. Lexique des tables Gold

## `gold_eligible_sport_bonus`

### Rôle

Table finale d'éligibilité à la prime sportive.

### Grain

1 ligne = 1 salarié

### Champs principaux

- `employee_id`
  - identifiant salarié
- `reference_year`
  - année de référence du calcul
- `full_name`
  - nom complet
- `business_unit`
  - BU
- `gross_salary`
  - salaire annuel brut
- `bonus_rate`
  - taux appliqué
- `bonus_amount`
  - montant théorique de la prime
- `transport_mode`
  - mode de transport retenu
- `distance_km_to_office`
  - distance utilisée dans la règle
- `eligibility_status`
  - booléen : éligible ou non
- `eligibility_reason`
  - raison métier : `eligible`, `transport_non_sportif`, `distance_hors_regle`
- `rule_version`
  - version de règle utilisée pour le calcul

### Utilité métier

Table de référence pour la prime sportive.

## `gold_eligible_wellbeing_days`

### Rôle

Table finale d'éligibilité aux jours bien-être.

### Grain

1 ligne = 1 salarié

### Champs principaux

- `employee_id`
  - identifiant salarié
- `reference_year`
  - année de référence
- `full_name`
  - nom complet
- `business_unit`
  - BU
- `activity_count_12m`
  - volume d'activités sur 12 mois
- `wellbeing_days_awarded`
  - nombre de jours attribués
- `eligibility_status`
  - booléen : éligible ou non
- `eligibility_reason`
  - raison : `eligible` ou `insufficient_activities`
- `rule_version`
  - version de règle utilisée

### Utilité métier

Table de référence pour les jours bien-être.

## `gold_kpi_finance`

### Rôle

Table de synthèse KPI pour la vue exécutive.

### Grain

1 ligne = 1 année de référence

### Champs principaux

- `reference_year`
  - année du calcul
- `eligible_bonus_employees`
  - nombre de salariés éligibles à la prime
- `eligible_wellbeing_employees`
  - nombre de salariés éligibles aux jours bien-être
- `total_bonus_cost`
  - coût total des primes
- `avg_bonus_amount`
  - montant moyen de prime
- `activity_count_total`
  - nombre total d'activités valides

### Utilité métier

Table idéale pour :
- cartes KPI ;
- pilotage de coût ;
- restitution exécutive.

## `gold_kpi_employee_status`

### Rôle

Vue détaillée par salarié pour les analyses et filtres de dashboard.

### Grain

1 ligne = 1 salarié

### Champs principaux

- `employee_id`
  - identifiant salarié
- `full_name`
  - nom complet
- `business_unit`
  - BU
- `is_bonus_eligible`
  - booléen : éligibilité prime
- `bonus_amount`
  - montant de prime
- `bonus_reason`
  - raison métier liée à la prime
- `is_wellbeing_eligible`
  - booléen : éligibilité jours bien-être
- `wellbeing_days_awarded`
  - nombre de jours attribués
- `wellbeing_reason`
  - raison métier liée aux jours bien-être
- `activity_count_12m`
  - nombre d'activités sur 12 mois
- `transport_mode`
  - mode de transport
- `distance_km_to_office`
  - distance domicile-bureau

### Utilité métier

C'est la table principale de drill-down pour Tableau.

## `gold_slack_messages`

### Rôle

Table finale des messages Slack simulés générés par les activités sportives.

### Grain

1 ligne = 1 message

### Champs principaux

- `message_id`
  - identifiant du message
- `activity_id`
  - activité ayant déclenché le message
- `employee_id`
  - salarié concerné
- `channel_name`
  - channel Slack simulé
- `message_text`
  - contenu du message
- `generated_at`
  - date/heure de génération
- `status`
  - statut du message

### Utilité métier

Cette table sert à démontrer la dimension streaming et gamification du projet.

## `gold_quality_anomalies`

### Rôle

Table consolidée des anomalies qualité détectées dans le pipeline.

### Grain

1 ligne = 1 anomalie

### Champs principaux

- `anomaly_id`
  - identifiant de l'anomalie
- `detected_at`
  - date de détection
- `table_name`
  - table concernée
- `record_id`
  - identifiant d'enregistrement concerné
- `anomaly_type`
  - type d'anomalie
- `anomaly_detail`
  - détail métier ou technique

### Utilité métier

Cette table sert au pilotage qualité et à la démonstration de robustesse du pipeline.

## 4. Tables à privilégier pour Tableau

Pour Tableau, les tables les plus utiles sont :

- `public_gold.gold_kpi_finance`
  - pour les cartes KPI
- `public_gold.gold_kpi_employee_status`
  - pour les analyses détaillées par salarié et BU
- `public_gold.gold_eligible_sport_bonus`
  - pour détailler la prime sportive
- `public_gold.gold_eligible_wellbeing_days`
  - pour détailler les jours bien-être
- `public_gold.gold_quality_anomalies`
  - pour la page qualité
- `public_gold.gold_slack_messages`
  - pour illustrer la gamification

## 5. Résumé simple

### Silver

- niveau de préparation analytique
- données propres et enrichies
- base des règles métier

### Gold

- niveau de restitution
- tables prêtes pour dashboard et soutenance
- KPI et décisions métier directement exploitables
