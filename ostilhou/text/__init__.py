from typing import Iterator, Any

from .tokenizer import (
    Token, TokenType,
    tokenize, detokenize,
    split_sentences, split_sentences_old
)
from .normalizer import normalize, normalize_sentence
from .inverse_normalizer import inverse_normalize_sentence, inverse_normalize_timecoded
from .utils import (
    strip_punct, filter_out_chars, filter_in_chars, capitalize, pre_process,
    extract_parenthesis_content, sentence_stats,
)
from .definitions import PUNCTUATION, LETTERS, PUNCT_PAIRS, VALID_CHARS
from ..utils import read_file_drop_comments
from ..hspell import get_hspell_mistakes



def load_translation_dict(path: str) -> dict:
    translation_dict = dict()
    with open(path, 'r', encoding='utf-8') as f:
        for line in f.readlines():
            line = line.strip()
            if '\t' in line:
                key, val = line.split('\t')
                translation_dict[key] = val
            else:
                translation_dict[line] = ""
    return translation_dict



def reverse_translation_dict(path: str, newpath: str) -> None:
    """
    Build a translation dictionary (tsv file) by reversing another translation dictionary
    """
    reversed = dict()
    for line in read_file_drop_comments(path):
        line = pre_process(line)
        if '\t' in line:
            key, val = line.split('\t')
            if ' ' in key or ' ' in val:
                print("no spaces allowed in translation dictionaries")
                continue
            if val in reversed:
                reversed[val] += ", {}".format(key)
            else:
                reversed[val] = key
    with open(newpath, 'w', encoding='utf-8') as f:
        for k in sorted(reversed):
            f.write(f"{k}\t{reversed[k]}\n")



def correct_sentence(sentence: str) -> str:
    return detokenize(tokenize(sentence, autocorrect=True))



def translate_tokens(token_stream: Iterator[Token], tra_dict: dict, **options: Any) -> Iterator[Token]:
    """
    Substitute tokens according to a given dictionary
        
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


def count_words(sentence: str) -> int:
    """Return number of regular words in sentence"""
    n = 0
    for t in tokenize(sentence, norm_punct=True, autocorrect=True):
        if t.type == Token.WORD:
            n += 1
    return n


def is_full_sentence(sentence: str) -> bool:
    """Check if sentence is a complete sentence, punctuation-wise"""
    simplified = filter_out_chars(sentence, "\"«»'’()").strip()
    return simplified[0].isupper() and simplified[-1] in ".!?…;:"


def is_sentence_start_open(sentence: str) -> bool:
    """Returns True if the sentence starts irregularly"""
    simplified = filter_out_chars(sentence, "\"«»'’()").strip()
    return (
        simplified[0].islower()
        or (simplified[0].isupper() and (simplified[1].isupper() or simplified[1].isdigit()))  # Acronym
        or simplified[0].isdigit()
    )
	

def is_sentence_end_open(sentence: str) -> bool:
    """Returns True if the sentence ends abruptly"""
    simplified = filter_out_chars(sentence, "\"«»'’()").strip()
    return (
        simplified[-1].islower()
        #or sentence[-1] in "…'’,»\":"
        or simplified[-1] in "…,"
        or simplified[-1].isdigit()
    )


def is_sentence_punct_paired(sentence: str) -> bool:
    if sentence.count('"') % 2 != 0:
        return False
    for punct in PUNCT_PAIRS:
        if sentence.count(punct) != sentence.count(PUNCT_PAIRS[punct]):
            return False
    return True


def score_sentence(sentence: str):
    """
    NOT USED
    TODO
    """
    n_word = count_words(sentence)
    highlighted_str, n_hspell_mistakes = get_hspell_mistakes(sentence, autocorrected=False)
    print(highlighted_str)

    n_mistakes = 0

    for tok in tokenize(sentence, autocorrect=True):
        if tok.type == Token.WORD:
            if tok.data.lower() in lexicon_sub:
                n_mistakes -= 1
            elif tok.data.lower() in verbal_fillers:
                n_mistakes -= 1
            elif Flag.INCLUSIVE in tok.flags:
                head, *_ = tok.data.split('·')
                if not hs_dict.spell(head):
                    n_mistakes -= 1
            elif Flag.CORRECTED in tok.flags:
                n_mistakes -= 1
            elif not hs_dict.spell(tok.data):
                n_mistakes += 1
        elif tok.type == Token.RAW:
            n_mistakes += 1

    return 1.0