from ostilhou import phonetize_word
from ostilhou.asr import lexicon_add, lexicon_sub


def test_phonetize():
    
    assert len(phonetize_word("the")) == 2
    assert len(phonetize_word("world")) == 1
    assert len(phonetize_word("bepred")) == 4

    assert phonetize_word("Monique") == ['M O N I K']
    assert phonetize_word("Marie-Jeanne") == ['M A R I J A N']
    assert phonetize_word("tra-mañ-tra") == ['T R A M AN T R A']

    # Acronyms
    assert phonetize_word("QR") == ['K U EH R']
    assert phonetize_word("BZH") == ['B E Z E D A CH']

    # Fillers
    assert phonetize_word("tiens") == ['T I EN']

    # Single letters spelled out
    assert phonetize_word("B") == ['B E']
    assert phonetize_word("Ñ") == ['EH N T I L D E']