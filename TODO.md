# ZiRcoN Coach — Build Optimizer v1

## État d'exécution — 2026-09-10 — REVIEW_REQUIRED / NO FREEZE

Mission produit **non terminée** : les branches indépendantes sont testées, mais
le moteur ne sait pas encore recommander le meilleur achat contextuel.
Voir BUILD_OPTIMIZER_AUDIT.md et BUILD_OPTIMIZER_EVALUATION.md.

| Étapes de ce TODO | État réel |
|---|---|
| 0–1 Baseline / audit | PASS : 43/43 suites, main.py, 89 fichiers FROZEN inchangés |
| 2 BuildContext | Projection préfixe testée ; rôle post-game, gold exact absent et inventaires ambigus restent inconnus |
| 3 Item Knowledge | Réutilisé sans modification ; restriction complète d'achat UNMODELED |
| 4 Candidats | Filtrage structurel testé, pas une validation complète des achats |
| 5–6 Scoring / breakdown | Sous-total de recette diagnostic seulement ; score d'utilité contextuelle BLOCKED |
| 7 Purchase Optimizer | Recettes/budget/slots et crédit de composants indépendamment audités ; buy_now reste vide sans contrat de légalité |
| 8 Explications | Raisons des contributions diagnostiques testées ; aucune raison combat inventée |
| 9 Alternatives | BLOCKED : pas de condition de switch contextuelle validée |
| 10 Scénarios | 23 tests d'invariants/scénarios + 15 adversarial gate checks ; qualité gameplay NON VALIDÉE |
| 11–12 Replay / évaluation | 7 Golden Games + 129 matchs SoloQ locaux, invariance temporelle vérifiée ; 516 abstentions QUESTIONABLE au sens produit |
| 13–14 API / E2E | API sérialisable sans UI ; E2E jusqu'à l'abstention explicite |
| 15 Zero Gate | 8 gates techniques PASS ; recommandations, qualité scénario, scoring final et légalité complète BLOCKED |
| 16 Freeze | NON EFFECTUÉ ; aucun fichier ajouté au FROZEN guard |

8 385 cas contrôlés sur catalogues réels et 10 760 plans historiques de recettes
vérifiés ne prouvent pas une recommandation valide. Les contrôles adversariaux
rejettent maintenant un crédit de composant étranger, un surcrédit répété,
un crédit ancêtre+descendant, un item structurellement exclu et une étape hors
de la recette cible. Aucun poids combat ni owner inventé. Aucun successeur
commencé. La mission originale reste ci-dessous.

## Objectif de cette phase

Construire un moteur capable de répondre à :

> « À cet instant précis de cette partie, avec mon champion, mon gold, mon inventaire, les ennemis, leurs items et l’état de la game, quel est mon meilleur prochain achat et pourquoi ? »

Ce n’est PAS un build meta statique.

Le moteur doit produire :

```text
TARGET ITEM
Liandry's Torment

BUY NOW
Blasting Wand
Amplifying Tome

ALTERNATIVE
Zhonya's Hourglass

WHY
+ forte frontline ennemie
+ bonne valeur en combat prolongé
+ cohérent avec le build AP actuel
- moins défensif contre Vi
```

---

# Règles absolues

1. Ne casse pas `Stable Base v1`.
2. Ne modifie pas les fondations déjà FROZEN sauf nécessité démontrée.
3. Ne refais pas GameContext s’il existe déjà.
4. Ne refais pas Item Knowledge s’il existe déjà.
5. Aucun gros refactor gratuit.
6. Le moteur v1 doit être déterministe.
7. Aucun LLM ne choisit directement l’item.
8. Toute recommandation doit être explicable.
9. Chaque score doit être décomposable.
10. Aucun usage de données futures lors d’un replay historique.
11. Aucun item impossible ne peut apparaître dans `buy_now`.
12. Aucun chiffre magique dispersé dans le code.
13. Les poids doivent être centralisés.
14. Les hypothèses non validées doivent être marquées.
15. Pas d’overlay live pendant cette phase.
16. Pas de Recall Optimizer complet.
17. Pas d’Adaptive Build complet.
18. Pas de ML.
19. Chaque étape doit ajouter ou renforcer des tests.
20. Ne freeze pas la phase tant que les critères de sortie ne sont pas satisfaits.

---

# Étape 0 — Baseline

Avant toute modification :

```powershell
git status
git log -10 --oneline
git branch --show-current
git tag
python main.py
```

Puis lancer toute la suite de tests existante.

Conserver les résultats comme baseline.

Créer / utiliser :

```text
feature/build-optimizer
```

Ne commence pas à coder avant d’avoir identifié les fondations réellement disponibles.

---

# Étape 1 — Audit de ce qui existe déjà

Inspecter :

```text
GameContext
Player state
Enemy state
Timeline
Frames
Gold
Inventory
Item Knowledge
Champion Knowledge
Rune Knowledge
Damage metrics
Resistance / penetration
Formula foundation
Stat ownership
Death Analyzer
Golden Games
Tests
```

Le but est de réutiliser les fondations existantes.

Créer un court rapport :

```text
BUILD_OPTIMIZER_AUDIT.md
```

avec :

```text
REUSED
EXTENDED
MISSING
NOT NEEDED
BLOCKED
```

Avant de coder, expliquer l’architecture réelle prévue.

---

# Étape 2 — BuildContext

Créer une représentation propre de l’état nécessaire au Build Optimizer.

Cible conceptuelle :

```python
BuildContext(
    champion=...,
    role=...,
    level=...,
    timestamp=...,
    gold=...,
    inventory=...,
    allies=...,
    enemies=...,
    enemy_items=...,
    game_state=...
)
```

Le `BuildContext` doit venir de la Stable Base.

Interdiction de parser directement les JSON Riot dans plusieurs endroits du moteur.

Tests obligatoires :

```text
valid context
missing data
empty inventory
full inventory
invalid timestamp
unknown item
unknown champion
```

---

# Étape 3 — Item Knowledge utilisable par le moteur

Réutiliser la fondation Item Knowledge déjà FROZEN.

Le Build Optimizer doit pouvoir obtenir proprement :

```text
item id
name
total cost
base cost
components
builds into
stats
tags
purchasable
restrictions
```

Ne pas mélanger :

```text
Raw Data Dragon
Knowledge
Scoring
```

Ils doivent rester séparés.

Si certains passifs ne peuvent pas encore être interprétés proprement, ne pas inventer de pseudo-valeurs.

Les marquer :

```text
UNMODELED
PARTIAL
SUPPORTED
```

---

# Étape 4 — Candidate Generator

Créer un composant qui génère seulement les achats plausibles.

Il doit éliminer :

```text
items non achetables
items spéciaux
items hors mode
items incompatibles
doublons interdits
achats impossibles
```

Il doit tenir compte :

```text
gold
inventory
components possédés
slots
recette actuelle
```

Il doit distinguer :

```text
TARGET ITEM
BUY NOW
FUTURE ALTERNATIVE
```

Important :

Le Candidate Generator ne décide pas encore du meilleur item.

---

# Étape 5 — Scoring Engine v1

Le moteur doit être déterministe.

Cible :

```text
FinalScore =
ChampionSynergy
+ EnemyCounter
+ CurrentBuildSynergy
+ GameNeed
+ PowerSpikeValue
+ EconomyValue
+ PurchaseFeasibility
- RedundancyPenalty
- IncompatibilityPenalty
```

Chaque scorer doit être indépendant.

---

## Champion Synergy

Analyser uniquement ce qu’on peut réellement supporter :

```text
AP
AD
AS
HP
armor
MR
ability haste
penetration
on-hit
etc.
```

Utiliser les fondations champion / spell / formula existantes si elles permettent une conclusion fiable.

Ne pas inventer une synergie non supportée.

---

## Enemy Counter

Prendre en compte si disponibles :

```text
enemy HP
armor
MR
healing
shielding
CC
AD threat
AP threat
frontline
```

---

## Current Build Synergy

Détecter :

```text
redondance
complémentarité
cohérence du build
composants déjà possédés
```

---

## Game Need

Utiliser uniquement les métriques fiables :

```text
besoin DPS
besoin survivabilité
anti-tank
anti-heal
penetration
defensive need
```

Ne pas utiliser une métrique EXPERIMENTAL sans l’indiquer.

---

## Economy

Prendre en compte :

```text
gold disponible
coût restant
composants possédés
achat immédiat
efficacité du prochain spike
```

---

# Étape 6 — Score Breakdown

Chaque item doit produire quelque chose de ce type :

```text
Liandry's Torment

Champion Synergy       17
Enemy Counter          19
Build Synergy          14
Game Need              16
Economy                  9
Purchase Feasibility     8
Redundancy              -2

FINAL                   81
```

Les poids doivent être centralisés dans un endroit clair.

Exemple :

```python
BUILD_SCORE_WEIGHTS = {...}
```

Pas de nombres magiques dispersés.

---

# Étape 7 — Purchase Optimizer minimal

Différencier :

```text
TARGET ITEM
```

et :

```text
BUY NOW
```

Exemple :

```text
Current gold:
2050

Target:
Liandry

Buy now:
Blasting Wand
Amplifying Tome
```

Le moteur doit gérer :

```text
budget exact
budget insuffisant
plusieurs composants possibles
composants déjà possédés
item complet accessible
slots limités
```

Ce n’est PAS encore le Recall Optimizer.

---

# Étape 8 — Explanation Engine

Toute recommandation doit être expliquée par les facteurs du scoring réel.

Exemple :

```text
Liandry — 87.4

+ deux ennemis très tanky
+ forte valeur en combat prolongé
+ bon complément au build actuel
+ composant important achetable maintenant

- moins défensif contre la menace physique principale
```

Interdiction de générer une raison qui n’a aucune contribution réelle au score.

Retourner :

```text
positive reasons
negative reasons
warnings
confidence / limitations si utile
```

---

# Étape 9 — Alternatives

Le moteur doit retourner :

```text
Main recommendation
Offensive alternative
Defensive alternative
```

si pertinent.

Exemple :

```text
MAIN
Liandry

DEFENSIVE
Zhonya

SWITCH CONDITION
Vi devient la principale menace et te cible régulièrement
```

La condition doit provenir de métriques réelles.

---

# Étape 10 — Scénarios de référence

Créer au minimum ces scénarios :

```text
1. Shyvana AP vs double tank
2. Shyvana AP vs full squishy
3. grosse menace AD
4. grosse menace AP
5. forte MR ennemie
6. gros healing adverse
7. inventaire partiellement construit
8. faible gold
9. gold suffisant pour gros composant
10. gold suffisant pour item complet
```

Chaque scénario doit tester :

```text
candidate validity
score coherence
purchase validity
explanation validity
```

Ne pas forcément forcer un item exact si les fondations ne permettent pas encore une certitude suffisante.

---

# Étape 11 — Historical Replay

Réutiliser les Golden Games.

Tester plusieurs timestamps :

```text
10:00
15:00
20:00
25:00
```

À chaque instant reconstruire :

```text
inventory
gold
level
known enemy items
enemy state
game context
```

Puis exécuter le Build Optimizer.

Règle absolue :

```text
NO FUTURE LEAKAGE
```

À 15:00, le moteur ne doit pas connaître les items ou événements de 25:00.

Créer un test spécifique de temporal integrity.

---

# Étape 12 — Évaluation

Ne pas considérer l’item réellement acheté par le joueur comme vérité absolue.

Classer chaque recommandation :

```text
GOOD
PLAUSIBLE
QUESTIONABLE
WRONG
BUG
```

Corriger :

```text
BUG
WRONG évident
```

avant freeze.

Les `QUESTIONABLE` doivent être documentés.

---

# Étape 13 — API finale

Cible :

```python
recommendation = optimizer.recommend(context)
```

Sortie minimale :

```python
BuildRecommendation(
    target_item=...,
    buy_now=[...],
    score=...,
    score_breakdown=...,
    alternatives=[...],
    reasons=[...],
    warnings=[...],
    timestamp=...
)
```

La sortie doit être sérialisable.

Pas de dépendance UI.

---

# Étape 14 — End-to-End

Pipeline final :

```text
Historical Match
        ↓
Timeline Snapshot
        ↓
GameContext
        ↓
BuildContext
        ↓
Candidate Generator
        ↓
Scoring Engine
        ↓
Purchase Optimizer
        ↓
Explanation Engine
        ↓
BuildRecommendation
```

Tester :

```text
unit
integration
Golden Games
historical replay
batch games
Stable Base regression
```

---

# Étape 15 — Zero Gate

Avant freeze, produire un rapport du type :

```text
BUILD OPTIMIZER V1 ZERO GATE

Stable Base regression          PASS
Unit tests                      PASS
Scenario tests                  PASS
Historical replay               PASS
Temporal integrity              PASS
Invalid purchase count          0
Future information leakage      0
Unexplained recommendations     0
Fatal scoring errors            0
git diff --check                PASS
```

Si un gate critique échoue :

```text
NO FREEZE
```

---

# Étape 16 — Freeze

Seulement si tout est valide :

Créer un commit du type :

```text
Freeze Build Optimizer foundation v1
```

Mettre à jour :

```text
TODO.md
LAST_RUN.md
FROZEN_FILES
documentation pertinente
```

Marquer :

```text
Build Optimizer v1 — FROZEN
```

Ne commencer aucun successeur.

Créer ensuite un second commit de vérification uniquement si nécessaire :

```text
Record Build Optimizer v1 freeze verification
```

---

# État attendu à la fin

```text
Stable Base                         FROZEN
Item Knowledge                      FROZEN
Champion Knowledge                  FROZEN
Rune Knowledge                      FROZEN
Combat foundations                  FROZEN
Build Optimizer v1                  FROZEN
```

Avec un moteur capable de produire :

```text
Game state
    ↓
Best target item
    ↓
Best purchase now
    ↓
Alternatives
    ↓
Score breakdown
    ↓
Explanation
```

---

# Ce qu'il ne faut PAS commencer après le freeze

Ne démarre pas automatiquement :

```text
Adaptive Build
Recall Optimizer
Threat Analyzer v2
Live Overlay
Machine Learning
```

Le successeur sera décidé après review du freeze.
