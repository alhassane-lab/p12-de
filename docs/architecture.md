# Architecture cible

Le POC sépare clairement :
- l'atterrissage des données brutes ;
- le nettoyage et l'enrichissement ;
- les restitutions métier.

## Couches

### Bronze

- sources brutes exposées dans dbt à partir des tables `raw`
- traçabilité des fichiers et des événements
- conservation du payload JSON original

### Silver

- typage des dates Excel
- normalisation des modes de transport
- dédoublonnage
- calcul de distance domicile-bureau
- consolidation salariés / activités / pratique déclarative

### Gold

- éligibilité prime sportive
- éligibilité jours bien-être
- coûts, KPI, messages Slack, anomalies qualité

## Point d'attention POC

Le géocodage est simulé localement de manière déterministe à partir de l'adresse. Cela évite toute dépendance API externe tout en permettant de démontrer la règle de distance. Dans un projet réel, cette brique serait remplacée par un service de géocodage maîtrisé.

## Orchestration Airflow

Le projet utilise un DAG Airflow unique pour l'orchestration du pipeline quotidien.

Deux comportements sont prévus :
- en exécution planifiée quotidienne à `08:00`, les tâches de chargement statique sont skippées ;
- en exécution manuelle avec `run_static_load=true`, ces tâches sont rejouées.

Le branchement est modélisé directement dans le code du DAG par deux dépendances :

```python
branch_static_load >> skip_static_load >> generate_activities
branch_static_load >> load_business_rules >> ingest_static_sources >> generate_activities
```

La fonction Python du `BranchPythonOperator` décide simplement quelle première tâche de branche doit être suivie.
