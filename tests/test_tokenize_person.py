from ostilhou.text.tokenizer import tokenize, generate_person_tokens, TokenType



def test_nouns():
    sentences = [
        "Yann Kervella",
        "Gweltaz Duval-Guennoc",
        "Janig an Duigou",
        "Aotrou Kalvez",
        "it. Marie Morvan",
    ]

    for sentence in sentences:
        print("#####")
        tokens = list(generate_person_tokens(tokenize(sentence)))
        print(tokens[0])
        assert len(tokens) == 1 and tokens[0].type == TokenType.PERSON