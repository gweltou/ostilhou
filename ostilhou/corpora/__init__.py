from typing import List


def load_corpus(path: str) -> List[str]:
    corpus = []
    with open(path, 'r') as f:
        for line in f.readlines():
            corpus.append(line.strip())
    return corpus


def load_mcv_oplb():
    corpus_path = __file__.replace("__init__.py", "mcv-oplb.txt")
    return load_corpus(corpus_path)


def load_wikipedia_150k():
    corpus_path = __file__.replace("__init__.py", "wikipedia-br-150k.txt")
    return load_corpus(corpus_path)


def load_sarmoniou():
    corpus_path = __file__.replace("__init__.py", "sarmonioù_an_aotroù_quere.txt")
    corpus = load_corpus(corpus_path)
    corpus = corpus[31:-365] # Strip header and footnotes
    # Mapping to correct encoding errors
    mapping = {146: 8217, 151: 8212, 156: 230, 148: 8221}
    return [line.translate(mapping) for line in corpus if line not in (".NFO", ".NTO", ".NHO", ".NPO")]