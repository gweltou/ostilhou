from typing import List, Iterator, Any
from .tokenizer import Token, tokenize, detokenize, split_sentence, PUNCTUATION
from .normalizer import normalize, normalize_sentence
from .inverse_normalizer import inverse_normalize_sentence



def strip_punct(word: str) -> str:
    """ strip punctuation left and right of a word """

    while word and word[0] in PUNCTUATION:
        word = word[1:]
    while word and word[-1] in PUNCTUATION:
        word = word[:-1]
    return word


def filter_out(text: str, chars: str) -> str:
    """ Remove characters from a string """

    filtered_text = ""
    for l in text:
        if not l in chars: filtered_text += l
    return filtered_text


def pre_process(text: str) -> str:
    text = text.replace('‘', "'")
    text = text.replace('’', "'")
    text = text.replace('ʼ', "'")
    text = text.replace(',', ',')
    text = text.replace('˜', '') # Found instead of non-breakable spaces when parsing Ya! pdfs
    text = text.replace('Š', '') # Found instead of long dashes when parsing Ya! pdfs
    text = text.replace('ñ', 'ñ') # A sneaky n-tilde (found in Ya! webpages)
    text = text.replace('ň', 'ñ')
    text = text.replace('ù', 'ù') # Another sneaky one (found in Ya! webpages)
    return text


def load_translation_dict(path: str) -> dict:
    translation_dict = dict()
    with open(path, 'r') as f:
        for line in f.readlines():
            line = line.strip()
            if '\t' in line:
                key, val = line.split('\t')
                translation_dict[key] = val
            else:
                translation_dict[line] = ""
    return translation_dict


def translate(token_stream: Iterator[Token], tra_dict: dict, **options: Any) -> Iterator[Token]:
    """ Substitute tokens according to a given dictionary
        
        Keys with uppercase letters will be case-sentitive
        Keys with lowercase letters only will be case-insensitive
        Translate will operate according to the first match in the dictionary

        Key/value pairs of the translation dictionary can contain
        the '*' character to match any character
        Ex: "*a" : "*añ"    -> will change suffixes of words ending with 'a'


    """

    for tok in token_stream:
        for key, val in tra_dict.items():
            if key.startswith('*'):
                if key.endswith('*'):
                    # Match chars in the middle of words
                    expr = key.strip('*')
                    if expr in tok.data:
                        tok.data.replace(expr, val.strip('*'))
                else:
                    # Match at the end
                    expr = key.lstrip('*')
                    if tok.data.endswith(expr):
                        tok.data = tok.data[:-len(expr)] + val.lstrip('*')
            elif key.endswith('*'):
                # Match at the beginning
                expr = key.rstrip('*')
                if tok.data.startswith(expr):
                    tok.data = val.rstrip('*') + tok.data[len(expr):]
            elif key.islower():
                if key == tok.data.lower():
                    if tok.data.istitle():
                        tok.data = val.capitalize()
                    elif tok.data.isupper():
                        tok.data = val.upper()
                    else:
                        tok.data = val
                    break
            else:
                if key == tok.data:
                    tok.data = tra_dict[tok.data]
                    break
        
        yield tok