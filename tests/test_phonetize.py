from ostilhou import phonetize
from ostilhou.asr import lexicon_add, lexicon_sub


def test_phonetize():
    
    assert len(phonetize("the")) == 2
    assert len(phonetize("world")) == 1
    assert len(phonetize("bepred")) == 4

    assert phonetize("Monique") == ['M O N I K']
    assert phonetize("Marie-Jeanne") == ['M A R I J A N']
    assert phonetize("tra-mañ-tra") == ['T R A M AN T R A']