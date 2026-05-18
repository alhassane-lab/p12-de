# Dashboard Tableau

Ce document décrit le dashboard Tableau final du projet, ses objectifs métier et les principales tables utilisées.

Dashboard public de référence :
- `https://public.tableau.com/app/profile/alhassane.ahmed/viz/Classeur1_17788668104040/1_avantages_sportif2`

## Objectif

Le dashboard permet de :
- suivre les KPI globaux du programme d'avantages sportifs ;
- segmenter les salariés par contrat et par moyen de transport ;
- observer l'évolution des salariés éligibles dans le temps ;
- analyser l'activité sportive et sa dynamique.

## Structure du dashboard

### 1. KPI globaux

Indicateurs affichés :
- nombre de salariés éligibles au bonus sport
- nombre de salariés éligibles aux jours bien-être
- coût total des bonus attribués
- nombre total de jours bien-être attribués

Tables utilisées :
- `public_gold.gold_kpi_finance`
- `public_gold.gold_kpi_employee_status`

### 2. Répartition des salariés

Analyses affichées :
- répartition par `contract_type`
- répartition par `transport_mode`

Mesures possibles :
- nombre de salariés
- nombre de salariés éligibles
- montant total des bonus

Tables utilisées :
- `public_gold.gold_kpi_employee_status`
- `public_silver.sil_employees`

### 3. Évolution des salariés éligibles

Visualisation :
- courbe temporelle

Objectif :
- suivre l'évolution du nombre de salariés éligibles au bonus sport
- comparer si besoin avec l'éligibilité aux jours bien-être

Table utilisée :
- `public_gold.gold_employee_benefit_timeline`

Mesures utiles :
- `COUNTD(employee_id)` avec filtre `is_bonus_eligible = true`
- `COUNTD(employee_id)` avec filtre `is_wellbeing_eligible = true`

### 4. Évolution de l'activité sportive

Visualisation :
- courbe d'activité dans le temps

Mesure principale :
- `SUM(activity_count_on_date)`

Table utilisée :
- `public_gold.gold_employee_benefit_timeline`

Variantes utiles :
- activité par `contract_type`
- activité par `business_unit`

## Filtres recommandés

- `business_unit`
- `contract_type`
- `transport_mode`
- `snapshot_date`

## Message métier

Le dashboard doit permettre de répondre rapidement aux questions suivantes :
- combien de salariés bénéficient effectivement des avantages ?
- quels profils sont les plus représentés parmi les éligibles ?
- l'éligibilité progresse-t-elle dans le temps ?
- le mode de transport influence-t-il l'accès au bonus sport ?
