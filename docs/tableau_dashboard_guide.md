# Dashboard Tableau - Guide pas à pas

Ce document explique comment construire entièrement le dashboard attendu dans Tableau à partir des tables finales déjà calculées par le pipeline.

Le principe est simple :
- le pipeline alimente PostgreSQL ;
- dbt calcule les tables finales dans le schéma `public_gold` ;
- Tableau se connecte à PostgreSQL et consomme directement ces tables.

## 1. Pré-requis

Avant d'ouvrir Tableau, vérifiez que :
- PostgreSQL tourne ;
- le pipeline a bien été exécuté ;
- les tables finales existent dans `public_gold`.

Commande de vérification :

```bash
docker exec -it sport-postgres psql -U sport_user -d sport_data
```

Puis dans `psql` :

```sql
\dt public_gold.*
select * from public_gold.gold_kpi_finance;
select * from public_gold.gold_kpi_employee_status limit 5;
```

Les tables utiles pour le dashboard sont :
- `public_gold.gold_kpi_finance`
- `public_gold.gold_kpi_employee_status`
- `public_gold.gold_eligible_sport_bonus`
- `public_gold.gold_eligible_wellbeing_days`
- `public_gold.gold_slack_messages`
- `public_gold.gold_quality_anomalies`

## 2. Connexion Tableau à PostgreSQL

Dans Tableau :

1. ouvrir Tableau
2. dans `Connect`, choisir `PostgreSQL`
3. renseigner :

```text
Server: localhost
Port: 5432
Database: sport_data
Username: sport_user
Password: sport_pass
```

4. cliquer sur `Sign In`

Si Tableau demande un driver PostgreSQL, l'installer puis relancer Tableau.

## 3. Choisir les tables à importer

Une fois connecté :

1. sélectionner le schéma `public_gold`
2. ajouter les tables suivantes dans la source :
   - `gold_kpi_finance`
   - `gold_kpi_employee_status`
   - `gold_eligible_sport_bonus`
   - `gold_eligible_wellbeing_days`
   - `gold_slack_messages`
   - `gold_quality_anomalies`

Recommandation :
- pour un POC, il est plus simple de créer plusieurs sources Tableau séparées au lieu de forcer une grosse jointure unique.

Configuration recommandée :
- Source 1 : `gold_kpi_finance`
- Source 2 : `gold_kpi_employee_status`
- Source 3 : `gold_eligible_sport_bonus`
- Source 4 : `gold_eligible_wellbeing_days`
- Source 5 : `gold_slack_messages`
- Source 6 : `gold_quality_anomalies`

## 4. Dashboard attendu

Le dashboard peut être construit en 3 pages :
- Vue exécutive
- Analyse des activités
- Pilotage qualité

## 5. Page 1 - Vue exécutive

Objectif :
- montrer immédiatement les KPI globaux du programme d'avantages sportifs.

### 5.1 KPI 1 - Nombre de salariés éligibles à la prime

Source :
- `gold_kpi_finance`

Créer une feuille :
- nom : `KPI Eligibles Prime`
- type : `Text`

Champs :
- utiliser `eligible_bonus_employees`

Format :
- gros chiffre
- titre : `Salariés éligibles à la prime`

### 5.2 KPI 2 - Nombre de salariés éligibles aux jours bien-être

Source :
- `gold_kpi_finance`

Créer une feuille :
- nom : `KPI Eligibles Bien-Etre`

Champs :
- `eligible_wellbeing_employees`

### 5.3 KPI 3 - Coût total des primes

Source :
- `gold_kpi_finance`

Créer une feuille :
- nom : `KPI Cout Total Prime`

Champs :
- `total_bonus_cost`

Format :
- devise ou nombre avec séparateur
- titre : `Coût total des primes`

### 5.4 KPI 4 - Nombre total d'activités

Source :
- `gold_kpi_finance`

Créer une feuille :
- nom : `KPI Nombre Activites`

Champs :
- `activity_count_total`

### 5.5 Histogramme - Eligibilité prime par BU

Source :
- `gold_kpi_employee_status`

Créer une feuille :
- nom : `Prime par BU`
- type : `Bar chart`

Champs :
- Colonnes : `business_unit`
- Lignes : `SUM(INT([is_bonus_eligible]))`

Astuce :
- si Tableau ne convertit pas bien le booléen, créer un champ calculé :

```text
IF [is_bonus_eligible] THEN 1 ELSE 0 END
```

Puis agréger ce champ.

### 5.6 Histogramme - Eligibilité bien-être par BU

Source :
- `gold_kpi_employee_status`

Créer une feuille :
- nom : `Bien-Etre par BU`

Champs :
- Colonnes : `business_unit`
- Lignes : `SUM(INT([is_wellbeing_eligible]))`

## 6. Page 2 - Analyse des activités

Objectif :
- montrer l'engagement sportif et le détail par salarié.

### 6.1 Répartition des salariés selon l'activité sur 12 mois

Comme la table `gold_kpi_employee_status` contient `activity_count_12m`, elle peut déjà servir pour l'analyse.

Créer une feuille :
- nom : `Top Salaries Actifs`
- type : `Table`

Champs :
- `full_name`
- `business_unit`
- `activity_count_12m`
- `is_bonus_eligible`
- `is_wellbeing_eligible`

Tri :
- décroissant sur `activity_count_12m`

### 6.2 Répartition par BU

Créer une feuille :
- nom : `Activite moyenne par BU`

Champs :
- Colonnes : `business_unit`
- Lignes : `AVG(activity_count_12m)`

### 6.3 Vue de synthèse salarié

Créer une feuille :
- nom : `Statut Salaries`

Champs :
- `full_name`
- `business_unit`
- `bonus_amount`
- `wellbeing_days_awarded`
- `activity_count_12m`
- `transport_mode`
- `distance_km_to_office`

## 7. Page 3 - Pilotage qualité

Objectif :
- montrer que le pipeline ne fait pas seulement du calcul métier, mais aussi du contrôle de qualité.

### 7.1 KPI - Nombre d'anomalies

Source :
- `gold_quality_anomalies`

Créer une feuille :
- nom : `KPI Anomalies`

Mesure :
- `COUNT(anomaly_id)`

### 7.2 Tableau - Anomalies par type

Créer une feuille :
- nom : `Anomalies par Type`

Champs :
- `anomaly_type`
- `COUNT(anomaly_id)`

### 7.3 Tableau détaillé des anomalies

Créer une feuille :
- nom : `Detail Anomalies`

Champs :
- `table_name`
- `record_id`
- `anomaly_type`
- `anomaly_detail`
- `detected_at`

## 8. Page 4 optionnelle - Messages Slack simulés

Cette page peut être utile en démo pour montrer la logique de streaming et de gamification.

Source :
- `gold_slack_messages`

Créer une feuille :
- nom : `Messages Slack`

Champs :
- `generated_at`
- `employee_id`
- `channel_name`
- `message_text`
- `status`

## 9. Filtres recommandés

Sur les pages analytiques, ajouter si possible :
- `business_unit`
- `full_name`
- `is_bonus_eligible`
- `is_wellbeing_eligible`

## 10. Mise en page recommandée

### Dashboard 1 - Vue exécutive

Disposition :
- 4 KPI en haut
- 2 histogrammes en dessous

### Dashboard 2 - Analyse salariés

Disposition :
- histogramme BU à gauche
- tableau top salariés à droite
- tableau détaillé en bas

### Dashboard 3 - Qualité

Disposition :
- KPI anomalies en haut
- anomalies par type au centre
- détail en bas

### Dashboard 4 optionnel - Slack

Disposition :
- tableau simple

## 11. Conseils de démo

Pendant la soutenance :

1. montrer la connexion à PostgreSQL
2. montrer que les données viennent des tables `public_gold`
3. commencer par la vue exécutive
4. zoomer ensuite sur une BU ou un salarié
5. finir par la page qualité pour montrer la robustesse du pipeline

Phrase possible :

`Le pipeline calcule les indicateurs finaux dans PostgreSQL, dans les tables du schéma public_gold. Tableau ne fait ici que la restitution visuelle des résultats produits par le pipeline data.`

## 12. Vérification SQL utile avant la démo

Avant d'ouvrir Tableau, vérifier rapidement :

```bash
docker exec -it sport-postgres psql -U sport_user -d sport_data
```

Puis :

```sql
select * from public_gold.gold_kpi_finance;
select count(*) from public_gold.gold_kpi_employee_status;
select count(*) from public_gold.gold_quality_anomalies;
select count(*) from public_gold.gold_slack_messages;
```

## 13. Résumé minimal

Pour faire le dashboard :

1. lancer le pipeline
2. vérifier les tables `public_gold`
3. connecter Tableau à PostgreSQL
4. créer les feuilles KPI
5. assembler les dashboards
6. vérifier le rendu final avant soutenance
