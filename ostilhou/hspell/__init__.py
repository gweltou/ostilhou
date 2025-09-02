import os
import sys
from typing import Tuple
from colorama import Fore

from ..text.tokenizer import (
    Token, TokenType, Flag,
    tokenize, detokenize
)
from ..asr import lexicon_sub, verbal_fillers
from ..dicts import interjections



hspell_root = os.path.dirname(os.path.abspath(__file__))

hs_dic_path = os.path.join(hspell_root, "hunspell-dictionary", "br_FR")
hs_aff_path = os.path.join(hspell_root, "hunspell-dictionary", "br_FR.aff")

additional_words = ["add.txt", "add_gwe.txt"]

_hs = None


def get_hunspell_dict():    
    global _hs
    if _hs != None:
        return _hs
    
    print("Loading Hunspell dictionary...", file=sys.stderr)
    import hunspell

    _hs = hunspell.HunSpell(hs_dic_path+".dic", hs_aff_path)
    #hs = hunspell.Hunspell(HS_DIC_PATH) # for cyhunspell
    for path in additional_words:
        HS_ADD_PATH= os.path.join(hspell_root, path)
        with open(HS_ADD_PATH, 'r', encoding='utf-8') as f:
            for w in f.readlines():
                if not w.startswith('#'):
                    w = w.split()[0]
                    _hs.add(w.strip())
    for w in interjections:
        _hs.add(w)
    return _hs


def get_hunspell_spylls():    
    global _hs
    if _hs != None:
        return _hs
    
    print("Loading Hunspell dictionary...", file=sys.stderr)
    from spylls.hunspell import Dictionary

    _hs = Dictionary.from_files(hs_dic_path)
    
    return _hs



def get_hspell_mistakes(sentence: str, autocorrected=True) -> Tuple[str, int]:
    """
    Return a string which is a colored correction of the sentence
    and the number of spelling mistakes in the sentence.

    Parameters
    ----------
        autocorrect: bool
            Apply autocorrection before counting errors
    """

    hs = get_hunspell_dict()

    n_mistakes = 0
    colored_tokens = []

    for tok in tokenize(sentence, autocorrect=True):
        if tok.type == TokenType.WORD:
            if Flag.INCLUSIVE in tok.flags:
                head, *_ = tok.data.split('·')
                if not hs.spell(head):
                    n_mistakes += 1
                    tok.data = Fore.RED + tok.data + Fore.RESET
            elif Flag.CORRECTED in tok.flags:
                tok.data = Fore.YELLOW + tok.data + Fore.RESET
            elif tok.data.lower() in lexicon_sub:
                tok.data = Fore.YELLOW + tok.data + Fore.RESET
            elif not hs.spell(tok.data):
                n_mistakes += 1
                tok.data = Fore.RED + tok.data + Fore.RESET
        elif tok.type in (TokenType.PROPER_NOUN, TokenType.COUNTRY, TokenType.FIRST_NAME, TokenType.LAST_NAME):
            tok.data = Fore.GREEN + tok.data + Fore.RESET
        elif tok.type == TokenType.ACRONYM:
            tok.data = Fore.BLUE + tok.data + Fore.RESET
        elif tok.type in (
                TokenType.ROMAN_NUMBER,
                TokenType.ROMAN_ORDINAL,
                TokenType.TIME,
                TokenType.UNIT,
                TokenType.QUANTITY
        ):
            tok.data = Fore.YELLOW + tok.data + Fore.RESET
        elif tok.type == TokenType.SPECIAL_TOKEN:
            tok.data = Fore.BLUE + tok.data + Fore.RESET
        elif tok.type == TokenType.RAW:
            tok.data = Fore.RED + tok.data + Fore.RESET
            n_mistakes += 1
        colored_tokens.append(tok)
    
    return detokenize(colored_tokens), n_mistakes