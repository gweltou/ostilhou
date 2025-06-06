from typing import List, Dict
import sys
import os
import platform

from .post_processing import verbal_fillers
from ..dicts import acronyms, dicts

from .dataset import *
from .recognizer import *


# Graphemes to phonemes
w2f = {
    'a'     :   'A',
    'â'     :   'A',        # lÂret
    'à'     :   'A',        # diàr (gwennedeg)
    'añ'    :   'AN',
    'an'    :   'AN N',
    'amm'   :   'AN M',     # liAMM
    'añv.'  :   'AN',       # klAÑV {gouzañv ?}
    'aux.'  :   'O',        # chevAUX (galleg)
    'b'     :   'B',
    'ch'    :   'CH',       # CHom
    "c'h"   :   'X',        # 
    'd'     :   'D',
    'dei'   :   'D EH I',   # DEIlenn
    'c'     :   'K',        # (galleg)
    'e'     :   'E',        # spEred
    'ê'     :   'E',        # gÊr
    'é'     :   'E',        # (galleg)
    'è'     :   'EH',       # (galleg/gwennedeg)
    "ec'h"  :   'EH X',     # nec'h
    'ei'    :   'EY',       # kEIn      # could replace with (EH I) maybe ?
    'eiñ'   :   'EY',       # savetEIÑ
    'el.'   :   'EH L',     # broadEL
    'ell'   :   'EH L',
    'em'    :   'EH M',     # lEMm
    'eñ'    :   'EN',       # chEÑch
    'en.'   :   'EH N',     # meriEN
    'enn.'  :   'EH N',     # lENN
    'enn'   :   'E N',      # c'helENNer
    'eñv.'  :   'EN',       # adreñv {leñv ?}
    'er.'   :   'EH R',     # hantER
    'eu'    :   'EU',       # lEUn
    'eü'    :   'E U',      # EÜrus
    'euñv'  :   'EN',       # stEUÑV
    'f'     :   'F',
    'g'     :   'G',
    'gn'    :   'GN',       # miGNon
    'h'     :   'H',
    'ha.'   :   'A',
    'hag.'  :   'A G',
    'i'     :   'I',
    'ï'     :   'I',
    'iñ'    :   'I N',      # bIÑs
    'iñv'   :   'I V',      # fIÑV {gwiñver ?}
    'iñ.'   :   'I',        # debrIÑ
    'iv.'   :   'I W',     # liv, div, riv
    'j'     :   'J',        # BeaJiñ
    'k'     :   'K',
    'l'     :   'L',
    'lh'    :   'LH',
    'll'    :   'L',
    'm'     :   'M',
    'mm'    :   'M',
    'n'     :   'N',
    'nn'    :   'N',
    'o'     :   'O',        # nOr
    'ô'     :   'O',        # kornôg
    'om'    :   'ON M',     # lakOMp
    'on'    :   'ON N',     # dON
    'ont.'  :   'ON N',     # mONt
    'oñ'    :   'ON',       # sOÑjal
    'ou'    :   'OU',       # dOUr
    'oû'    :   'OU',       # gOÛt (kerneveg)
    'où'    :   'OU',       # goulOÙ
    'or'    :   'OH R',     # dORn      ! dor, goudoriñ
    'orr'   :   'O R',      # gORRe
    "oc'h"  :   'OH X',     # pellOC'H
    'p'     :   'P',
    ".p'h"  :   'P',        # P'He
    'qu'    :   'K',        # xxx GALLEG xxx
    'q'     :   'K',        # xxx GALLEG xxx
    'r'     :   'R',
    'rr'    :   'R',
    's'     :   'S',
    't'     :   'T',
    'u'     :   'U',        # tUd
    'û'     :   'U',        # Ûioù (kerneveg)
    'ü'     :   'U',        # emrOÜs
    'uñ'    :   'UN',       # pUÑs
    '.un.'  :   'OE N',     # UN dra
    '.ul.'  :   'OE L',     # UL labous
    '.ur.'  :   'OE R',     # UR vag
    "'un."  :   'OE N',     # d'UN
    "'ur."  :   'OE R',     # d'UR
    "'ul."  :   'OE L',     # d'UL
    'v'     :   'V',
    'v.'    :   'O',        # beV
    'vr.'   :   'OH R',     # kaVR, loVR
    'w'     :   'W',
    'x'     :   'K S',      # Axel
    'y'     :   'I',        # pennsYlvania
    'ya'    :   'IA',       # YAouank
    'ye'    :   'IE',       # YEzh
    'yo'    :   'IO',       # YOd
    'you'   :   'IOU',      # YOUc'hal
    'z'     :   'Z',
    'zh'    :   'Z',
}


# Single letters phonemes (used for acronyms)
acr2f = {
    'A' : ['A'],
    'B' : ['B E'],
    'C' : ['S E'],
    'D' : ['D E'],
    'E' : ['EU', 'E'],
    'F' : ['EH F'],
    'G' : ['J E'],
    'H' : ['A CH'],
    'I' : ['I'],
    'J' : ['J I'],
    'K' : ['K A', 'K OE'],
    'L' : ['EH L'],
    'M' : ['EH M'],
    'N' : ['EH N'],
    'Ñ' : ['EH N T I L D E'],
    'O' : ['O'],
    'P' : ['P E', 'P OE'],
    'Q' : ['K U'],
    'R' : ['EH R'],
    'S' : ['EH S'],
    'T' : ['T E', 'T OE'],
    'U' : ['U'],
    'V' : ['V E'],
    'W' : ['W E', 'W OE'],
    'X' : ['I K S'],
    'Y' : ['YE'],
    'Z' : ['Z EH D', 'Z OE'],
}


phonemes = set()
for val in list(w2f.values()) + list(verbal_fillers.values()) + [t for sub in acr2f.values() for t in sub]  :
    for tok in val.split():
        phonemes.add(tok)


lexicon_root = os.path.split(os.path.abspath(__file__))[0]

# Check if there is any tsv file in folder
if lexicon_root and os.path.exists(lexicon_root):
    for filename in os.listdir(lexicon_root):
        if filename.endswith(".tsv"):
            break
    else:
        lexicon_root = None
else:
    lexicon_root = None

if lexicon_root is None:
    if platform.system() in ("Linux", "Darwin"):
        default = os.path.join(os.path.expanduser("~"), ".local", "share")
    elif platform.system() == "Windows":
        default = os.getenv("LOCALAPPDATA")
    else:
        raise OSError("Unsupported operating system")
    lexicon_root = os.path.join(os.getenv("XDG_DATA_HOME ", default), "anaouder", "asr")
    
    if not os.path.exists(lexicon_root):
        os.makedirs(lexicon_root)

print(f"loading lexicons in {lexicon_root}", file=sys.stderr)


def load_lexicon_add():
    """
        Lexicon_add contains pronunciation variants of words that can't be infered
        by the `phonetize` function from their spelling in 'peurunvan' alone.
        Those pronunciation should be added to the ones infered by `phonetize`.
    """

    lexicon_add: Dict[str, List[str]] = dict()
    _lexicon_add_path = os.path.join(lexicon_root, "lexicon_add.tsv")

    with open(_lexicon_add_path, 'r', encoding='utf-8') as f:
        for l in f.readlines():
            w, phon = l.strip().split(maxsplit=1)
            if w in lexicon_add:
                lexicon_add[w].append(phon)
            else:
                lexicon_add[w] = [phon]
    
    return lexicon_add

lexicon_add = load_lexicon_add()


def load_lexicon_sub():
    """
        Lexicon_sub contains hardcoded pronunciations for (mostly) foreign words and
        pronunciation exceptions.

        When a word is present in `lexicon_sub`, the `phonetize` function will not
        infer it's pronunciation from its spelling. Only the harcoded one(s) will
        be returned.

        When there is more than one possible particular pronunciation for a word,
        supplementary pronunciation can be put in `lexicon_sub.dic` or `lexicon_add.dic`
    """

    lexicon_sub: Dict[str, List[str]] = dict()
    _lexicon_sub_path = os.path.join(lexicon_root, "lexicon_sub.tsv")
    
    with open(_lexicon_sub_path, 'r', encoding='utf-8') as f:
        for l in f.readlines():
            w, phon = l.strip().split(maxsplit=1)
            if w in lexicon_sub:
                lexicon_sub[w].append(phon)
            else:
                lexicon_sub[w] = [phon]
    
    return lexicon_sub

lexicon_sub = load_lexicon_sub()



def phonetize_word(word: str) -> tuple[List[str], int]:
    """ Simple phonetizer
        Returns a string of phonemes representing the pronunciation
        of a single given word.
        All words must be given in lowercase, except acronyms
        Numbers can't be phonetized, so they need to be normalized first.
    """
    
    word = word.strip()
    lowered = word.lower()

    if '-' in word:
        # Composed word with hyphen, treat every subword individually
        prop = [""]
        errors = 0
        for sub in word.split('-'):
            new_prop = []
            rep, err = phonetize_word(sub)
            errors += err
            for r in rep:
                for pre in prop:
                    new_prop.append(str.strip(pre + ' ' + r))
            prop = new_prop
        return prop, errors

    if word in acronyms:
        return acronyms[word], 0
    
    if word in acr2f:
        return acr2f[word], 0
    
    for d in [
        "first_names",
        "last_names",
        "places",
        "proper_nouns"
    ]:
        if word in dicts[d]:
            if dicts[d][word]:
                return dicts[d][word], 0

    if lowered in lexicon_sub:
        alter = lexicon_add.get(lowered, [])
        return lexicon_sub[lowered] + alter, 0
    
    if lowered in verbal_fillers:
        return [ verbal_fillers[lowered] ], 0

    
    head = 0
    phon = []
    wordb = '.' + word + '.'
    errors = []
    while head < len(wordb):
        parsed = False
        for i in (4, 3, 2, 1):
            token = wordb[head:head+i].lower()
            if token in w2f:
                phon.append(w2f[token])
                head += i-1
                parsed = True
                break
        head += 1
        if not parsed and token not in ('.', "'"):
            errors.append(token)
    
    pron = ' '.join(phon)

    if errors:
        print("ERROR [phonetizer]", word, pron, errors)
    
    variants = lexicon_add.get(word, [])
    return [pron] + variants, len(errors)
