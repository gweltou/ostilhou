import sys
import os
import platform


dict_root = os.path.dirname(os.path.abspath(__file__))

# Check if there is any tsv file in folder
if dict_root and os.path.exists(dict_root):
    for filename in os.listdir(dict_root):
        if filename.endswith(".tsv"):
            break
    else:
        dict_root = None
else:
    dict_root = None

if dict_root is None:
    if platform.system() in ("Linux", "Darwin"):
        default = os.path.join(os.path.expanduser("~"), ".local", "share")
    elif platform.system() == "Windows":
        default = os.getenv("LOCALAPPDATA")
    else:
        raise OSError("Unsupported operating system")
    dict_root = os.path.join(os.getenv("XDG_DATA_HOME ", default), "anaouder", "dicts")
    
    if not os.path.exists(dict_root):
        os.makedirs(dict_root)

print(f"loading dicts in {dict_root}", file=sys.stderr)


# Proper nouns dictionary
# with phonemes when name has a foreign or particular pronunciations

def load_proper_nouns():
    proper_nouns = dict()
    proper_nouns_files = [
        "proper_nouns_phon.tsv",
        "places.tsv",
        # "countries.tsv",
        "last_names.tsv",
        "first_names.tsv",
    ]

    for file in proper_nouns_files:
        path = os.path.join(dict_root, file)
        if not os.path.exists(path):
            print(f"Missing dictionary file {file}")
            continue
        with open(path, 'r', encoding='utf-8') as f:
            for l in f.readlines():
                l = l.strip()
                if l.startswith('#') or not l: continue
                w, *pron = l.split(maxsplit=1)
                pron = pron or []
                
                if w in proper_nouns and pron:
                    if pron[0] not in proper_nouns[w]: # Avoid duplicate entries, which Kaldi hates
                        proper_nouns[w].append(pron[0])
                else:
                    proper_nouns[w] = pron
    
    return proper_nouns

proper_nouns = load_proper_nouns()


# Noun dictionary
# Things that you can count

def load_nouns_f():
    nouns_f = set()
    _nouns_f_path = os.path.join(dict_root, "noun_f.tsv")

    if not os.path.exists(_nouns_f_path):
        print(f"Missing dictionary file noun_f.tsv")
        return nouns_f

    with open(_nouns_f_path, 'r', encoding='utf-8') as f:
        for l in f.readlines():
            l = l.strip()
            if l.startswith('#') or not l: continue
            nouns_f.add(l)
    
    return nouns_f

nouns_f = load_nouns_f()


def load_nouns_m():
    nouns_m = set()
    _nouns_m_path = os.path.join(dict_root, "noun_m.tsv")

    if not os.path.exists(_nouns_m_path):
        print(f"Missing dictionary file noun_m.tsv")
        return nouns_m

    with open(_nouns_m_path, 'r', encoding='utf-8') as f:
        for l in f.readlines():
            l = l.strip()
            if l.startswith('#') or not l: continue
            nouns_m.add(l)
    
    return nouns_m

nouns_m = load_nouns_m()


# Acronyms dictionary

def load_acronyms():
    """
        Acronyms are stored in UPPERCASE in dictionary
        Values are lists of strings for all possible pronunciation of an acronym
    """
    acronyms = dict()
    _acronyms_path = os.path.join(dict_root, "acronyms.tsv")

    # for l in "BCDFGHIJKLMPQRSTUVWXZ":
    #     acronyms[l] = [acr2f[l]]
    
    if os.path.exists(_acronyms_path):
        with open(_acronyms_path, 'r', encoding='utf-8') as f:
            for l in f.readlines():
                l = l.strip()
                if l.startswith('#') or not l: continue
                acr, pron = l.split(maxsplit=1)
                if acr in acronyms:
                    acronyms[acr].append(pron)
                else:
                    acronyms[acr] = [pron]
    else:
        print("Acronym dictionary not found... creating file")
        open(_acronyms_path, 'a', encoding='utf-8').close()
    return acronyms

acronyms = load_acronyms()


# Abbreviations

def load_abbreviations():
    abbreviations = dict()
    _abbreviations_path = os.path.join(dict_root, "abbreviations.tsv")

    if not os.path.exists(_abbreviations_path):
        print(f"Missing dictionary file abbreviations.tsv")
        return abbreviations
    
    with open(_abbreviations_path, 'r', encoding='utf-8') as f:
        for l in f.readlines():
            l = l.strip()
            if l.startswith('#') or not l: continue
            k, v = l.split('\t')
            # v = v.split()
            abbreviations[k] = v
    
    return abbreviations

abbreviations = load_abbreviations()


# Interjections


def load_interjections():
    """
        Acronyms are stored in UPPERCASE in dictionary
        Values are lists of strings for all possible pronunciation of an acronym
    """
    interjections = dict()
    _interjections_path = os.path.join(dict_root, "interjections.tsv")

    # for l in "BCDFGHIJKLMPQRSTUVWXZ":
    #     acronyms[l] = [acr2f[l]]
    
    if os.path.exists(_interjections_path):
        with open(_interjections_path, 'r', encoding='utf-8') as f:
            for l in f.readlines():
                l = l.strip()
                if l.startswith('#') or not l: continue
                interj, *pron = l.split(maxsplit=1)
                pron = pron if pron else []

                if interj in interjections and pron:
                    interjections[interj].append(pron)
                else:
                    interjections[interj] = pron
    else:
        print("Interjections dictionary not found... creating file")
        open(_interjections_path, 'a', encoding='utf-8').close()
    return interjections

interjections = load_interjections()


# Common word mistakes

def load_corrected_tokens():
    corrected_tokens = dict()
    _corrected_tokens_path = os.path.join(dict_root, "corrected_tokens.tsv")

    if not os.path.exists(_corrected_tokens_path):
        print(f"Missing dictionary file corrected_tokens.tsv")
        return corrected_tokens
    
    with open(_corrected_tokens_path, 'r', encoding='utf-8') as f:
        for l in f.readlines():
            l = l.strip()
            if l.startswith('#') or not l: continue
            k, v = l.split('\t')
            v = v.split()
            corrected_tokens[k] = v
    
    return corrected_tokens

corrected_tokens = load_corrected_tokens()


# Standardization tokens

def load_standard_tokens():
    standard_tokens = dict()
    _standard_tokens_path = os.path.join(dict_root, "standard_tokens.tsv")

    if not os.path.exists(_standard_tokens_path):
        print(f"Missing dictionary file standard_tokens.tsv")
        return standard_tokens

    with open(_standard_tokens_path, 'r', encoding='utf-8') as f:
        for l in f.readlines():
            l = l.strip()
            if l.startswith('#') or not l: continue
            k, v = l.split('\t')
            v = v.split()
            standard_tokens[k] = v
    
    return standard_tokens

standard_tokens = load_standard_tokens()