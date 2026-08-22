from knowledge.champion_spell_value_resolver import *

def main():
    result = resolve_rank_value([0.0, 15.25, 30.5, 45.75], 2, 3)
    assert result["status"] == VALUE_RESOLVED and result["value"] == 30.5 and result["index"] == 2
    assert resolve_rank_value([0, 0, 10], 1, 2)["value"] == 0
    print("Spell value resolver precision checks: PASS (2/2)")

if __name__ == "__main__": main()
