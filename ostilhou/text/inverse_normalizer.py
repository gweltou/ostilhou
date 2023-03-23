
token_value = {
    "mann" : 0, "zero" : 0,
    "un" : 1, "ur" : 1, "ul" : 1, "unan" : 1,
    "daou" : 2, "div" : 2,
    "tri" : 3, "teir" : 3,
    "pevar" : 4, "peder" : 4,
    "pemp" : 5,
    "c'hwec'h" : 6,
    "seizh" : 7,
    "eizh" : 8,
    "nav" : 9,
    "dek" : 10,
    "unnek" : 11,
    "daouzek" : 12,
    "trizek" : 13,
    "pevarzek" : 14,
    "pemzek" : 15,
    "c'hwezek" : 16,
    "seitek" : 17,
    "triwec'h" : 18,
    "naontek" : 19,
    "ugent" : 20,
    "tregont" : 30,
    "kant" : 100, "c'hant" : 100,
    "mil" : 1000, "vil" : 1000,
    "milion" : 1_000_000, "vilion" : 1_000_000,
    "miliard" : 1_000_000_000, "viliard" : 1_000_000_000,
    "hanter" : 0.5,
    "ha" : '+', "hag" : '+', "warn" : '+'
}


def solve_num_tokens(numerical_tokens):
    # Token 0.5 ("hanter") takes precedence and is applied to next closest token
    while 0.5 in numerical_tokens:
        i = numerical_tokens.index(0.5)
        if i < len(numerical_tokens) - 1:
            numerical_tokens = numerical_tokens[:i] + [0.5*numerical_tokens[i+1]] + numerical_tokens[i+2:]
        else:
            break

    # Find highest value token
    i_max, val_max = -1, -1
    i_token_add, token_add = -1, False
    for i, val in enumerate(numerical_tokens):
        if val == '+':
            token_add = True
            i_token_add = i
        elif val > val_max:
            val_max = val
            i_max = i
    
    if token_add and val_max < 100:
        # Invert two parts of token_list around '+' symbol and solve
        inverted = numerical_tokens[i_token_add+1:] + numerical_tokens[:i_token_add]
        return solve_num_tokens(inverted)
    else:
        # solve recursively
        if len(numerical_tokens) == 0:
            return 0
        elif len(numerical_tokens) == 1:
            return numerical_tokens[0]
        else:
            left_part = solve_num_tokens(numerical_tokens[:i_max])
            if left_part == 0:
                left_part = 1
            right_part = solve_num_tokens(numerical_tokens[i_max+1:])
            return left_part * val_max + right_part



def inverse_normalize_sentence(sentence: str) -> str:
    """ Translate spelled form numerical values to more readable numbers
        This is a simple function expected to work on STT output with no punctuation
        The sentence is simply split on whitespaces
    """
    
    print(sentence)
    return ""