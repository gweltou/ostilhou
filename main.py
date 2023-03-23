from talbr import tokenize, detokenize
from talbr.text import normalize, strip_punct, split_sentence, load_translation_dict, translate
from talbr.corpora import load_wikipedia_150k, load_sarmoniou


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
    # Extract words following the cardinals 'un', 'ur', 'ul', 'daou' and 'div'
    # Write them to files

    sentences = load_wikipedia_150k()
    print(len(sentences))
    card = ['un', 'ur', 'ul', 'daou', 'div']
    d = {denom : set() for denom in card}
    for sentence in sentences:
        words = sentence.split()
        for card in d.keys():
            try:
                i = words.index(card)
                if i+1 < len(words):
                    word = strip_punct(words[i+1])
                    if word.endswith("-se"):
                        word = word[:-3]
                    elif word.endswith("-mañ"):
                        word = word[:-4]
                    d[card].add(word)
            except ValueError:
                continue
    
    for card in d.keys():
        with open(card + ".txt", 'w') as f:
            f.writelines( [n+'\n' for n in sorted(d[card])] )


def test_sarmoniou():
    sarmoniou = load_sarmoniou()

    # Using a translation dictionary to replace words with their modern form
    td = load_translation_dict("talbr/dicts/old_leoneg.tsv")

    # with open("sarmonioù.txt", 'w') as f:
    #     for line in sarmoniou:
    #         f.write(detokenize( translate(tokenize(line), td) ) + '\n')
    for line in sarmoniou:
        print(detokenize( translate(tokenize(line), td) ))
    


if __name__ == "__main__":
    sentence = ""
    # test_tokenize(sentence)
    # test_detokenize(sentence)
    # test_wiki150()
    test_sarmoniou()

