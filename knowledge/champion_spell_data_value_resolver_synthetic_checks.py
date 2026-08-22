from knowledge.champion_spell_data_value_resolver import *

def main():
    registry = build_registry([{"name":"Exact","values":[0,2]}, {"name":"Dup","values":[1]}, {"name":"Dup","values":[2]}])
    assert resolve_data_value(registry,"Exact",1,1,indexing_contract=None)["value"] == 2
    assert resolve_data_value(registry,"exact",1,1)["status"] == DATA_VALUE_NOT_FOUND
    assert resolve_data_value(registry,"Dup",1,1)["status"] == DATA_VALUE_AMBIGUOUS
    print("Spell DataValue resolver synthetic checks: PASS (3/3)")

if __name__ == "__main__": main()
