from ostilhou.asr.aligner import align, _prepare_text



def test_prepare_text():
    test_cases = [
        ("- Demat Deni ! Pelec’h emaout ?", "dematdenipeleXemaout"),
    ]

    for ref, hyp in test_cases:
        assert hyp == _prepare_text(ref)



def test_aligner():
    sentences = [
        "- Demat Bleuenn ! Dale zo ganin, digarez.",
        "- Demat Deni ! Pelec’h emaout ?",
        "- E kreiz-kêr Kemper emaon c’hoazh. Stank eo an dremeniri.",
        "- Mat eo. Gortoz a reomp ac’hanout. Na rez ket bil !",
        "- Trugarez dit. - Ken bremaik.",
    ]

    hyp = [
        {'conf': 1.0, 'end': 0.54, 'start': 0.18, 'word': 'demat'},
        {'conf': 0.748311, 'end': 1.02, 'start': 0.54, 'word': 'bleuñv'},
        {'conf': 0.97706, 'end': 2.01, 'start': 1.710159, 'word': 'dale'},
        {'conf': 1.0, 'end': 2.16, 'start': 2.01, 'word': 'zo'},
        {'conf': 0.996774, 'end': 2.580138, 'start': 2.16, 'word': 'ganin'},
        {'conf': 0.99998, 'end': 3.45, 'start': 2.79, 'word': 'digarez'},
        {'conf': 0.503817, 'end': 4.676278, 'start': 4.269406, 'word': 'nemet'}, #6
        {'conf': 0.951045, 'end': 4.98, 'start': 4.680731, 'word': 'enni'},
        {'conf': 1.0, 'end': 6.06, 'start': 5.73, 'word': "pelec'h"},
        {'conf': 1.0, 'end': 6.57, 'start': 6.06, 'word': 'emaout'}, #9
        {'conf': 0.992537, 'end': 7.71, 'start': 7.68, 'word': 'e'},
        {'conf': 1.0, 'end': 8.07, 'start': 7.71, 'word': 'kreiz'},
        {'conf': 1.0, 'end': 8.31, 'start': 8.07, 'word': 'kêr'},
        {'conf': 0.985919, 'end': 8.790053, 'start': 8.31, 'word': 'Kemper'},
        {'conf': 0.988489, 'end': 9.03, 'start': 8.790053, 'word': 'emañ'},
        {'conf': 1.0, 'end': 9.51, 'start': 9.030345, 'word': "c'hoazh"},
        {'conf': 1.0, 'end': 10.5, 'start': 10.08, 'word': 'stank'},
        {'conf': 1.0, 'end': 10.62, 'start': 10.5, 'word': 'eo'},
        {'conf': 1.0, 'end': 10.74, 'start': 10.62, 'word': 'an'},
        {'conf': 1.0, 'end': 11.43, 'start': 10.74, 'word': 'dremeniri'}, #19
        {'conf': 0.970097, 'end': 12.9, 'start': 12.63, 'word': 'mat'},
        {'conf': 1.0, 'end': 13.2, 'start': 12.9, 'word': 'eo'},
        {'conf': 1.0, 'end': 14.37, 'start': 13.92, 'word': 'gortoz'},
        {'conf': 1.0, 'end': 14.43, 'start': 14.37, 'word': 'a'},
        {'conf': 0.689874, 'end': 14.669006, 'start': 14.43, 'word': 'reont'},
        {'conf': 0.497754, 'end': 14.759442, 'start': 14.67, 'word': 'ar'},
        {'conf': 0.255605, 'end': 15.27, 'start': 14.759442, 'word': "c'hannad"},
        {'conf': 0.840543, 'end': 15.599797, 'start': 15.42, 'word': 'na'},
        {'conf': 0.97553, 'end': 15.78, 'start': 15.6, 'word': 'rez'},
        {'conf': 1.0, 'end': 15.93, 'start': 15.78, 'word': 'ket'},
        {'conf': 1.0, 'end': 16.29, 'start': 15.93, 'word': 'bil'},
        {'conf': 1.0, 'end': 17.52, 'start': 16.98, 'word': 'trugarez'},
        {'conf': 1.0, 'end': 17.82, 'start': 17.52, 'word': 'dit'},
        {'conf': 0.514245, 'end': 18.84, 'start': 18.63, 'word': 'kent'},
        {'conf': 1.0, 'end': 19.35, 'start': 18.84, 'word': 'bremaik'}
    ]

    matches = align(sentences, hyp, 0, len(hyp))

    print(matches)
    assert matches[0]["span"] == (0, 6)
    assert matches[1]["span"] == (6, 10)
    assert matches[2]["span"] == (10, 20)
    assert matches[3]["span"] == (20, 31)
    assert matches[4]["span"] == (31, 35)