import subprocess
import random

from ..asr import phonetize_word
from ..text import filter_out_chars, PUNCTUATION


_phon_coalesce = {
    ('t', 'd'): 'd',
}


_mbrola_phon_dict_loaded = False
_mbrola_phon_dict = dict()
_mbrola_phon_dur_dict = dict()


def _load_mbrola_phon_dict():
    if _mbrola_phon_dict_loaded:
        return
    
    path = __file__.replace("__init__.py", "mbrola_phon.tsv")
    with open(path, 'r', encoding='utf-8') as f_in:
        for line in f_in.readlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            key, val = line.split('\t')
            _mbrola_phon_dict[key] = val
    
    path = __file__.replace("__init__.py", "mbrola_phon_dur.tsv")
    with open(path, 'r', encoding='utf-8') as f_in:
        for line in f_in.readlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            key, val = line.split('\t')
            _mbrola_phon_dur_dict[key] = int(val)




def to_mbrola_phon(sentence: str) -> str:
    """ Convert a Breton sentence to a Mbrola phon file """

    _load_mbrola_phon_dict()
    sentence = filter_out_chars(sentence, PUNCTUATION)
    words = sentence.split()
    words_phon = [ phonetize_word(w)[0] for w in words ]
    print(words_phon)

    mbrola_phon_list = []
    for word_phon in words_phon:
        for phon in word_phon.split():
            mbrola_phon = _mbrola_phon_dict[phon]
            dur = _mbrola_phon_dur_dict.get(mbrola_phon, 100) + random.randint(-20, 20)
            mbrola_phon_list.append((mbrola_phon, dur))

    # Remove excess phones
    mbrola_phon_list_coalesced = []
    i = 0
    while i < len(mbrola_phon_list)-1:
        diphone = (mbrola_phon_list[i][0], mbrola_phon_list[i+1][0])
        if diphone in _phon_coalesce:
            new_phon = _phon_coalesce[diphone]
            duration = mbrola_phon_list[i][1] + mbrola_phon_list[i+1][1]
            mbrola_phon_list_coalesced.append((new_phon, duration))
            i += 1
        else:
            mbrola_phon_list_coalesced.append(mbrola_phon_list[i])
        i += 1
    mbrola_phon_list_coalesced.append(mbrola_phon_list[-1])
    mbrola_phon_list = mbrola_phon_list_coalesced

    data = ["_   100"]  # Pause
    for phon, dur in mbrola_phon_list:
        data.append(f"{phon:4}{dur}")
    data.append("_   100")

    return '\n'.join(data)


def to_wavefile(sentence: str, filename: str) -> None:
    data = to_mbrola_phon(sentence)
    print(data)
    with open(filename, 'w') as f_out:
        f_out.write(data)


def speak(sentence: str) -> None:
    data = to_mbrola_phon(sentence)
    proc = subprocess.Popen(["mbrola", "/usr/share/mbrola/bz1/bz1", '-', '-.au'],
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    proc.stdin.write(data.encode())
    proc.stdin.flush()
    print(data)

    output, error = proc.communicate()
    proc.stdin.close()
    subprocess.run(['aplay', '-'], input=output)