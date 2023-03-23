from ..asr import phonetize


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