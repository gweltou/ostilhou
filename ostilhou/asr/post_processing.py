import os
from typing import List, Optional
from ..text.inverse_normalizer import inverse_normalize_sentence, inverse_normalize_vosk
from ..text.definitions import is_noun
from ..utils import read_file_drop_comments



# Verbal fillers with phonetization

verbal_fillers = {
    'euh'   :   'OE',
    'euhm'  :   'OE M',
    'beñ'   :   'B EN',
    'beh'   :   'B E',
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
    'pff'   :   'P F F',
    'mais'  :   'M EH'
    #'oh'    :   'O',
    #'ah'    :   'A',
}



def load_postproc_dict(filepath: str) -> List[dict]:
    """ Load the post processing dictionary from a tsv file
        Keys are treated uncased
    """

    trigrams = dict()
    bigrams = dict()
    monograms = dict()
    for l in read_file_drop_comments(filepath):
        k, v = l.split('\t')
        k = tuple([t.lower() for t in k.split()])
        v = tuple(v.split())
        if len(k) == 1:
            monograms[k] = v
        elif len(k) == 2:
            bigrams[k] = v
        elif len(k) == 3:
            trigrams[k] = v
        else:
            print("ERROR (postproc_dict): number of tokens should be between 1 and 3")
            print(k)
    
    return [monograms, bigrams, trigrams]


_postproc_dict_path = os.path.join(os.path.split(__file__)[0], "postproc_sub.tsv")
_postproc_dict = load_postproc_dict(_postproc_dict_path)

_inorm_units_dict_path = os.path.join(os.path.split(__file__)[0], "inorm_units.tsv")
_inorm_units_dict = load_postproc_dict(_inorm_units_dict_path)



def post_process_text(sentence: str, normalize=False, keep_fillers=False) -> str:
    sentence = apply_post_process_dict_text(sentence, _postproc_dict)
    
    # Add hyphens for "-se" and "-mañ"
    sentence = sentence.split()
    parsed = []
    prev_word = ''
    for word in sentence:
        if not keep_fillers and word.lower() in verbal_fillers:
            continue
        if word in ("se", "mañ") and is_noun(prev_word):
            parsed.append('-'.join([parsed.pop(), word]))
            prev_word = parsed[-1]
        else:
            parsed.append(word)
            prev_word = word
    sentence = ' '.join(parsed)

    if normalize:
        sentence = apply_post_process_dict_text(sentence, _inorm_units_dict)
        sentence = inverse_normalize_sentence(sentence)
    return sentence



def post_process_vosk(
        tokens: List[dict],
        normalize=False,
        keep_fillers=True) -> List[dict]:
    
    tokens = apply_post_process_dict_vosk(tokens, _postproc_dict)

    # Add hyphens for "-se" and "-mañ"
    parsed = []
    prev_word = ''
    for idx, tok in enumerate(tokens):
        if not keep_fillers and tok["word"].lower() in verbal_fillers:
            continue
        if tok["word"] in ("se", "mañ") and is_noun(prev_word):
            word = prev_word + '-' + tok["word"]
            new_token = {
                        "word": word,
                        "start": tokens[idx-1]["start"],
                        "end": tok["end"],
                        "conf": tok["conf"]
                        }
            parsed.append(new_token)
            prev_word = word
        else:
            parsed.append(tok)
    tokens = parsed

    if normalize:
        tokens = apply_post_process_dict_vosk(tokens, _inorm_units_dict)
        tokens = inverse_normalize_vosk(tokens)
    return tokens



def apply_post_process_dict_text(sentence: str, ngram_dicts: List[dict]=_postproc_dict) -> str:

    def check_ngram(n: int):
        ngram_lowered = tuple( [ t.lower() for t in tokens[idx:idx+n] ] )
        sub = ngram_dicts[n-1].get(ngram_lowered, None)
        if sub:
            for t in sub:
                translated.append(t)    #XXX the translation is always lowercase
            return True
        return False
    
    tokens = sentence.split()
    translated = []
    tlen = len(tokens)
    idx = 0
    while idx < tlen:
        if idx <= tlen-3 and check_ngram(3):
            idx += 3
            continue
        if idx <= tlen-2 and check_ngram(2):
            idx += 2
            continue
        if idx <= tlen-1 and check_ngram(1):
            pass
        else:
            translated.append(tokens[idx])
        idx += 1

    return ' '.join(translated)



def apply_post_process_dict_vosk(tokens: List[dict], ngram_dicts: List[dict]=_postproc_dict) -> List[dict]:

    def check_ngram(n: int):
        ngram = tuple( [ t["word"].lower() for t in tokens[idx:idx+n] ] )
        sub = ngram_dicts[n-1].get(ngram, None)
        if sub:
            t_start = tokens[idx]["start"]
            t_dur = tokens[idx+n-1]["end"] - t_start
            t_dur = t_dur / len(sub)
            conf = tokens[idx]["conf"]
            for t in sub:
                token = {"word": t, "start": t_start, "end": t_start + t_dur, "conf": conf}
                translated.append(token)
                t_start += t_dur
            return True
        return False
    
    translated = []
    tlen = len(tokens)
    idx = 0
    while idx < tlen:
        if idx <= tlen-3 and check_ngram(3):
            idx += 3
            continue
        if idx <= tlen-2 and check_ngram(2):
            idx += 2
            continue
        if idx <= tlen-1 and check_ngram(1):
            pass
        else:
            translated.append(tokens[idx])
        idx += 1

    return translated
