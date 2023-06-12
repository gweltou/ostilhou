from ostilhou.text.normalizer import normalize, normalize_sentence, norm_ordinal, norm_roman_ordinal
from ostilhou.text.tokenizer import is_ordinal, is_roman_ordinal
from ostilhou.text.normalizer import solve_mutation_article, solve_mutation_number


def test_normalization():

    def should_be(s1: str, s2: str) -> None:
        normalized = normalize_sentence(s1)
        print(normalized)
        assert s2 == normalized

    test_cases = [
        # Mine
        ("d'an 3 a viz Here", "d'an tri a viz Here"),
        ("1 skouerenn", "ur skouerenn"),
        ("tro dro da 85000 den e Mec'hiko", "tro dro da pemp ha pevar-ugent mil den e Mec'hiko"),
        ("12 000 euro", "daouzek mil euro"),
        ("92 ki", "daouzek ki ha pevar-ugent"),
        ("Ouzhpenn da 42 bemdez", "ouzhpenn da daou ha daou-ugent bemdez"),
        ("51 dre den", "unan hag hanter-kant dre den"),
        ("da lavaret eo 950km", "da lavaret eo nav c'hant hanter-kant kilometr"),
        ("72 m eo he uhelder keitat", "daouzek metr ha tri-ugent eo he uhelder keitat"),
        ("75m2 eo gorread an dachenn", "pemzek metr karrez ha tri-ugent eo gorread an dachenn"),
        ("Un dachenn 5km²", "un dachenn pemp kilometr karrez"),
        ("34% e 2010", "pevar ha tregont dre gant e daou vil dek"),
        ("35 % eus al loened", "pemp ha tregont dre gant eus al loened"),
        ("12e30, 11e35, 9e15, 8e45", "kreisteiz hanter, unnek eur pemp ha tregont, nav eur ha kard, nav eur nemet kard"),
        ("da 5e56 e roas an urzh", "da c'hwec'h eur nemet pevar e roas an urzh"),
        ("kement mañ tout etre 2 eur ha 7eur abardaez", "kement mañ tout etre div eur ha seizh eur abardaez"),
        ("Loeiz XVI", "Loeiz c'hwezek"),
        ("kemeret perzh er 7vet hag en 8vet kuzuliadegoù", "kemeret perzh er seizhvet hag en eizhvet kuzuliadegoù"),
        ("en XXIvet kantved", "en un warn-ugentvet kantved"),
        ("1 vloaz, 2 bloaz, 3 bloaz, 5 bloaz, 10 bloaz", "ur bloaz, daou vloaz, tri bloaz, pemp bloaz, dek vloaz"),
        ("d'an oad a 25 bloaz", "d'an oad a pemp bloaz warn-ugent"),
        ("e 1982 e varvas", "e mil nav c'hant daou ha pevar-ugent e varvas"),
        ("1, 1 c'hazh, 21 loarenn", "unan, ur c'hazh, ul loarenn warn-ugent"),
        ("32 687 bit", "daou ha tregont mil c'hwec'h kant seizh bit ha pevar-ugent"),
        ("Bichon bihan en doa strobinellet 2.500 den.", "Bichon bihan en doa strobinellet daou vil pemp kant den."),
        ("e 2021 ez eus ganet 32 065 babig, 1 072 muioc'h eget e 2020 +35 %", ""),
        ("9 400 en Il-ha-Gwilen +09 % ouzhpenn 3 800 er Morbihan +05% ouzhpenn 500 en aodoù an Arvor", ""),
        ("klask ar 500 000€ a vo ezhomm", "klask ar pemp kant mil euro a vo ezhomm"),
        ("21000 steredenn", "unan warn-ugent mil steredenn"),
        ("1kg sukr, 1kg bleud", "ur c'hilo sukr, ur c'hilo bleud"),
        ("1m2, 2m2, 3m3", "ur metr karrez, daou metr karrez, tri metr diñs"),
        ("1cm, 2cm2, 3cm3", "ur santimetr, daou santimetr karrez, tri santimetr diñs"),
        ("20 € em eus en va chakod, ha n'eo ket 20$", "ugent euro em eus en va chakod, ha n'eo ket ugent dollar"),
        ("da 4 c'hm eus kreiz Montroulez e c'houlenne ar rannvro 200 000€ o c'houzout e oa ivez goude evit 1M€ a labourioù", "da pevar c'hilometr eus kreiz Montroulez e c'houlenne ar rannvro daou c'hant mil euro o c'houzout e oa ivez goude evit ur milion euro a labourioù"),
        ("da 1e g.m., pe da 2e gm.", "da un eur goude meren, pe da ziv eur goude meren"),
        ("d’ar Sadorn 1añ a viz Ebrel da 8e30 noz e france.tv ha da 0e15 war France 3 Breizh.", ""),
        ("1,5, 3,50 €, 1,001%", "unan virgulenn pemp, tri euro hanter-kant, unan virgulenn mann mann unan dre gant"),
        ("13,1 km, 378 m a zinaou", ""),

        # OPAB - Mozilla Common Voice
        ("Un 40 den bennak.", "un daou-ugent den bennak."),
        ("Un 20 c'hoarier bennak.", "un ugent c'hoarier bennak."),
        ("Un 30 studier bennak.", "un tregont studier bennak."),
        ("Un 50 polis bennak.", "un hanter-kant polis bennak."),
        ("Ur 15 istrogell bennak.", "ur pemzek istrogell bennak."),
        ("Sul 14 a viz Mezheven 1998.", "Sul pevarzek a viz Mezheven mil nav c'hant triwec'h ha pevar-ugent."),
        ("D'ar Sul 24 a viz C'hwevrer 2008.", "d'ar Sul pevar warn-ugent a viz C'hwevrer daou vil eizh."),
        ("XIIvet betek ar XVIIvet kantved.", "daouzekvet betek ar seitekvet kantved."),
        ("Sadorn eus nav eur da 12h00 ", "Sadorn eus nav eur da greisteiz"),
        ("pe abadenn da 15e + atalier da 16e 7,00 € dre vugel.", "pe abadenn da teir eur muiñ atalier da peder eur seizh euro dre vugel."),
        ("Pep ½ eurvezh a fakturenner ha n’eo ket pep eurvezh.", ""),
        ("Straed Sz Anna - 02.97.60.78.49.", ""),
        ("bali ar Jeneral de Gaulle - 02.97.60.72.94.", "bali ar jeneral de Gaulle - mann daou, daou seizh, c"),
        ("Bras / Bihan.", "Bras/Bihan."),
        ("26 vloaz on.",""),
        ("32 vloaz on.",""),
        ("6'2 bras on.",""),

        # OPAB - Aziliz
        ("HEULIAÑ AR PRODUIOÙ, SURENTEZ AR BOUED, LEC'H GWAREZET.", "heuliañ ar produioù, surentez ar boued, lec'h gwarezet."),
    ]

    for t, gt in test_cases:
        should_be(t, gt)

    

def test_ordinal_normalization():
    test_cases = ["1añ", "2vet", "3de", "3vet", "IIIde", "4e", "IVe", "4re", "4vet", "5vet", "17vet", "XIIvet", "123vet", "XXIvet"]
    for t in test_cases:
        print(t, end=' ')
        if is_ordinal(t): print(norm_ordinal(t))
        elif is_roman_ordinal(t): print(norm_roman_ordinal(t))
        else: print("Not an ordinal", t)



def test_mutations_articles():

    def should_be(s1: str, s2: str) -> None:
        mutated = solve_mutation_article(*s1.split())
        assert s2 in mutated
    
    should_be("ar ki", "ar c'hi")
    should_be("an dor", "an nor")
    should_be("ur kador", "ur gador")
    should_be("ar paner", "ar baner")
    should_be("ul taol", "un daol")
    should_be("an godell", "ar c'hodell")
    should_be("ar gwastell", "ar wastell")
    should_be("ar bag", "ar vag")
    should_be("ar mamm", "ar vamm")
