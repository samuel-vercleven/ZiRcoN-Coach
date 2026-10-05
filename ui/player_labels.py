"""Translate absent data at the presentation boundary, preserving stored values."""


def player_label(value, missing='—'):
    if value is None or str(value).strip() in ('', 'UNAVAILABLE', 'UNKNOWN', 'None'):
        return missing
    return {'Local player': 'Ton compte Riot', 'UNRANKED': 'Non classé'}.get(str(value), str(value))


def role_label(value):
    return {'TOP': 'Top', 'JUNGLE': 'Jungle', 'MIDDLE': 'Mid', 'BOTTOM': 'ADC', 'UTILITY': 'Support'}.get(value, player_label(value))
