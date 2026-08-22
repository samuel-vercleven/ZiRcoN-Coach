from knowledge.spell_damage_mitigation import mitigate_component
def main():
    a={"stats":{"armor_penetration_percent":0,"armor_penetration_flat":0,"lethality":0,"magic_penetration_percent":0,"magic_penetration_flat":0}}; t={"stats":{"armor":100,"armor_native":100,"magic_resistance":25}}
    base={"status":"RAW_DAMAGE_RESOLVED","raw_damage":100}
    assert mitigate_component({**base,"damage_type":"PHYSICAL"},a,t)["post_mitigation_damage"]==50
    assert mitigate_component({**base,"damage_type":"MAGIC"},a,t)["post_mitigation_damage"]==80
    assert mitigate_component({**base,"damage_type":"TRUE"},a,t)["post_mitigation_damage"]==100
    print("Spell damage mitigation synthetic checks: PASS (3/3)")
if __name__=="__main__": main()
