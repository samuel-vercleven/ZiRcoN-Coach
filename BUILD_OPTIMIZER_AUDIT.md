# Build Optimizer v1 — audit préalable

Baseline : `9b9af010885acf19b647d0c75d763f628e8f5d2b`, branche
`feature/build-optimizer`, 2026-09-08. Aucun fichier FROZEN modifié.
`main.py` PASS ; 43/43 suites Stable Base PASS, compilation de 159 modules,
89 chemins FROZEN inchangés. Journaux : `logs/build_optimizer/baseline/`.
Les six suppressions locales de documents de stabilisation sont préexistantes
et ne sont ni restaurées ni incluses dans les commits de cette mission.

## Contextual pass v1 — 2026-09-10

REUSED: GameContext prefix projection, frozen Item Knowledge facts, v22 recipe
consumption and historical mutation framework. EXTENDED: totalGold observations,
read-only legality and semantic contracts, phase-bucketed prior-match baseline,
Shyvana AP heuristic scoring and traceable explanations. MISSING: no formal
client rules engine or combat simulation; neither is claimed.

The only supported champion profile is `shyvana_ap_build_profile_v1`. Semantic
profiles are reviewed literal contracts for eight major AP SR item IDs, fingerprinted
by exact patch, price and direct recipe. They are not description parsing at runtime.
Supported patches are 16.9/16.16/16.17/16.18; any other patch fails closed.

Legality is `LEGAL_SUPPORTED` only for that explicit whitelist after frozen Item
Knowledge SR/purchasable/in-store/graph checks, v1 duplicate policy and a valid
recipe plan. Boots, consumables, trinkets, starters/pets, support/quest/special,
mode-specific and champion-specific items remain excluded. Shop presence is not
known: the plan is `IF_SHOPPING_NOW` only.

## Interfaces réelles et admissibilité

| Fondation | Classement | Interface / décision |
|---|---|---|
| GameContext | REUSED | `services.game_context.GameContext` ; données locales validées, mais contient toute la partie et les items finaux. Ne jamais transmettre l'objet entier au scorer. |
| Player / Enemy / Timeline / Frames / Gold | EXTENDED | Projection vers un petit BuildContext à timestamp explicite ; allowlist des identités et des champs de frame. Pas de niveau final, résultat, durée finale, statistiques finales ou gold futur. |
| Inventory v22 | REUSED | `reconstruct_item_timeline(meta, events, ItemCatalog)` sur le seul préfixe. Ne pas utiliser `build_itemization_history` puis filtrer : la fiabilité dépend d'acquisitions/remplacements ultérieurs et du compteur final. |
| Fiabilité temporelle inventaire | EXTENDED | Une transaction ambiguë ou warning reste PARTIAL dans la projection. Pas de restauration rétrospective d'un état fiable. Grants/transformations non observés restent non exécutables. |
| Item Knowledge 2A | REUSED | `build_item_knowledge_catalog(..., raw_items, versions)` ; coût total/base, composants avec multiplicité, graphe, stats et provenance. Fallback latest refusé. |
| Restrictions d'achat exhaustives | MISSING | `applicability` expose map, purchasable, requiredChampion, inStore, classes ; aucun contrat complet des groupes mutuellement exclusifs, restrictions liées aux runes/quêtes ou accès magasin. L'absence d'un champ n'est pas preuve d'absence de restriction. |
| Champion Knowledge 2B1 | REUSED | Identité et provenance patch ; tags et descriptions ne valident ni AP/AD synergy ni force d'un matchup. |
| Rune Knowledge 2C1 | REUSED | Identités/perks et source du grant Magical Footwear, pas d'exécution des effets. |
| Level stats 2D | BLOCKED | AS pin 16.16 non transposable au patch 16.17. Pas nécessaire au calcul de coût d'une recette. |
| Resistance / penetration 2E | NOT_NEEDED | Math disponible, mais ne fournit ni profil de dégâts futur ni valeur marginale globale d'un item. Pas de duplication. |
| Spell source 2F | REUSED | Provenance structurelle consultée ; pas d'exécution ajoutée. |
| Formula foundation 2G | BLOCKED | Zéro composant réel de dégâts résolu ; 13 calculs arithmétiques résolus ne sont pas 13 sorts exécutables. |
| Stat references 2H / owners 2I | BLOCKED | 0/569 owner exécutable ; ne pas convertir CONTEXT_DEPENDENT en CASTER. |
| Death v11 et statistiques | NOT_NEEDED | Coûts post-mort et références historiques ne constituent pas un scorer marginal d'items à t. Ne pas injecter des fenêtres futures ou des interprétations EXPERIMENTAL comme une vérité combat. |
| Golden Games | REUSED | Sept paires brutes locales avec SHA-256 et faits vérifiés ; nouveaux replays 10/15/20/25 minutes distincts de l'audit post-game. |
| Scoring champion/counter/game need | MISSING | Aucun contrat numérique validé de contribution item -> utilité contextuelle. Les poids de l'exemple utilisateur ne sont pas une calibration ni une preuve. |

## Architecture autorisée sans changer les fondations

```text
GameContext existant -> projection temporelle BuildContext
Item Knowledge existant -> vue coût/recettes/provenance
                       -> candidats structurels + plans budget/slots
                       -> contributions économiques diagnostiques
                       -> recommandation explicite ou abstention motivée
```

Le module n'a ni dépendance UI, ni réseau implicite, ni lecture SQLite dans le
scorer. L'audit historique injecte les catalogues exacts et les GameContexts.
La planification de recette ne devient pas une preuve d'achat légal dans le
client. Les plans diagnostiques sont distincts de `buy_now`.

## Limite de décision avant implémentation importante

Les branches indépendantes peuvent être construites et testées : projection,
recettes, coût restant, slots, sérialisation, absence de fuite, abstention.
Une recommandation du « meilleur achat » ne sera pas fabriquée en classant
simplement les dépenses ou les tags. ChampionSynergy, EnemyCounter, GameNeed,
PowerSpikeValue et restrictions sans preuve restent UNMODELED.
Sans contrat d'admissibilité des achats et de scoring défendable, le gate
produit reste BLOCKED / NO FREEZE, même si les invariants techniques passent.
Le rapport final distinguera tests d'abstention et recommandations réellement
validées ; zéro recommandation ne prouve pas la qualité du moteur demandé.

## Sources techniques

- Code local : `services/game_context.py`, `analysis/itemization_analyzer.py`
  (`_destroyed_evidence_context` utilise explicitement later/final),
  `knowledge/item_knowledge.py` (`classify_applicability`, `attach_item_graph`),
  `knowledge/champion_spell_stat_owner_semantics.py` (`build_execution_gate`).
- [Documentation officielle Riot — Data Dragon](https://developer.riotgames.com/docs/lol#data-dragon) : catalogues et versionnement, pas un contrat exhaustif d'achats contextuels.
- Catalogues Data Dragon exacts déjà conservés localement en 16.9.1, 16.16.1
  et 16.17.1. Aucun mapping issu d'un forum ou d'une table historique n'est admis.
