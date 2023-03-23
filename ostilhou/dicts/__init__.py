import os
from ..asr import phonetize, acr2f


# Proper nouns dictionary
# with phonemes when name has a foreign or particular pronunciations
# Beware, entries are lowercase

proper_nouns = dict()
_proper_nouns_phon_path = __file__.replace("__init__.py", "proper_nouns_phon.txt")

with open(_proper_nouns_phon_path, 'r') as f:
    for l in f.readlines():
        l = l.strip()
        w, *pron = l.strip().split()
        if not pron:
            pron = phonetize(w)
        if w.lower() in proper_nouns:
            proper_nouns[w.lower()].append(' '.join(pron))
        else:
            proper_nouns[w.lower()] = [' '.join(pron)]


# Noun dictionary
# Things that you can count
nouns = set()
_nouns_path = __file__.replace("__init__.py", "nouns.txt")

nouns.update(["bloaz"])


# Acronyms

_acronyms_path = __file__.replace("__init__.py", "acronyms.txt")

def get_acronyms_dict():
    """
        Acronyms are stored in UPPERCASE in dictionary
    """
    acronyms = dict()
    for l in "BCDFGHIJKLMPQRSTUVWXZ":
        acronyms[l] = [acr2f[l]]
    
    if os.path.exists(_acronyms_path):
        with open(_acronyms_path, 'r') as f:
            for l in f.readlines():
                if l.startswith('#') or not l: continue
                acr, *pron = l.split()
                if acr in acronyms:
                    acronyms[acr].append(' '.join(pron))
                else:
                    acronyms[acr] = [' '.join(pron)]
    else:
        print("Acronym dictionary not found... creating file")
        open(_acronyms_path, 'a').close()
    return acronyms

acronyms = get_acronyms_dict()