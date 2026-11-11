# État du projet par rapport au manuel complet

Référence examinée : *Manuel de travaux pratiques — Développement et déploiement d’applications intelligentes*, édition enrichie du 11 novembre 2026 (Atelier 0 et TP1 à TP4).

## Couverture présente

- Atelier 0 : cadrage, scripts d’installation, diagnostic, dépôt et tests de clone.
- TP1 : génération de données, entraînement/évaluation, prédiction CLI, API FastAPI et tests.
- TP2 : validation, abstention, jeu d’or, tests aux limites, typage et CI. L’API `/v1` protégée par clés/roles et le client JavaScript sont désormais ajoutés; `/predict` et Streamlit restent utilisables pour compatibilité.
- TP3 : interface Streamlit, traitement CSV, résumé et téléchargement des résultats.
- TP4 : paquet, CLI, roue et test d’installation hors du dépôt dans la CI.

## Éléments restant à compléter

1. **Complément Java (manuel, activité complémentaire, p. 51–52)** : `java/avis-service`, Spring Boot, cinq tests JUnit, construction du JAR et appels réels n’étaient pas présents dans le dépôt au moment de la comparaison. Cette activité est facultative dans le manuel.
2. **Publication de release** : la procédure `gh release create` est décrite, mais aucune publication ne peut être déduite des fichiers locaux. La release v1.0.0 nécessite un dépôt distant, les distributions construites et le fichier `docs/livrable-tp4.txt`.
3. **Hébergement Streamlit** : le manuel fournit une procédure, sans exécution cloud attendue dans le kit local.
4. **Travail de séance/binôme** : les commits des deux membres, les clés réelles, l’historique Git distant et la démonstration dans un navigateur doivent être vérifiés dans les environnements concernés; les fichiers seuls ne prouvent pas ces actions.

Les TP5/TP6 présents dans ce dépôt dépassent le périmètre de ce volume du manuel. Le PDF décrit des exercices et sorties attendues; il ne prouve pas à lui seul qu’une procédure a été exécutée sur ce projet.
