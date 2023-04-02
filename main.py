import re
from ostilhou import tokenize, detokenize
from ostilhou.text import (
    strip_punct, filter_out,
    split_sentences, extract_parenthesis_content,
    load_translation_dict, translate,
    normalize, normalize_sentence,
    pre_process, sentence_stats,
    )
from ostilhou.text.definitions import OPENING_QUOTES, CLOSING_QUOTES, PATTERN_DOTTED_ACRONYM, PUNCTUATION
from ostilhou.corpora import load_wikipedia_150k, load_sarmoniou
from ostilhou.asr import phonetize
from ostilhou.hspell import get_hspell_mistakes



def test_tokenize(sentence):
    for t in tokenize(sentence, norm_punct=True):
        print(t, t.norm)


def test_detokenize(sentence):
    print(detokenize(tokenize(sentence, norm_punct=True), end_sentence='\n'))


def test_normalize(sentence):
    for token in tokenize(sentence):
        print(token, token.norm)
    print(detokenize(normalize(tokenize(sentence))))


def test_wiki150_noun_gender():
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
    sentences = set()
    sentences_norm = set()
    n_parsed = 0
    #with open("ostilhou/corpora/wikipedia-br-150k.txt", 'r') as fin:
    with open("ya_dump.txt", 'r') as fin:
        for line in fin.readlines():
            if line:
                line = pre_process(line).replace('*', '').replace('OOO', '000')
                line = filter_out(line, OPENING_QUOTES + CLOSING_QUOTES)
                for sentence in split_sentences(line, end=''):
                    n_parsed += 1

                    # if re.search(PATTERN_DOTTED_ACRONYM, sentence):
                    #     print(sentence)

                    stats = sentence_stats(sentence)
                    if stats["upper"] / len(sentence) > 0.2:
                        # Lots of uppercases
                        continue
                    if stats["letter"] / len(sentence) < 0.5:
                        # Too few letters
                        continue
                    if re.search(r"\d\d \d\d ", sentence):
                        # Telephone numbers
                        continue
                    if re.search(r"\d\d\.\d\d\.", sentence):
                        # Telephone numbers (no match but it doesn't harm either)
                        continue
                    if re.search(r"[\w.]+@[\w.]+", sentence):
                        # E-mail adresses
                        continue
                    if '@' in sentence:
                        # E-mail adresses, more severe
                        continue

                    if sentence.startswith("– "):
                        sentence = sentence[2:]
                    elif re.match(r"\d – ", sentence):
                        sentence = sentence[4:]
                    elif re.match(r".\) ", sentence):
                        sentence = sentence[3:]
                    elif re.match(r".'\) ", sentence):
                        sentence = sentence[4:]
                    
                    ntok = len(sentence.split())
                    if ntok < 3:
                        # Sentences is too short
                        continue

                    sentence = detokenize(tokenize(sentence, autocorrect=True))

                    colored, n_mistakes = get_hspell_mistakes(sentence)
                    if n_mistakes >= 1:
                        print(colored)
                    elif n_mistakes == 0:
                        # Capitalize first letter
                        # sentence = sentence[0].upper() + sentence[1:]
                        sentences.add(sentence)
                    
                    # leave out inclusive words for now, as they can't be phonetized yet
                    if '·' in sentence:
                        continue

                    normalized = normalize_sentence(sentence)
                    normalized = filter_out(normalized, PUNCTUATION + '<#>').replace('-', ' ')
                    _, n_mistakes = get_hspell_mistakes(normalized)
                    if n_mistakes == 0:
                        sentences_norm.add(' '.join(normalized.split()))

    with open("ya_propr.txt", 'w') as fout:
        for sentence in sorted(sentences):
            fout.write(sentence + '\n')

    # with open("comparaison.txt", 'w') as fout:
    #     for sentence in sorted(sentences):
    #         normalized = normalize_sentence(sentence)
    #         if len(sentence) != len(normalized):
    #             fout.write(sentence + '\n')
    #             fout.write(normalized + '\n\n')

    n_kept = 0
    with open("ya_propr_norm.txt", 'w') as fout:
        for sentence in sorted(sentences_norm):
            if not re.search("[0-9]", sentence):
                fout.write(sentence + '\n')
                n_kept += 1
    
    print(f"Total sentences: {n_parsed}")
    print(f"Kept: {len(sentences)} ({len(sentences)/n_parsed:.2%})")
    print(f"Kept (normalized): {n_kept} ({n_kept/n_parsed:.2%})")



if __name__ == "__main__":
    sentence = "pemzek cl laezh ha tri ugent"
    # test_tokenize(sentence)
    # print(get_hspell_mistakes(sentence)[0])
    # test_detokenize(sentence)
    test_normalize(sentence)
    # test_wiki150_noun_gender()
    # test_sarmoniou()
    # sentence = filter_out(sentence, OPENING_QUOTES + CLOSING_QUOTES)
    # for s in split_sentence(sentence):
    #     print(s, end='')
    
    # test_clean_ya()