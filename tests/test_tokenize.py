
from ostilhou import tokenize, detokenize
from ostilhou.text import split_sentences
from ostilhou.text.tokenizer import TokenType



def test_tokenizer():
    def num_tokens(s):
        return len(list(tokenize(s)))
    
    test_cases = [
        ("unan daou tri", 3),
        ("demat,deoc'h", 3),
        ("fin miz Gouere.Laouen e oa", 8), # +1 for EOS token
    ]

    for s, n in test_cases:
        assert num_tokens(s) == n


def test_split_sentence():
    test_cases = [
        ("Un tan-gwall a voe d'ar 1añ a viz Gouhere 2011 el leti. Ne voe den ebet gloazet pe lazhet. Un nebeud estajoù nemetken a oa bet tizhet.", 3),
        ("unan daou tri : pevar pemp c'hwec'h", 1),
        ("Cheñchet en deus ar mor e douar sec'h. Treuzet hon eus ar stêr war droad.", 2),
        ("Tamm ebet. Klasket em boa e-pad 5 miz ha n’on ket bet plijet ; un afer a bublik eo.", 2),
        ("Tout an dud en em soñj. Piv int ar skrivagnerien-se ? Eus pelec'h emaint o tont... ?", 3),
        ("E 1938 e voe he gwaz harzet ha lazhet en U. R. S. S., ar pezh na viras ket ouzh Ana Pauker a chom feal d'ar gomunouriezh, d'an U. R. S. S. ha da Jozef Stalin.", 1),
        ("Ur maen-koun zo war lein, da bevar barzh eus ar vro : T. Hughes Jones, B.T. Hopkins, J. M. Edwards hag Edward Prosser Rhys.", 1),
        ("Dindan anv A. J. Orde, E. E. Horlak, ha B. J. Oliphant he-deus skrivet hag hec'h oberennoù kentañ a voe embannet dindan anv Sheri S. Eberhart.", 1),
        ("""Hervez Levr ar C'heneliezh ec'h eo Yafet eil mab Noah. Hervez ar Bibl e tiskouezas doujañs e-kenver e dad mezv-dall. Benniget e voe gantañ evel Shem : "Frankiz ra roio Doue da Yafet ! Ha ra chomo e tinelloù Shem !" """, 3),
        ("""C'hoariet en deus evit Stade Rennais Football Club etre 1973 ha 1977 hag e 1978-1979. Unan eus ar c'hoarierien wellañ bet gwelet e klub Roazhon e oa. Pelé en deus lavaret diwar e benn : « Kavet 'm eus an hini a dapo ma flas. Laurent Pokou e anv. ».""", 3),
        ("Sed aze pal ar « c'hendivizad a-ziforc'h evit treuzkas yezhoù Breizh (2022-2027) ». Sinet e oa bet ivez d'ar Meurzh 15 a viz Meurzh 2022 e Roazhon.", 2),
        ("Eilpennet dehoù/kleiz eo ar skoed a zo diskouezet war Commons e-keñver an hini a zo war lec'hienn kêr Lambal, war Armor Magazine (Mae 1997) hag en Armorial des communes des Côtes-d'Armor Froger & Pressensé, 2008, p. 34 ; Kuzul ar Gumun : 16 a viz Here 1994.", 1),
        ("""Dirak an it. Lena Louarn, besprezidantez ar C’huzul-rannvro karget eus yezhoù Breizh ha prezidantez OPAB,
            an it. Solange Creignou, besprezidantez Kuzul-departamant Penn-ar-Bed dileuriet evit ar brezhoneg,
            an it. Isabelle ar Bal, eilmaerez 1añ Kemper hag an ao. Jean-Luc Bleunven, kannad eus Penn-ar-Bed,
            eo bet sinet an emglev Ya d’ar brezhoneg gant an ao. Mathieu Gallou, prezidant ar skol-veur.""", 1),
        ("O teskin brezhoneg emaoc’h (live 1, 2) ha c’hoant ho peus d’en em lakaat da gaozeal Deuit gant Kristin Ar Menn evit un endervezh plijus e brezhoneg Petra vo graet ? C’hoarioù (daou-ha-daou, a-stroll, etc..) evit gwelout penaos ober anaoudegezh ha kaozeal e-pad ar predoù. E fin an endervezh e vo graet merenn-vihan ganeomp ha implijet […]", 4),
    ]

    for t in test_cases:
        sub_sentences = split_sentences(t[0])
        print(t[0])
        sub_sentences = list(sub_sentences)
        assert len(sub_sentences) == t[1]


def test_detokenize():

    def should_be_equal(s: str) -> None:
        toklist = tokenize(s)
        assert s == detokenize(toklist)

    def should_be(s1: str, s2: str) -> None:
        toklist = tokenize(s1)
        assert s2 == detokenize(toklist)
    
    should_be_equal('"Digoret eo ar brezel douzh ar viruz brein-se."')
    should_be_equal('Ha n\'int ket gwelet mat gant tud ar vro. "Estrañjourion eo ar re-se, traken" en deus lavaret ministr an deskadurezh.')

    should_be('Un deiz bennag, he \ndoa lâret ar brezidantez, e \nvint sovet marse ha lakaet da \nzoned a varw da véw gant ar\n"jeni-jenetik".',
                'Un deiz bennag, he doa lâret ar brezidantez, e vint sovet marse ha lakaet da zoned a varw da véw gant ar "jeni-jenetik".')
    should_be('Ha setu perak ‚oa bet divizet ganeomp', 'Ha setu perak‚ oa bet divizet ganeomp') # Sneaky fake comma
    should_be("al labour- \ndouar", "al labour-douar")
    should_be('3 / 4 eus an dud.', '3/4 eus an dud.')
    should_be('Dindan c\'hwec\'h vloaz :digoust.', 'Dindan c\'hwec\'h vloaz\xa0: digoust.')
    should_be("unan... daou ...tri ... pevar ....pemp!... c'hwec'h,....seizh", "unan... daou... tri... pevar.... pemp !... c'hwec'h,.... seizh")
    should_be("n'eus ster ebet, « na penn na lost» da gement-se.", "n'eus ster ebet, «\xa0na penn na lost\xa0» da gement-se.")
    should_be("un abadenn “ mikro digor” tro-dro d’ar rap", "un abadenn “mikro digor” tro-dro d’ar rap")
    should_be("Gouel Broadel ar Brezhoneg ( GBB ) .", "Gouel Broadel ar Brezhoneg (GBB).")
    should_be("8,6 M€, 2 cm2", "eizh virgulenn c'hwec'h milion euro, daou santimetr karrez")


def test_norm_punct():
    def should_be(s1: str, s2: str) -> None:
        toklist = tokenize(s1, norm_punct=True)
        assert s2 == detokenize(toklist, normalize=True)
    
    should_be("unan... daou ...tri ... pevar ....pemp!... c'hwec'h,....seizh", "unan… daou… tri… pevar… pemp !… c'hwec'h,… seizh")
    should_be("ur virgulenn‚ lous", "ur virgulenn, lous")


def test_split_into_sentences():
    count_sentences = lambda s: len(detokenize(tokenize(s), end='\n').split('\n'))-1

    assert 2 == count_sentences("Demat. Mont a ra ?")
    assert 1 == count_sentences("\"N'eo ket gwir !\" a huchas heñ.")
    assert 1 == count_sentences("«N'eo ket gwir !» a huchas heñ.")


def test_tokenize_list():
    sentences = [
        "Tregont vloaz da c'houde, am",
        'eus kroget da ziskrivañ al levr evit e',
        'embann war ar roued. Echu eo bremañ',
        'al labour hag hir e voe ! Gant un',
        'hanter-eur evit pep pajenn ha teir fajenn',
        "pep sizhun, n'eo ket diaes jediñ an amzer",
        'ma voe ret din evit diskrivañ ar pevar',
        "c'hant pajenn eus al levr-se. Spi am eus ma",
        'vo va labour talvoudus evit an holl re o',
        "deus c'hoant d'ober enklaskoù e skridoù",
        'kozh evel ar "Sarmonioù".',
    ]

    assert len(detokenize(tokenize(sentences))) == 411


def test_autocorrection():
    def should_be(sent: str, correction: str) -> str:
        assert detokenize(tokenize(sent, autocorrect=True)) == correction
    
    should_be("kemer an taski", "kemer an taxi") 
    should_be("abadenn France 3", "abadenn Frañs 3")
    should_be("abadenn France 3", "abadenn Frañs 3")
    should_be("Hirio on aet war twitter", "Hiziv on aet war Twitter")
    should_be("Ar bleuñ", "Ar bleuñv")


def test_abbreviations():
    def should_be(sent: str, correction: str) -> str:
        assert detokenize(tokenize(sent), normalize=True) == correction
    
    should_be("Demat It. Marie", "Demat Itron Marie")



def test_metadata():
    sentence = "{parser: ignore}– Kerry Scully o komz. Ezhomm skoazell 'm eus.{parser: add}"
    assert list(tokenize(sentence))[0].type == TokenType.METADATA