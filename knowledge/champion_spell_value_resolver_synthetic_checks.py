from knowledge.champion_spell_value_resolver import *

def main():
    cases = [
        (resolve_rank_value([0,10,20],1,2), VALUE_RESOLVED, 10),
        (resolve_rank_value([0,5],0,1), VALUE_RESOLVED, 0),
        (resolve_rank_value([7],3,5), VALUE_RESOLVED, 7),
        (resolve_rank_value([1,2],3,5), VALUE_SHAPE_UNSUPPORTED, None),
        (resolve_rank_value([1,2,3],4,3), INVALID_SPELL_RANK, None),
        (resolve_rank_value(["x"],1,1), NON_NUMERIC_VALUE, None),
        (resolve_rank_value([0.1,0.2],2,2), VALUE_RESOLVED, 0.2),
    ]
    for result, status, value in cases:
        assert result["status"] == status and result["value"] == value
    print("Spell value resolver synthetic checks: PASS (7/7)")

if __name__ == "__main__": main()
