from ostilhou.asr.dataset import (
    load_ali_file, parse_ali_file,
    MetadataParser
)


def test_ali_parser():
    lines = [
        "{lang: br}\n",
        "{speaker: Yann-Bêr Duval; gender:m}\n",
        "Demat, mont a ra ? {lang: fr}Oui.{lang:br}\n",
        "Ah ya ?\n",
        "{spk:Marie Lagadec} Unan, daou tri{?}\n",
        "{lang: es}hola{lang:br} demat\n"
    ]

    parser = MetadataParser()

    # print("####################")
    # for line in lines:
    #     print("#######")
    #     print(line)
    #     regions = parser.parse_sentence(line)
    #     for text, metadata in regions:
    #         print(f"{text=}")
    #         print(f"{metadata=}")
    
    parser.reset()
    regions = parser.parse_sentence(lines[0])
    assert regions[0][1]["lang"] == "br"

    regions = parser.parse_sentence(lines[1])
    assert regions[0][1]["speaker"] == "yann-bêr_duval"
    assert regions[0][1]["gender"] == "m"

    regions = parser.parse_sentence(lines[2])
    assert len(regions) == 2
    assert regions[0][1]["speaker"] == "yann-bêr_duval"
    assert regions[0][1]["gender"] == "m"
    assert regions[1][1]["lang"] == "fr"

    regions = parser.parse_sentence(lines[3])
    assert regions[0][1]["lang"] == "br"

    regions = parser.parse_sentence(lines[4])
    assert regions[0][1]["speaker"] == "marie_lagadec"

    parser.set_filter({"lang": "br"})
    regions = parser.parse_sentence(lines[5])
    assert len(regions) == 1


# def test_load_file():
#     r = parse_ali_file("tests/da_anv_br.ali", {"subtitles": False})