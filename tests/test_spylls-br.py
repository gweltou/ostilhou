from ostilhou.hspell import get_hunspell_spylls


def test_spylls():
    dictionary = get_hunspell_spylls()
    
    print(dictionary.lookup('spylls'))

    for suggestion in dictionary.suggest('spylls'):
        print(suggestion)