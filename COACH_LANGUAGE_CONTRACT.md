# Coach : textes situationnels et préparation LLM

## Ce qui est actif

Le coach compose toujours ses conseils localement à partir des sorties actuelles.
Seuls les constats explicitement soutenus et les rapports disponibles/partiels
sont admis ; la priorité et la limite d’une carte par famille sont inchangées.

Une carte affiche un constat court et un réflexe. Les détails dépliables donnent :
pourquoi revoir, question de replay, option conditionnelle, vérification à la
prochaine revue, repères et limites. Rien ne prétend connaître une vision,
une intention, un trajet exact ou un cooldown absent des données.

Situations distinguées : mort à revoir, retard/avance de ressources, morts
rapprochées, période de déplacements, reprise boutique neutre/après mort,
suivie d’une mort, avant/après/entre des objectifs enregistrés.
Un objectif pris après le passage boutique n’est pas un délai d’apparition.

## Contrat préparé, aucun modèle connecté

`services/coaching_narrative.py` fournit un paquet minimal et un schéma JSON
indépendants du fournisseur. Pas de SDK, pas de clé de modèle, pas de requête
réseau, pas d’entraînement. Le champ `network_enabled` reste faux.

```python
from services.coaching_narrative import build_packet, response_schema, render_or_fallback

# Rapport courant du joueur, obtenu par le service d’analyse existant.
packet = build_packet(current_report)
schema = response_schema(packet)
display = render_or_fallback(packet)  # texte déterministe si aucun modèle
```

Le paquet n’exporte pas le match ID, le PUUID, le Riot ID, les notes privées,
les clés ou le rapport brut. Il porte des faits sélectionnés avec leur source,
des limites/inconnues explicites et des formulations déjà approuvées.
Les données ne doivent jamais être interprétées comme des instructions.
L’identifiant du paquet lie la réponse au contexte précis, avec un jeton opaque.

### Premier mode d’intégration : sélection contrôlée

La réponse choisit des identifiants de formulations par champ et par carte.
Elle ne peut pas ajouter du texte, changer la priorité ou supprimer les nuances.
Les variantes relèvent de la présentation, pas d’un nouveau conseil tactique.

```json
{
  "packet_id": "identifiant_du_paquet_courant",
  "selections": [{
    "card_id": "c1",
    "fields": {
      "title": "title:direct",
      "observation": "observation:direct",
      "why_review": "why_review:direct",
      "next_game_experiment": "next_game_experiment:direct",
      "review_question": "review_question:guided",
      "conditional_alternative": "conditional_alternative:direct",
      "experiment_check": "experiment_check:direct",
      "limitation": "limitation:direct"
    }
  }]
}
```

`validate_selection` rejette réponse ancienne, texte libre, identifiants inconnus,
cartes réordonnées, champs manquants/supplémentaires et clés JSON dupliquées.
`render_or_fallback` conserve les textes déterministes en cas d’erreur ou d’absence
de réponse. Un schéma vide reste une abstention, pas une invitation à inventer.

## Suite à décider séparément

Choix du fournisseur/modèle, local ou cloud, latence, budget et autorisation
d’envoi de données. La génération libre de nouvelles phrases n’est pas activée :
un filtre de mots-clés ne prouverait pas leur exactitude. Elle nécessitera des
évaluations de fidélité, des cas adverses et une revue avant application automatique.

Les tests locaux vérifient cette frontière, pas la qualité d’un modèle non branché.
L’audit sur 143 rapports de parties expose 247 cartes et 11 situations ; cela ne
valide pas les conseils comme des décisions optimales ou causales. NO FREEZE.
