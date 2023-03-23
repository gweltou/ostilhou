from typing import Tuple, List
from .metadata import extract_metadata


# Graphemes to phonemes

w2f = {
    'a'     :   'A',
    'â'     :   'A',        # lÂret
    'añ'    :   'AN',
    'an'    :   'AN N',
    'amm'   :   'AN M',     # liAMM
    'añv.'  :   'AN',       # klAÑV {gouzañv ?}
    'b'     :   'B',
    'd'     :   'D',
    'ch'    :   'CH',       # CHomm
    "c'h"   :   'X',        # 
    'c'     :   'K',        # xxx GALLEG XXX
    'e'     :   'E',        # spEred
    'ê'     :   'E',        # gÊr
    'é'     :   'E',        # xxx GALLEG XXX
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
    'iñ'    :   'I N',      # bIÑs
    'iñv'   :   'I V',      # fIÑV {gwiñver ?}
    'iñ.'   :   'I',        # debrIÑ
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
    'on'    :   'ON N',     # dON
    'ont.'  :   'ON N',     # mONt
    'oñ'    :   'ON',       # sOÑjal
    'ou'    :   'OU',       # dOUr
    'oû'    :   'OU',       # gOÛt (kerneveg)
    'où'    :   'OU',       # goulOÙ
    'or'    :   'OH R',     # dORn      ! dor, goudoriñ
    'orr'   :   'O R',      # gORRe
    'p'     :   'P',
    ".p'h"  :   'P',        # P'He
    'qu'    :   'K',        # xxx GALLEG XXX
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
    'A' :   'A',
    'B' :   'B E',
    'C' :   'S E',
    'D' :   'D E',
    'E' :   'EU',
    'F' :   'EH F',
    'G' :   'J E',
    'H' :   'A CH',
    'I' :   'I',
    'J' :   'J I',
    'K' :   'K A',
    'L' :   'EH L',
    'M' :   'EH M',
    'N' :   'EH N',
    'O' :   'O',
    'P' :   'P E',
    'Q' :   'K U',
    'R' :   'EH R',
    'S' :   'EH S',
    'T' :   'T E',
    'U' :   'U',
    'V' :   'V E',
    'W' :   'OU E',
    'X' :   'I K S',
    
    'Z' :   'Z EH D',
}


# Verbal fillers with phonetization

verbal_fillers = {
    'euh'   :   'OE',
    'euhm'  :   'OE M',
    'beñ'   :   'B EN',
    'eba'   :   'E B A',
    'ebeñ'  :   'E B EN',
    'kwa'   :   'K W A',
    'hañ'   :   'H AN',
    'heñ'   :   'EN',
    'boñ'   :   'B ON',
    'bah'   :   'B A',
    'feñ'   :   'F EN',
    'enfin' :   'AN F EN',
    'tiens' :   'T I EN',
    'alors' :   'A L OH R',
    'allez' :   'A L E',
    'voilà' :   'V O A L A',
    'pff'   :   'P F',
    #'oh'    :   'O',
    #'ah'    :   'A',
}


phonemes = set()
for val in list(w2f.values()) + list(acr2f.values()) + list(verbal_fillers.values()):
    for tok in val.split():
        phonemes.add(tok)


lexicon_sub = dict()
_lexicon_sub_path = __file__.replace("__init__.py", "lexicon_sub.dic")
with open(_lexicon_sub_path, 'r') as f:
    for l in f.readlines():
        w, *phon = l.split()
        lexicon_sub[w] = phon


lexicon_add = dict()
_lexicon_add_path = __file__.replace("__init__.py", "lexicon_add.dic")
with open(_lexicon_add_path, 'r') as f:
    for l in f.readlines():
        w, *phon = l.split()
        lexicon_add[w] = phon



def phonetize(word: str) -> str:
    if word in lexicon_sub:
        return lexicon_sub[word]
    
    head = 0
    phonemes = []
    word = '.' + word.strip().lower().replace('-', '.') + '.'
    error = False
    while head < len(word):
        parsed = False
        for i in (4, 3, 2, 1):
            token = word[head:head+i].lower()
            if token in w2f:
                phonemes.append(w2f[token])
                head += i-1
                parsed = True
                break
        head += 1
        if not parsed and token not in ('.', "'"):
            error = True
    
    if error:
        print("ERROR [phonetizer]", word, ' '.join(phonemes))
    
    return phonemes



Segment = Tuple[int, int]

def load_segments_data(split_filename: str) -> Tuple[List[Segment], str]:
    """ Load audio segments delimiters from a `.split` file
        Return a list of segments and a header string
    """

    segments = []
    header = ""
    first = True
    with open(split_filename, 'r') as f:
        for l in f.readlines():
            l = l.strip()
            if l:
                if first and l.startswith('#'):
                    header = l
                else:
                    t = l.split()
                    start = int(t[0])
                    stop = int(t[1])
                    segments.append((start, stop))
                first = False
    
    return segments, header



def load_text_data(filename):
    """ return list of sentences with metadata

        Return
        ------
            list of tuple (text sentences, metadata)
    """
    utterances = []
    with open(filename, 'r') as f:
        current_speaker = 'unknown'
        current_gender = 'unknown'
        no_lm = False
        for l in f.readlines():
            l = l.strip()
            if l and not l.startswith('#'):
                # Extract speaker id and other metadata
                l, metadata = extract_metadata(l)
                if "speaker" in metadata:
                    current_speaker = metadata["speaker"]
                else:
                    metadata["speaker"] = current_speaker
                
                if "gender" in metadata:
                    current_gender = metadata["gender"]
                else:
                    metadata["gender"] = current_gender
                
                if "parser" in metadata:
                    if "no-lm" in metadata["parser"]: no_lm = True
                    elif "add-lm" in metadata["parser"]: no_lm = False
                else:
                    if no_lm:
                        metadata["parser"] = ["no-lm"]
                if l:
                    utterances.append((l, metadata))
    return utterances




_postproc_sub = dict()
_postproc_sub_path = __file__.replace("__init__.py", "postproc_sub.tsv")

with open(_postproc_sub_path, 'r') as f:
    for l in f.readlines():
        l = l.strip()
        if l and not l.startswith('#'):
            print(f"{l=}")
            k, v = l.split('\t')
            _postproc_sub[k] = v


def sentence_post_process(text: str) -> str:
    if not text:
        return ''
    
    # web adresses
    if "HTTP" in text or "WWW" in text:
        text = text.replace("pik", '.')
        text = text.replace(' ', '')
        return text.lower()
    
    for sub in _postproc_sub:
        text = text.replace(sub, _postproc_sub[sub])
    
    splitted = text.split(maxsplit=1)
    splitted[0] = splitted[0].capitalize()
    return ' '.join(splitted)