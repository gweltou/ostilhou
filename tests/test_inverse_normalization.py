from ostilhou.text import inverse_normalize_sentence, inverse_normalize_vosk


test_cases = [
    ("un den", "un den"),
    ("ur marc'h", "ur marc'h"),
    ("peder plac'h", "4 plac'h"),
    ("ur c'hant bennak a dud", "100 bennak a dud"),
    ("er bloavez mil nav c'hant pevar ha pevar-ugent", "er bloavez 1984"),
    ("naontek kant c'hwec'h ha tregont", "1936"),
    ("kant daou vil pevarzek", "102014"),
    ("unan daou tri staget mat ar c'hi", "unan daou tri staget mat ar c'hi"),
    ("seizh eizh nav deomp da c’hoari atav", "7 8 9 deomp da c’hoari atav"),
    ("kant tri patatezenn hag hanter-kant am eus debret", "153 patatezenn am eus debret"),
    ("dek den mil kazh", "10 den 1000 kazh"),
    ("pemp kazh ha c'hwec'h pesk", "5 kazh ha 6 pesk"),
    ("daou gorn-boud warn-ugent", "22 gorn-boud"),
    ("ar c'hoant da zaou vil daou ha tregont", "ar c'hoant da 2032"),
    ("kant den hag hanter-kant a oa", "150 den a oa"),
    ("div blac'h kozh ha daou-ugent", "42 blac'h kozh"),
    ("div blac'h kozh ha daou-ugent kazh du", "2 blac'h kozh ha 42 kazh du"),
    ("div blac'h kozh ha daou-ugent aet d'an anaon", "42 blac'h kozh aet d'an anaon"),
]


def test_inverse_normalization():

    def should_be(s1: str, s2: str) -> None:
        normalized = inverse_normalize_sentence(s1, min_num=4)
        print(normalized)
        assert s2 == normalized

    for query, expected in test_cases:
        should_be(query, expected)



def test_inverse_normalization_vosk():

    def should_be(s1: str, s2: str) -> None:
        s1 = [{"word":t, "start":2*i, "end":2*i+1, "conf":1.0} for i, t in enumerate(s1.split())]
        tokens = inverse_normalize_vosk(s1, min_num=4)
        # Check timecode order
        for i in range(len(tokens)-1):
            assert tokens[i]["start"] < tokens[i+1]["start"]
        normalized = ' '.join( [t["word"] for t in tokens] )
        print(normalized)
        assert s2 == normalized

    for query, expected in test_cases:
        should_be(query, expected)
    