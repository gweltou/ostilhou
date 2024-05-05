import os
from typing import Tuple
import hunspell
from colorama import Fore

from ..text.tokenizer import Token, Flag, tokenize, detokenize
from ..asr import lexicon_sub, verbal_fillers
from ..dicts import interjections



ROOT = os.path.dirname(os.path.abspath(__file__))
HS_DIC_PATH = os.path.join(ROOT, "hunspell-dictionary", "br_FR")
HS_AFF_PATH = os.path.join(ROOT, "hunspell-dictionary", "br_FR.aff")

additional_words = ["add.txt", "add_gwe.txt"]



def get_hunspell_dict():
    hs = hunspell.HunSpell(HS_DIC_PATH+".dic", HS_AFF_PATH)
    #hs = hunspell.Hunspell(HS_DIC_PATH) # for cyhunspell
    for path in additional_words:
        HS_ADD_PATH= os.path.join(ROOT, path)
        with open(HS_ADD_PATH, 'r') as f:
            for w in f.readlines():
                if not w.startswith('#'):
                    hs.add(w.strip())
    for w in interjections:
        hs.add(w)
    return hs

hs_dict = get_hunspell_dict()



def get_hspell_mistakes(sentence: str, autocorrected=True) -> Tuple[str, int]:
    """ Return a string which is a colored correction of the sentence
        and the number of spelling mistakes in sentence.

        Parameters
        ----------
            autocorrect: bool
                Apply autocorrection before countint errors
    """

    n_mistakes = 0
    colored_tokens = []
    # colored = ""

    for tok in tokenize(sentence, autocorrect=True):
        if tok.kind == Token.WORD:
            if tok.data.lower() in lexicon_sub:
                tok.data = Fore.YELLOW + tok.data + Fore.RESET
            elif tok.data.lower() in verbal_fillers:
                tok.data = Fore.YELLOW + tok.data + Fore.RESET
            elif Flag.INCLUSIVE in tok.flags:
                head, *_ = tok.data.split('·')
                if not hs_dict.spell(head):
                    n_mistakes += 1
                    tok.data = Fore.RED + tok.data + Fore.RESET
            elif Flag.CORRECTED in tok.flags:
                tok.data = Fore.YELLOW + tok.data + Fore.RESET
            elif not hs_dict.spell(tok.data):
                n_mistakes += 1
                tok.data = Fore.RED + tok.data + Fore.RESET
        elif tok.kind == Token.PROPER_NOUN:
            tok.data = Fore.GREEN + tok.data + Fore.RESET
        elif tok.kind == Token.ACRONYM:
            tok.data = Fore.BLUE + tok.data + Fore.RESET
        elif tok.kind in (tok.ROMAN_NUMBER, tok.ROMAN_ORDINAL, tok.TIME, tok.UNIT, tok.QUANTITY):
            tok.data = Fore.YELLOW + tok.data + Fore.RESET
        elif tok.kind == Token.RAW:
            tok.data = Fore.BLACK + tok.data + Fore.RESET
            n_mistakes += 1
        colored_tokens.append(tok)
    
    return detokenize(colored_tokens), n_mistakes
    
