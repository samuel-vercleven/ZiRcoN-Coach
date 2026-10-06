"""Situational copy and offline language-boundary regression checks."""
from copy import deepcopy
import json
import unittest

from ui.player_coach import coaching_focuses
from viewmodels import CoachingReport, InsightViewModel
from services.coaching_narrative import build_packet, response_schema, render_or_fallback, validate_selection, FIELDS


def report(family='resets', *, origin='proxy de reset volontaire', timing='aucune', context=(), supported=True, metrics=(), events=None):
    event = {'title': 'Reset / shop à 03:35' if family == 'resets' else 'Mort à 03:35',
             'metrics': [{'label': 'Origine', 'value': origin}, {'label': 'Timing objectif', 'value': timing},
                         {'label': 'Production après reset vs historique', 'value': '5.2/100 · faible'}, *metrics],
             'context': list(context)}
    return CoachingReport('PRIVATE_MATCH_ID', (InsightViewModel(family.upper(), family, 'x', status='AVAILABLE',
                           source_module=family, source_version='accepted_version',
                           findings=({'title': 'Situation à 03:35', 'detail': 'Signal étayé', 'supported': supported, 'severity': 'MEDIUM'},),
                           events=tuple(events) if events is not None else (event,)),), 'AVAILABLE')


class LanguageChecks(unittest.TestCase):
    def focus(self, **kwargs):
        return coaching_focuses(report(**kwargs))[0]

    def test_shop_after_death_is_not_a_voluntary_recall_error(self):
        focus = self.focus(origin='retour après mort', timing='avant un objectif')
        self.assertEqual(focus.situation_id, 'shop_after_death')
        self.assertIn('réapparition', focus.next_game_experiment)

    def test_shop_followed_by_death_remains_non_causal(self):
        focus = self.focus(context=('mort observée dans les 120 s après le proxy de reset',))
        self.assertEqual(focus.situation_id, 'shop_followed_by_death')
        self.assertIn('sans en conclure', focus.why_review)
        self.assertIn('ne prouvent pas', focus.conditional_alternative)
        self.assertNotIn('5.2', focus.observation)

    def test_objective_before_is_not_spawn_countdown(self):
        focus = self.focus(timing='avant un objectif')
        self.assertEqual(focus.situation_id, 'shop_before_objective')
        self.assertIn('pas un compte à rebours', focus.why_review)
        self.assertNotIn('temps restant', focus.next_game_experiment)

    def test_after_and_between_are_not_upcoming_objective_advice(self):
        self.assertEqual(self.focus(timing='après un objectif').situation_id, 'shop_after_objective')
        self.assertEqual(self.focus(timing='entre deux objectifs').situation_id, 'shop_between_objectives')

    def test_unknown_and_negative_objective_context_does_not_promote(self):
        for value in ('aucune', 'inconnu', 'pas d’objectif proche', 'objectif inconnu', '—'):
            self.assertEqual(self.focus(timing=value).situation_id, 'shop_restart_review')

    def test_before_and_after_death_states_give_distinct_prompts(self):
        behind = self.focus(family='death', metrics=({'label': 'État avant la mort', 'value': 'en retard'},))
        ahead = self.focus(family='death', metrics=({'label': 'État avant la mort', 'value': 'en avance'},))
        self.assertNotEqual(behind.situation_id, ahead.situation_id)
        self.assertNotEqual(behind.next_game_experiment, ahead.next_game_experiment)
        self.assertIn('03:35', behind.observation)

    def test_ambiguous_event_clock_does_not_guess_state(self):
        events = ({'title': 'Mort à 03:35', 'metrics': [{'label': 'État avant la mort', 'value': 'AHEAD'}]},
                  {'title': 'Mort à 03:35', 'metrics': [{'label': 'État avant la mort', 'value': 'BEHIND'}]})
        self.assertEqual(self.focus(family='death', events=events).situation_id, 'death_review')

    def test_unsupported_report_abstains(self):
        packet = build_packet(report(supported=False), 'opaque')
        self.assertEqual(packet['status'], 'ABSTAIN')
        self.assertEqual(packet['data']['cards'], [])
        self.assertEqual(render_or_fallback(packet)['cards'], [])

    def packet(self):
        return build_packet(report(context=('mort observée dans les 120 s après le proxy de reset',)), 'opaque')

    def response(self, packet):
        return {'packet_id': packet['packet_id'], 'selections': [
            {'card_id': card['id'], 'fields': {field: options[0]['id'] for field, options in card['approved_fields'].items()}}
            for card in packet['data']['cards']]}

    def test_packet_is_anonymous_and_has_explicit_unknowns(self):
        packet = self.packet()
        self.assertNotIn('PRIVATE_MATCH_ID', json.dumps(packet))
        self.assertFalse(packet['network_enabled'])
        self.assertIn('player_visible_information', packet['data']['unknowns'])
        self.assertIn('objective_spawn_countdown', packet['data']['unknowns'])
        self.assertEqual(set(packet['data']['cards'][0]['approved_fields']), set(FIELDS))

    def test_schema_restricts_words_to_ids(self):
        schema = response_schema(self.packet())
        self.assertFalse(schema['additionalProperties'])
        self.assertEqual(schema['properties']['selections']['minItems'], 1)

    def test_valid_selection_preserves_facts_and_conditions(self):
        packet = self.packet(); before = deepcopy(packet)
        result = render_or_fallback(packet, self.response(packet))
        self.assertEqual(result['status'], 'APPROVED_SELECTION')
        self.assertEqual(packet, before)
        self.assertEqual(result['cards'][0]['observation'], packet['data']['cards'][0]['fallback']['observation'])

    def test_free_text_hallucination_is_rejected_and_falls_back(self):
        packet = self.packet(); response = self.response(packet)
        response['selections'][0]['fields']['observation'] = 'Tu es mort sans vision et tu as perdu la partie.'
        self.assertEqual(render_or_fallback(packet, response)['status'], 'DETERMINISTIC_FALLBACK')
        self.assertNotIn('Tu es mort sans vision', json.dumps(render_or_fallback(packet, response)))

    def test_stale_response_is_rejected(self):
        packet = self.packet(); response = self.response(packet)
        response['packet_id'] = 'previous-game'
        with self.assertRaises(ValueError): validate_selection(packet, response)

    def test_missing_extra_and_unknown_fields_are_rejected(self):
        packet = self.packet()
        for mode in ('missing', 'extra', 'id'):
            response = self.response(packet)
            if mode == 'missing': response['selections'][0]['fields'].pop('limitation')
            if mode == 'extra': response['reasoning'] = 'Invented extra reasoning'
            if mode == 'id': response['selections'][0]['card_id'] = 'unknown'
            self.assertEqual(render_or_fallback(packet, response)['status'], 'DETERMINISTIC_FALLBACK')

    def test_duplicate_json_keys_and_oversized_response_are_rejected(self):
        packet = self.packet()
        self.assertEqual(render_or_fallback(packet, '{"packet_id":"x","packet_id":"y","selections":[]}')['status'], 'DETERMINISTIC_FALLBACK')
        self.assertEqual(render_or_fallback(packet, 'x' * 16001)['status'], 'DETERMINISTIC_FALLBACK')

    def test_guided_variant_retains_original_question(self):
        packet = self.packet(); response = self.response(packet)
        response['selections'][0]['fields']['review_question'] = 'review_question:guided'
        output = validate_selection(packet, response)[0]
        self.assertTrue(output['review_question'].endswith(packet['data']['cards'][0]['fallback']['review_question']))


if __name__ == '__main__':
    unittest.main()
