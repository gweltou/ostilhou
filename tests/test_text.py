from ostilhou.text import extract_parenthesis_content, capitalize, correct_sentence
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


def test_capitalize():
    def should_be(s1, s2):
        assert capitalize(s1) == s2
    
    should_be("demat", "Demat")
    should_be("demat Yann-Fañch", "Demat Yann-Fañch")
    should_be("'vit se", "'Vit se")
    should_be("«ya!»", "«Ya!»")


def test_correct_sentence():
    assert correct_sentence("covid-19") == "Covid 19"