from ostilhou.text.tokenizer import tokenize, detokenize, Token



def test_nouns():
    sentences = [
        "Pebezh gador-mañ vrav !",
        "Demat Itron Marie-Françoise, Oliver eo va anv.",
        "E Bro Elzas ez eus ur ster."
    ]

    for sentence in sentences:
        tokens = list(tokenize(sentence))
        for t in tokens:
            print(t)