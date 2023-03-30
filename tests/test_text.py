from ostilhou.text import extract_parenthesis_content


def test_extract_parenthesis_content():
    s1 = "Iwerzhonad a-orin eo ar prezidant nevez (gant e vamm-gozh, hag a oa o chom gantañ ha gant e dud. Komzet e veze iwerzhoneg er gêr zoken) ha lorc'h ennañ."
    r, p = extract_parenthesis_content(s1)
    assert len(r) == 57
    assert len(p) == 1
