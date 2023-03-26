from typing import List
from ostilhou.dicts import proper_nouns, nouns_f, nouns_m


def reverse_mutation(word: str) -> List[str]:
    """ returns the list of possible reverse-mutated candidates
        from a mutated (or not) word.
        Note that many candidates won't have meaning
    """
    first_letter = word[0].lower()
    is_cap = word[0].isupper()
    candidates = []

    if word.lower().startswith("c'h"):
        candidates.append('k' + word[3:])
        candidates.append('g' + word[3:])
    elif first_letter == 'w':
        candidates.append('g' + word[:])
    elif first_letter == 'z':
        candidates.append('t' + word[1:])
        candidates.append('d' + word[1:])
    elif first_letter == 'f':
        candidates.append('p' + word[1:])
    elif first_letter == 'k':
        candidates.append('g' + word[1:])
    elif first_letter == 't':
        candidates.append('d' + word[1:])
    elif first_letter == 'p':
        candidates.append('b' + word[1:])
    elif first_letter == 'g':
        candidates.append('k' + word[1:])
    elif first_letter == 'd':
        candidates.append('t' + word[1:])
    elif first_letter == 'b':
        candidates.append('p' + word[1:])
    elif first_letter == 'v':
        candidates.append('b' + word[1:])
        candidates.append('m' + word[1:])
    
    if is_cap:
        candidates = [ w[0].upper() + w[1:] for w in candidates]
    return candidates



def is_noun_f(word: str) -> bool:
    if len(word) < 2:
        return False
    
    word = word.lower()
    if word in nouns_f:
        return True
    for candidate in reverse_mutation(word):
        if candidate in nouns_f:
            return True
    return False


def is_noun_m(word: str) -> bool:
    if len(word) < 2:
        return False

    word = word.lower()
    if word in nouns_m:
        return True
    for candidate in reverse_mutation(word):
        if candidate in nouns_m:
            return True
    return False


def is_noun(word: str) -> bool:
    return is_noun_m(word) or is_noun_f(word)