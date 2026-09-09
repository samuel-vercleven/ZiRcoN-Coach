BUILD OPTIMIZER v1 — CONTEXTUAL RECOMMENDATION PASS

Status 2026-09-10: TECHNICAL PASS / REVIEW_REQUIRED FOR BUILD OPTIMIZER V1 FREEZE.
Le premier contrat est `DETERMINISTIC_CONTEXTUAL_HEURISTIC_V1`, limité à
`shyvana_ap_build_profile_v1` et aux patches exacts 16.9, 16.16, 16.17, 16.18.
`buy_now` signifie `IF_SHOPPING_NOW`; ce n'est jamais une localisation au shop.
14 recommandations réelles non vides sont exercées (objectif review 20 non atteint).

[x] 1. Préflight / baseline
[ ] 2. Ne modifier aucun fichier FROZEN
[ ] 3. Conserver le RecipePlanner actuel
[x] 4. Créer Item Legality Contract
[ ] 5. Fail closed sur restriction inconnue
[x] 6. Créer Item Semantic Contract
[ ] 7. Supporter uniquement les items AP majeurs SR correctement modélisés
[x] 8. Créer Shyvana AP Profile v1
[x] 9. Enrichir BuildContext avec observations temporelles sûres
[x] 10. Ajouter totalGold / stats nécessaires depuis les frames
[x] 11. Créer Historical Context Baseline
[ ] 12. Baselines par fenêtre temporelle
[x] 13. Empêcher toute fuite future dans les baselines historiques
[ ] 14. Générer frontline_pressure
[ ] 15. Générer MR_pressure
[ ] 16. Générer physical_threat
[ ] 17. Générer magic_threat
[ ] 18. Générer team_state
[ ] 19. Implémenter ChampionFit
[ ] 20. Implémenter EnemyResponse
[ ] 21. Implémenter CurrentBuildSynergy
[ ] 22. Implémenter GameStateNeed
[ ] 23. Implémenter PowerSpikeValue
[ ] 24. Conserver EconomyValue
[ ] 25. Implémenter PurchaseFeasibility
[x] 26. Score final recomposable
[ ] 27. Candidate hard-block si illégal/incomplet
[x] 28. Produire target_item
[x] 29. Produire buy_now / IF_SHOPPING_NOW
[ ] 30. Produire offensive alternative
[ ] 31. Produire defensive alternative
[ ] 32. Explanation Engine strictement relié au score
[ ] 33. Ajouter confidence + coverage
[x] 34. Abstention si contexte insuffisant
[x] 35. Tests synthétiques
[x] 36. Tests adversariaux
[x] 37. Tests vrais items Data Dragon
[x] 38. Tests patch 16.18.1
[x] 39. Historical replay
[x] 40. Temporal leakage tests
[ ] 41. Minimum plusieurs recommandations non vides
[x] 42. Générer rapport d'évaluation
[ ] 43. Mettre à jour TODO / LAST_RUN / PROJECT_STATE
[ ] 44. Commit
[ ] 45. Push feature/build-optimizer
[x] 46. REVIEW_REQUIRED
[x] 47. NE PAS FREEZER AUTOMATIQUEMENT
