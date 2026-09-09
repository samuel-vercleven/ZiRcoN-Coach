# Build Optimizer v1 — évaluation et gate produit

2026-09-09 — `feature/build-optimizer`. **REVIEW_REQUIRED / NO FREEZE.**
Le socle indépendant est implémenté et testé ; la mission produit complète ne
peut pas être déclarée accomplie. Aucun « meilleur achat » n'est validé.

## Ce qui fonctionne réellement

```text
Match/timeline locaux -> GameContext existant
  -> BuildContext à t (identité et observations, aucune statistique finale)
  -> Item Knowledge exact-patch -> candidats structurels
  -> solveur de recettes (consommation v22, budget, slots)
  -> sous-total économique diagnostic et provenance
  -> BuildRecommendation : abstention motivée tant que les gates manquent
```

API sans UI/réseau implicite :

```python
from build_optimizer.context import build_context
from build_optimizer.engine import BuildOptimizer

context = build_context(game_context, timestamp_ms, catalog_view, champion_records)
recommendation = BuildOptimizer(catalog_view).recommend(context)
payload = recommendation.to_dict()  # sérialisable en JSON
```

`target_item=None`, `buy_now=[]`, `score=None`, alternatives vides restent
explicites. `candidate_diagnostics` et `RecipePlanner.plan` ne sont pas une
voie détournée pour annoncer un achat exécutable ou un item optimal.

## Scoring réel, pas celui illustré dans le TODO

| Facteur | Poids | État |
|---|---:|---|
| ChampionSynergy | null | UNMODELED, pas d'inférence AP/AD depuis un tag |
| EnemyCounter | null | UNMODELED, présence d'armure/MR n'est pas un modèle d'utilité |
| CurrentBuildSynergy | null | UNMODELED au sens gameplay |
| GameNeed | null | UNMODELED ; pas de causalité depuis Death/Reset |
| PowerSpikeValue | null | UNMODELED |
| EconomyValue | 1 | EXPERIMENTAL, fraction du coût de recette couverte |
| PurchaseFeasibility | null | Légalité complète UNMODELED |
| RedundancyPenalty | null | Pas de pénalité inventée |
| IncompatibilityPenalty | null | Restrictions connues filtrées, inconnues bloquantes |

Seul diagnostic numérique : `(prix total - coût restant après plan) / prix total`.
Le poids 1 conserve cette unité ; il n'est pas une calibration gameplay.
Ce sous-total est recomputable depuis ses contributions mais **n'est pas un
score final** et ne classe pas les items comme « meilleurs ».
Les raisons positives/négatives ne viennent que de contributions non nulles.
Les motifs d'abstention sont distincts des raisons de scoring.

Configuration centralisée : `build_optimizer/scoring.py`. Limites techniques
du planificateur : six slots (contrat v22), 5 000 états de recherche ; toute
troncature est signalée. Cadence de parsing : tolérance 90 s de GameContext,
pas de nouveau seuil gameplay ni de retuning d'un analyzer.

## Tests et jeux réels

- Baseline : main.py PASS, 43/43 suites Stable Base PASS, 159 modules compilés.
- Final : compilation 169 modules ; 43/43 suites Stable Base, main.py (2,26 s),
  89 chemins FROZEN, scan secrets et diff check PASS. Les cinq commandes du
  validateur final passent ; disposition globale REVIEW_REQUIRED / NO FREEZE.
- Nouveaux tests : 23 méthodes unittest, avec sous-cas et dix scénarios nommés.
  Les scénarios double frontline/squishy ont des observations HP/armure
  distinctes ; AD/AP/MR sont des observations synthétiques. Healing reste
  explicitement non modélisé. Ce sont des tests d'invariants et d'abstention,
  **pas dix matchups dont la recommandation aurait été validée**.
- Trois catalogues réels : 16.9.1, 16.16.1, 16.17.1 ; 217 cibles structurelles
  par patch, 8 385 cas contrôlés, 13 552 étapes vérifiées. Inventaires/budgets
  de ces cas sont synthétiques et distincts des replays historiques.
- Golden Games : sept paires match/timeline vérifiées par SHA-256 ; 28 heures
  demandées, 28 tests de mutation future, 28 contrôles des snapshots précédents.
  Inventaires propres trop incertains : aucun plan historique admis dans ces
  sept cas ; le rapport dit NOT_EXERCISED, pas une validation de recettes vide.
- Batch : 118 matchs SoloQ locaux, 472 heures demandées, 472 mutations futures,
  472 contrôles des snapshots précédents et 472 contrôles de sensibilité au passé.
  Sur les 50 snapshots admissibles : 10 760 plans, 13 942 étapes et 1 482 recettes
  complétables dans le modèle. Ces nombres ne sont pas des achats recommandés.
- Aucune donnée Riot nouvelle synchronisée ; données de match lues localement.
  Chargement des catalogues publics Data Dragon exacts autorisé hors UI.

Golden IDs : EUW1_7965168777, EUW1_7965120221, EUW1_7963255011,
EUW1_7959361127, EUW1_7951911875, EUW1_7836627546, EUW1_7839112939.
Ils sont également présents dans le batch : ne pas additionner les deux comme
des observations indépendantes. 7 timestamps Golden et 39 timestamps du batch
sont après la dernière frame de la partie ; ils restent indisponibles à t.

## Précision temporelle : correction issue du vrai replay

Dans EUW1_7965120221 les frames commencent à 0, 60003, 120018, 180040 ms.
L'ancien contrôle ajouté dans cette mission prenait une dérive de quelques
millisecondes pour un trou >60 s. Correction au contrat d'admission 90 s déjà
employé par GameContext, sans modifier GameContext.

Une demande à 600000 ms ne donne pas le gold exact de 600142 ms. Le gold à
540121 ms existe, mais n'est pas mélangé avec les achats de 540122–600000 ms.
Le replay teste séparément le snapshot entier à 540121 ms. Toutes les
reconstructions de recettes historiques portent leur `recipe_plan_timestamp`.
Les dates, items finaux, résultats, niveaux finaux et suffixes de timeline
modifiés artificiellement ne changent ni le contexte antérieur ni l'abstention.
Le rôle attribué post-game et la visibilité des ennemis ne sont pas présumés
connus à t.

## Classement de l'évaluation

Les 472 sorties demandées sont `QUESTIONABLE` au sens produit : abstention
sûre, décision demandée indisponible. Aucun label GOOD/PLAUSIBLE n'est attribué
à un item sur la seule base d'une facture correcte ou de l'achat réel du joueur.
Le replay et les cas contrôlés n'ont observé ni exception fatale, ni violation
de leurs invariants. Cela ne valide pas tous les cas du client Riot.

## Zero Gate

| Gate | Résultat |
|---|---|
| Régression Stable Base | PASS à la baseline et à la validation finale |
| Tests unitaires / scénarios d'invariants | PASS |
| Recettes sur vrais catalogues | PASS dans le modèle structurel |
| Replay historique / temporal integrity | PASS sur les mutations exécutées |
| Recommandations contextuelles validées | **0 — BLOCKED** |
| Légalité complète d'achat | **UNMODELED — BLOCKED** |
| Invalid buy_now | 0 parce que buy_now est vide, pas une preuve de légalité |
| Fuite future détectée dans les tests | 0 |
| Freeze produit | **NO FREEZE** |

Commande reproductible : `python -m build_optimizer.validation`.
Code retour 2 signifie REVIEW_REQUIRED si les tests techniques passent ;
code 1 signale un échec technique. Ce n'est pas un script qui retourne PASS
inconditionnellement lorsque toutes les recommandations sont vides.
Journaux : `logs/build_optimizer/final/`, `golden_replay.json`,
`batch_replay.json`, `catalog_checks.json`. Aucun JSON brut privé ni DB dans Git.

## Décision nécessaire avant la suite

1. Un contrat patché et sourcé de légalité : groupes exclusifs, limites de
   doublons, runes/quêtes/champions/modes, accès magasin, inventaire admissible.
2. Un périmètre de scoring contextuel défendable et une grille d'évaluation,
   avec poids explicitement expérimentaux si le projet accepte une heuristique.
   Les sorties Phase 2I restent non exécutables sans nouvelle preuve ; un score
   fondé sur des observations ne doit pas être présenté comme simulation combat.

Il n'est pas nécessaire de modifier une fondation FROZEN pour conserver ce
socle de projection/recettes. Aucun changement FROZEN, freeze, merge ou
successeur n'est effectué. Les étapes bloquées du TODO restent ouvertes.
