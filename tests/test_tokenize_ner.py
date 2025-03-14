from ostilhou.text.tokenizer import tokenize, detokenize, Token



def test_nouns():
    sentences = [
        "Pebezh gador-mañ vrav !",
        "Demat Itron Marie-Françoise, Oliver eo va anv.",
        "E Bro Elzas ez eus ur ster.",
        "Elen a oa o labourat e Vrest abaoe div sizhun",
        "An RATP a zo o verañ trenioù e Pariz."
    ]

    for sentence in sentences:
        print("#####")
        tokens = list(tokenize(sentence))
        for t in tokens:
            print(t)