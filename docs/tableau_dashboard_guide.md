# Guide Tableau

Ce guide résume les tables et visualisations recommandées pour construire le dashboard de soutenance.

## Connexion

Dans Tableau, se connecter à PostgreSQL avec :

```text
Server: localhost
Port: 5432
Database: sport_data
Username: sport_user
Password: sport_pass
```

## Tables recommandées

### Vue exécutive

- `public_gold.gold_kpi_finance`
- `public_gold.gold_kpi_employee_status`

### Analyse temporelle

- `public_gold.gold_employee_benefit_timeline`

### Carte salariés

- `public_gold.gold_employee_map`

### Détail activités

- `public_silver.sil_sport_activities`

## Visualisations recommandées

### 1. KPI globaux

Source :
- `gold_kpi_finance`

Mesures :
- salariés éligibles bonus
- salariés éligibles wellbeing
- coût total des bonus
- jours wellbeing attribués

### 2. Activité dans le temps

Source :
- `gold_employee_benefit_timeline`

Axes :
- X : `snapshot_date`
- Y : `SUM(activity_count_on_date)`

Variantes :
- activité par `contract_type`
- activité par `business_unit`

### 3. Éligibilité dans le temps

Source :
- `gold_employee_benefit_timeline`

Mesures :
- nombre d'éligibles bonus
- nombre d'éligibles wellbeing

Dimension :
- `snapshot_date`

### 4. Carte géographique

Source :
- `gold_employee_map`

Champs :
- longitude : `home_lon`
- latitude : `home_lat`
- détail : `full_name`
- couleur : `business_unit` ou `contract_type`

### 5. Analyse RH

Source :
- `gold_kpi_employee_status`

Dimensions :
- `contract_type`
- `business_unit`
- `bonus_reason` si nécessaire via la timeline

Mesures :
- `SUM(bonus_amount)`
- `SUM(wellbeing_days_awarded)`
- taux d'éligibilité

## Dashboard conseillé

1. Vue exécutive
- KPI globaux
- répartition par contrat et BU

2. Évolution
- activité dans le temps
- éligibilité dans le temps

3. Carte
- localisation des salariés

## Conseils

- utiliser `gold` pour la restitution métier
- éviter la timeline pour la carte afin de ne pas dupliquer les salariés
- utiliser `bonus_amount` pour le coût réel et `potential_bonus_amount` pour le scénario théorique
