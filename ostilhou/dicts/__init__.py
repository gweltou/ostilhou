"""
Load various dictionaries from local resources

The option should be given to load user dictionaries as well, stored in a system folder
"""

import sys
import importlib.resources


# if dict_root is None:
#     if platform.system() in ("Linux", "Darwin"):
#         default = os.path.join(os.path.expanduser("~"), ".local", "share")
#     elif platform.system() == "Windows":
#         default = os.getenv("LOCALAPPDATA")
#     else:
#         raise OSError("Unsupported operating system")
#     dict_root = os.path.join(os.getenv("XDG_DATA_HOME", default), "anaouder", "dicts")
    
#     if not os.path.exists(dict_root):
#         os.makedirs(dict_root)

# Proper nouns dictionary
# with phonemes when name has a foreign or particular pronunciations

dicts = dict()



def load_dictionary_pron(file_path: str) -> dict:
    """Load a case-sensitive lexicon file, with optional pronuciations"""
    dictionary_pron = dict()

    try:
        with importlib.resources.files(__name__).joinpath(file_path).open('r', encoding='utf-8') as f:
            for l in f.readlines():
                comment_start = l.find('#')
                if comment_start >= 0:
                    l = l[:comment_start]
                l = l.strip()
                if not l: continue
                w, *pron = l.split(maxsplit=1)
                pron = pron or []
                
                if w in dictionary_pron and pron:
                    if pron[0] not in dictionary_pron[w]: # Avoid duplicate entries, which Kaldi hates
                        dictionary_pron[w].append(pron[0])
                else:
                    dictionary_pron[w] = pron
    except FileNotFoundError:
        print(f"Missing dictionary file {file_path}", file=sys.stderr)

    return dictionary_pron


def load_dictionary_comp_pron(file_path: str) -> dict:
    """
    Load a case-sensitive lexicon file, with optional pronuciations
    The dictionary's keys can be a compound word (separated with spaces)
    """
    dictionary_pron = dict()

    try:
        with importlib.resources.files(__name__).joinpath(file_path).open('r', encoding='utf-8') as f:
            for l in f.readlines():
                # comment_start = l.find('#')
                # print(l.strip(), comment_start)
                if comment_start := l.find('#') >= 0:
                # if comment_start >= 0:
                    l = l[:comment_start]
                l = l.strip()
                if not l: continue
                w, *pron = l.split('\t', maxsplit=1)
                pron = pron or []
                
                if w in dictionary_pron and pron:
                    if pron[0] not in dictionary_pron[w]: # Avoid duplicate entries, which Kaldi hates
                        dictionary_pron[w].append(pron[0])
                else:
                    dictionary_pron[w] = pron
    except FileNotFoundError:
        print(f"Missing dictionary file {file_path}", file=sys.stderr)

    return dictionary_pron


def augment_dict_mutations(d: dict):
    """
    Duplicate words that can be mutated.
    Modifies the dictionary in-place.
    """

    for k in list(d):
        first = k[0]
        first_maj = first.upper()
        if first_maj == 'P':
            mutation = 'B'
        elif first_maj == 'B':
            mutation = 'V'
        elif first_maj == 'M':
            mutation = 'V'
        elif first_maj == 'K':
            mutation = 'G'
        elif first_maj == 'T':
            mutation = 'D'
        # elif first_maj == 'G':
        #     mutation = "C'h"
        else:
            continue
        mutation = mutation.upper() if first.isupper() else mutation.lower()
        mutated_word = mutation + k[1:]
        mutated_prons = [ mutation.upper() + pron[1:] for pron in d[k] ]
        d[mutated_word] = mutated_prons



dicts["first_names"] = load_dictionary_pron("first_names.tsv")
dicts["last_names"] = load_dictionary_pron("last_names.tsv")
dicts["places"] = load_dictionary_pron("places.tsv")
dicts["proper_nouns"] = load_dictionary_pron("proper_nouns_phon.tsv")
dicts["countries"] = load_dictionary_comp_pron("countries_phon.tsv")
dicts["adjectives"] = load_dictionary_pron("adjectives.tsv")


# Apply breton mutations
for d in [
    "places",
    "first_names",
    "adjectives",
]:
    augment_dict_mutations(dicts[d])



# Nouns dictionary
# Things that you can count

def load_nouns_f():
    nouns_f = set()
    filepath = "noun_f.tsv"

    try:
        with importlib.resources.files(__name__).joinpath(filepath).open('r', encoding='utf-8') as f:
            
            for l in f.readlines():
                l = l.strip()
                if l.startswith('#') or not l: continue
                nouns_f.add(l)
        
        return nouns_f
    except FileNotFoundError:
        print(f"Missing dictionary file {filepath}", file=sys.stderr)
        return nouns_f

nouns_f = load_nouns_f()


def load_nouns_m():
    nouns_m = set()
    filepath = "noun_m.tsv"

    try:
        with importlib.resources.files(__name__).joinpath(filepath).open('r', encoding='utf-8') as f:
            for l in f.readlines():
                l = l.strip()
                if l.startswith('#') or not l: continue
                nouns_m.add(l)
        
        return nouns_m
    except FileNotFoundError:
        print(f"Missing dictionary file {filepath}", file=sys.stderr)
        return nouns_m

nouns_m = load_nouns_m()



# Acronyms dictionary

def load_acronyms():
    """
    Acronyms are stored in UPPERCASE in dictionary
    Values are lists of strings for all possible pronunciation of an acronym
    """
    acronyms = dict()
    filepath = "acronyms.tsv"

    # for l in "BCDFGHIJKLMPQRSTUVWXZ":
    #     acronyms[l] = [acr2f[l]]
    
    try:
        with importlib.resources.files(__name__).joinpath(filepath).open('r', encoding='utf-8') as f:
            for l in f.readlines():
                l = l.strip()
                if l.startswith('#') or not l: continue
                acr, pron = l.split(maxsplit=1)
                if acr in acronyms:
                    acronyms[acr].append(pron)
                else:
                    acronyms[acr] = [pron]
    except FileNotFoundError:
        print(f"Missing dictionary file {filepath}", file=sys.stderr)
    
    return acronyms

acronyms = load_acronyms()



# Abbreviations

def load_abbreviations():
    abbreviations = dict()
    filepath = "abbreviations.tsv"

    try:
        with importlib.resources.files(__name__).joinpath(filepath).open('r', encoding='utf-8') as f:
            for l in f.readlines():
                l = l.strip()
                if l.startswith('#') or not l: continue
                k, v = l.split('\t')
                # v = v.split()
                abbreviations[k] = v
    except FileNotFoundError:
        print(f"Missing dictionary file {filepath}", file=sys.stderr)
    
    return abbreviations

abbreviations = load_abbreviations()


# Interjections

def load_interjections():
    """
    Values are lists of strings for all possible pronunciation of an acronym
    """
    interjections = dict()
    filepath = "interjections.tsv"
    
    try:
        with importlib.resources.files(__name__).joinpath(filepath).open('r', encoding='utf-8') as f:
            for l in f.readlines():
                l = l.strip()
                if l.startswith('#') or not l: continue
                interj, *pron = l.split(maxsplit=1)
                pron = pron if pron else []

                if interj in interjections and pron:
                    interjections[interj].append(pron)
                else:
                    interjections[interj] = pron
    except FileNotFoundError:
        print(f"Missing dictionary file {filepath}", file=sys.stderr)

    return interjections

interjections = load_interjections()


# Common word mistakes

def load_corrected_tokens():
    corrected_tokens = dict()
    filepath = "corrected_tokens.tsv"

    try:
        with importlib.resources.files(__name__).joinpath(filepath).open('r', encoding='utf-8') as f:
            for l in f.readlines():
                l = l.strip()
                if l.startswith('#') or not l: continue
                k, v = l.split('\t')
                v = v.split()
                corrected_tokens[k] = v
    except FileNotFoundError:
        print(f"Missing dictionary file {filepath}", file=sys.stderr)
    
    return corrected_tokens

corrected_tokens = load_corrected_tokens()


# Standardization tokens

def load_standard_tokens():
    standard_tokens = dict()
    filepath = "standard_tokens.tsv"

    try:
        with importlib.resources.files(__name__).joinpath(filepath).open('r', encoding='utf-8') as f:
            for l in f.readlines():
                l = l.strip()
                if l.startswith('#') or not l: continue
                k, v = l.split('\t')
                v = v.split()
                standard_tokens[k] = v
    except FileNotFoundError:
        print(f"Missing dictionary file {filepath}", file=sys.stderr)
    
    return standard_tokens

standard_tokens = load_standard_tokens()


# Stopwords

def load_stopwords():
    stopwords = set()
    filepath = "stopwords.tsv"

    try:
        with importlib.resources.files(__name__).joinpath(filepath).open('r', encoding='utf-8') as f:
            for l in f.readlines():
                l = l.strip()
                if l.startswith('#') or not l: continue
                stopwords.add(l)
    except FileNotFoundError:
        print(f"Missing dictionary file {filepath}", file=sys.stderr)
    
    return stopwords

stopwords = load_stopwords()
