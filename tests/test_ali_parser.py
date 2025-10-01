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
    data, _ = parser.parse_sentence(lines[0])
    assert data[0]["lang"] == "br"

    data, _ = parser.parse_sentence(lines[1])
    assert data[0]["speaker"] == "yann-bêr_duval"
    assert data[0]["gender"] == "m"

    data, _ = parser.parse_sentence(lines[2])
    assert len(data) == 2
    assert data[0]["speaker"] == "yann-bêr_duval"
    assert data[0]["gender"] == "m"
    assert data[1]["lang"] == "fr"

    data, _ = parser.parse_sentence(lines[3])
    assert data[0]["lang"] == "br"

    data, _ = parser.parse_sentence(lines[4])
    assert data[0]["speaker"] == "marie_lagadec"

    parser.set_filter_in({"lang": "br"})
    data, _ = parser.parse_sentence(lines[5])
    assert len(data) == 1


def test_load_file():
    utterances = parse_ali_file("/home/gweltaz/STT/aligned/Brezhoweb/V9Gw_1BLKZA-Al_Liviou_-_Les_couleurs_en_breton_Mona_Jaouen_-_Toutouig.ali", {"lang": "br"})
    
    print(utterances[:2])
    print("############################")
    for regions, segment in utterances:
        text = ''.join([ r['text'] for r in regions ]).strip()
        print(segment, text)
        # for r in regions:
        #     print(r)


def test_parse_ali():
    ali_data = """
        {spk: George M.; gender: m}
        {lang: br; accent: leoneg}
        {start: 1.0; end: 4.0}Demat bed holl !
        {start: 4.0; end: 5.0}{train:false}Beñ, {train:true}ya ! Mat tre !
        {start: 5.0; end: 6.0}  {train:false} Netra netra netra {train:true}
        """
    
    data_lines = []
    parser = MetadataParser()
    parser.set_filter_out({"train": False})
    for line in ali_data.strip().split('\n'):
        data_lines.append(parser.parse_sentence(line))

    assert data_lines[2][1] == (1.0, 4.0)
    assert data_lines[2][0][0]["text"] == "Demat bed holl !"
    assert data_lines[2][0][0]["speaker"] == "george_m."
    assert data_lines[2][0][0]["accent"] == "leoneg"

    assert len(data_lines[3][0]) == 1
    assert data_lines[3][0][0]["text"] == "ya ! Mat tre !"

    assert "text" not in data_lines[4][0][0]