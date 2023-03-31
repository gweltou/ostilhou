from ostilhou.text import extract_parenthesis_content
from ostilhou.text.definitions import is_proper_noun


def test_extract_parenthesis_content():
    s1 = "Iwerzhonad a-orin eo ar prezidant nevez (gant e vamm-gozh, hag a oa o chom gantañ ha gant e dud. Komzet e veze iwerzhoneg er gêr zoken) ha lorc'h ennañ."
    r, p = extract_parenthesis_content(s1)
    assert len(r) == 57
    assert len(p) == 1


def test_proper_noun():
    assert is_proper_noun("Eleonore")
    assert is_proper_noun("Marie-Jeanne")
    assert is_proper_noun("Marie-Christine")
    assert not is_proper_noun("Debdeb")