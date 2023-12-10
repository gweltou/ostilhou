from typing import List
from ostilhou.asr.post_processing import apply_post_process_dict_text, post_process_timecoded, post_process_text


test_cases = [
    ("e penn ar bed ez eus un tour tan", "e Penn-ar-Bed ez eus un tour-tan"),
    ("new york n'emañ ket e breizh izel", "New York n'emañ ket e Breizh-Izel"),
    ("Emañ Nolwenn war he marc'h houarn", "Emañ Nolwenn war he marc'h-houarn"),
    ("naontek dregant ha tri ugent", "79 %"),
    ("Euh mont a ra kwa !", "mont a ra !"),
    ("Evel se mañ", "evel-se mañ")
]


def test_post_process_text():
    def should_be(s1: str, s2: str) -> None:
        hyp = post_process_text(s1, normalize=True, keep_fillers=False)
        print(hyp)
        assert hyp == s2
    
    for test in test_cases:
        should_be(test[0], test[1])



# def test_post_process_vosk():

#     def tokenize(s: str) -> List[dict]:
#         return [{"word":t, "start":2*i, "end":2*i+1, "conf":1.0} for i, t in enumerate(s.split())]
    
#     def detokenize(tokens: List[dict]) -> str:
#         return [t["word"] for t in tokens]

#     def should_be(s1: str, s2: str) -> None:
#         tokens = post_process_vosk(tokenize(s1), normalize=True, remove_fillers=True)
#         # Check timecode order
#         for i in range(len(tokens)-1):
#             assert tokens[i]["start"] < tokens[i+1]["start"]
#         hyp = ' '.join(detokenize(tokens))
#         print(hyp)
#         assert hyp == s2
    
#     for test in test_cases:
#         should_be(test[0], test[1])
    