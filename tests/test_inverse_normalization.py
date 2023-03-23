from ostilhou.text import inverse_normalize_sentence

def test_inverse_normalization():

    def should_be(s1: str, s2: str) -> None:
        normalized = inverse_normalize_sentence(s1)
        print(normalized)
        assert s2 == normalized

    should_be("un den", "1 den")
    should_be("ur marc'h", "1 marc'h")
    should_be("ur c'hant bennak a dud", "100 bennak a dud")
    should_be("mil daou", "1002")
    should_be("mil nav c'hant pevar ha pevar-ugent", "1984")
    should_be("naontek kant c'hwec'h ha tregont", "1936")
    should_be("er bloavez daou vil tri warn-ugent", "er bloavez 2023")
    should_be("kant den hag hanter-kant a oa", "150 den a oa")
    should_be("kant daou vil pevarzek", "102014")
    should_be("tri kazh ha daou besk", "3 kazh ha 2 besk")
    should_be("unan daou tri, staget mat ar c'hi", "1 2 3, staget mat ar c'hi")
    should_be("div blac'h kozh ha daou-ugent", "42 blac'h kozh")
    should_be("div blac'h kozh ha daou-ugent kazh du", "2 blac'h kozh ha 42 kazh du")
    should_be("div blac'h kozh ha daou-ugent aet d'an anaon", "42 blac'h kozh aet d'an anaon")
    should_be("kant tri patatezenn hag hanter-kant em eus debret", "153 patatezenn am eus debret")