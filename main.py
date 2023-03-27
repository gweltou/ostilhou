from ostilhou import tokenize, detokenize
from ostilhou.text import (
    strip_punct,
    split_sentence,
    load_translation_dict, translate,
    normalize, normalize_sentence,
    pre_process
    )
from ostilhou.corpora import load_wikipedia_150k, load_sarmoniou
from ostilhou.asr import phonetize

from libMySTT import get_cleaned_sentence, corrected, corrected_sentences, get_correction


def read_file(filename):
    with open(filename, 'r') as f:
        return f.read()


def test_tokenize(sentence):
    for t in tokenize(sentence, norm_punct=True):
        print(t, t.norm)


def test_detokenize(sentence):
    print(detokenize(tokenize(sentence, norm_punct=True), end_sentence='\n'))


def test_normalize(sentence):
    for token in tokenize(sentence):
        print(token, token.norm)
    print(detokenize(normalize(tokenize(sentence))))


def test_wiki150():
    # Find male and female nouns by looking at the words following
    # the cardinals 'daou', 'tri', 'pevar' (for male nouns) and
    # 'div', 'teir', 'peder' (for female nouns)
    # Write them to separate files

    sentences = load_wikipedia_150k()
    print(len(sentences))
    m_card = ['daou', 'tri', 'pevar']
    f_card = ['div', 'teir', 'peder']
    m_noun = {}
    f_noun = {}
    for sentence in sentences:
        words = sentence.split()
        for card in m_card + f_card:
            try:
                i = words.index(card)
                if i+1 < len(words):
                    word = strip_punct(words[i+1]).lower()
                    if word.endswith("-se"):
                        word = word[:-3]
                    elif word.endswith("-mañ"):
                        word = word[:-4]
                    if card in m_card:
                        m_noun[word] = m_noun.get(word, 0) + 1
                    elif card in f_card:
                        f_noun[word] = f_noun.get(word, 0) + 1
            except ValueError:
                continue
    
    with open("noun_f.txt", 'w') as f:
        for noun, _ in sorted(f_noun.items(), key=lambda x: x[1], reverse=True):
            f.write(f"{noun}\n")
    with open("noun_m.txt", 'w') as f:
        for noun, _ in sorted(m_noun.items(), key=lambda x: x[1], reverse=True):
            f.write(f"{noun}\n")


def test_sarmoniou():
    sarmoniou = load_sarmoniou()

    # Using a translation dictionary to replace words with their modern form
    td = load_translation_dict("talbr/dicts/sarmonioù_peurunvan.tsv")

    # with open("sarmonioù.txt", 'w') as f:
    #     for line in sarmoniou:
    #         f.write(detokenize( translate(tokenize(line), td) ) + '\n')
    for line in sarmoniou:
        print(detokenize( translate(tokenize(line), td) ))


def test_clean_ya():
    # Parse a ya.bzh dump file
    rejected = 0
    sentences = set()
    sentences_norm = set()
    n_parsed = 0
    with open("ya_dump.txt", 'r') as fin:
        for line in fin.readlines():
            if line:
                line = pre_process(line).replace('*', '').replace('OOO', '000')
                for sentence in split_sentence(line, end='\n'):
                    n_parsed += 1
                    ntok = len(sentence.split())
                    if ntok < 3:
                        continue
                    if len(sentence) / ntok < 3.2:
                        continue

                    corr, n_mistakes = get_correction(sentence)
                    if n_mistakes >= 1:
                        print(corr)
                        rejected += 1
                    elif n_mistakes == 0:
                        sentences.add(sentence)
                    # normalized = normalize_sentence(sentence)
                    # if normalized[1:].split() != sentence[1:].split():
                    #     print(sentence[:-1])
                    #     print(normalized)
                    #     print()
                    # corr, n_mistakes = get_correction(sentence)
                    # if n_mistakes == 0:
                    #     sentences_norm.add(normalized)
                    
    with open("ya_propr.txt", 'w') as fout:
        for sentence in sentences:
            fout.write(sentence)
    print(f"Total sentences: {n_parsed}")
    print(f"Kept: {len(sentences)}")
    print(f"{rejected=} ({rejected/n_parsed:.2%})")


if __name__ == "__main__":
    sentence = "klask ar 500 000€ a vo ezhomm"
    # test_tokenize(sentence)
    # test_detokenize(sentence)
    # test_normalize(sentence)
    # test_wiki150()
    # test_sarmoniou()
    
    test_clean_ya()