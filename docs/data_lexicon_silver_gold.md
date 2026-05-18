# Lexique des données Silver et Gold

Ce document résume les tables les plus utiles pour l'analyse métier et la restitution BI.

## Couche Silver

### `public_silver.sil_employees`

Rôle :
- référentiel salariés nettoyé et enrichi

Grain :
- 1 ligne = 1 salarié

Champs utiles :
- `employee_id`
- `full_name`
- `business_unit`
- `contract_type`
- `gross_salary`
- `home_address`
- `home_lat`
- `home_lon`
- `distance_km_to_office`
- `transport_mode`
- `is_transport_mode_sportive`
- `is_distance_rule_valid`

Usage :
- base RH pour les calculs d'éligibilité
- carte des domiciles salariés

### `public_silver.sil_sport_activities`

Rôle :
- activités sportives consommées et validées

Grain :
- 1 ligne = 1 activité

Champs utiles :
- `activity_id`
- `employee_id`
- `activity_type`
- `activity_date`
- `distance_km`
- `duration_min`
- `calories_burned`
- `event_ts`
- `is_valid_activity`

Usage :
- volumétrie d'activité
- analyses par type de sport et par date

## Couche Gold

### `public_gold.gold_kpi_employee_status`

Rôle :
- vue synthétique par salarié

Grain :
- 1 ligne = 1 salarié

Champs utiles :
- `employee_id`
- `full_name`
- `business_unit`
- `contract_type`
- `is_bonus_eligible`
- `bonus_amount`
- `potential_bonus_amount`
- `is_wellbeing_eligible`
- `wellbeing_days_awarded`
- `last_activity_date`
- `last_process_date`

Usage :
- KPI salariés
- segmentation RH
- suivi des avantages

### `public_gold.gold_employee_benefit_timeline`

Rôle :
- historique journalier des activités et avantages

Grain :
- 1 ligne = 1 salarié + 1 `snapshot_date`

Champs utiles :
- `employee_id`
- `snapshot_date`
- `activity_count_on_date`
- `activity_count_12m`
- `distance_km_on_date`
- `duration_min_on_date`
- `bonus_reason`
- `is_bonus_eligible`
- `bonus_amount`
- `is_wellbeing_eligible`
- `wellbeing_days_awarded`

Usage :
- évolution de l'activité dans le temps
- évolution des primes et éligibilités

### `public_gold.gold_employee_map`

Rôle :
- table dédiée à la cartographie salariés

Grain :
- 1 ligne = 1 salarié

Champs utiles :
- `employee_id`
- `full_name`
- `business_unit`
- `contract_type`
- `home_city`
- `home_lat`
- `home_lon`
- `distance_km_to_office`
- `is_bonus_eligible`
- `is_wellbeing_eligible`

Usage :
- carte géographique
- filtres RH et métier

## Lecture recommandée pour la BI

- vue RH synthétique : `gold_kpi_employee_status`
- analyse temporelle : `gold_employee_benefit_timeline`
- carte salariés : `gold_employee_map`
- analyses détaillées activités : `sil_sport_activities`
