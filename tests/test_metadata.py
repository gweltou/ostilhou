from ostilhou.asr.dataset import extract_metadata


def test_metadata():
    test_cases = [
        ("demat {anv-bihan anv}", "demat", {'speaker':'anv-bihan_anv'}),
        ("unknown{?} words {?}here", "unknown words here", {'unknown': [0, 2]}),
        ("{spk: abc def; gender:f} o komz emaon", "o komz emaon", {'speaker':'abc_def', 'gender':'f'}),
        ("{spk:marc'harid; gender:f}", "", {'speaker': "marc'harid", 'gender': 'f'}),
        ("{c'h-ch d}", "", {'speaker': "c'h-ch_d"}),
        ("{anv-bihan familh; gender:f; accent:gwened}", "", {'speaker': "anv-bihan_familh", 'gender': 'f', 'accent': ['gwened']}),
        ("\n{parser:no-lm}\n\n", "", {'parser': 'no-lm'}),
        ("{accent: gwenedeg, }", "", {'accent': ['gwenedeg']}),
        ("{mac'ha-rid le lagadeg}", "", {'speaker': "mac'ha-rid_le_lagadeg"}),
        ("{accent:kerneveg, kemper}", "", {'accent': ['kerneveg', 'kemper']}),
        ("{source-audio: http://www.radiobreizh.bzh/medias/19961031-Ar-melour-Pierre-Ollivier-RKB20180.mp3}",
        "", {'source-audio': 'http://www.radiobreizh.bzh/medias/19961031-Ar-melour-Pierre-Ollivier-RKB20180.mp3'}),
        ("{tags: rkb}", "", {"tags": ["rkb"]}),
        ("{tags: radio, rkb}", "", {"tags": ["radio", "rkb"]}),
    ]

    for t in test_cases:
        sentence, metadata = extract_metadata(t[0])
        print(sentence)
        print(metadata)
        print()
        assert sentence.strip() == t[1]
        assert metadata == t[2]