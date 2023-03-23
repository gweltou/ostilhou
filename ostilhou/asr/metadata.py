import re


METADATA_PATTERN = re.compile(r'{\s*(.+?)\s*}')
METADATA_UNIT_PATTERN = re.compile(r"\s*([\w\s:,_'-]+)\s*")
SPEAKER_NAME_PATTERN = re.compile(r"(?:spk\s*:\s*)?([\w '_-]+?)")
SPEAKER_ID_PATTERN_DEPR = re.compile(r'([-\'\w]+):*([mf])*')
KEYVAL_PATTERN = re.compile(r"([\w_'-]+)\s*:\s*([\w ,_'-]+?)\s*")

_VALID_PARAMS = {
    "speaker", "spk",
    "gender",
    "accent",
    "phon",
    "author",
    "parser",
}


def extract_metadata(sentence: str):
    """ Returns the sentence stripped of its metadata (if any)
        and a dictionary of metadata
        Keeps unknown word marker '{?}'
    """
    metadata = dict()

    match = METADATA_PATTERN.search(sentence)
    while match:
        start, end = match.span()
        if match.group(1) == '?':       # Unknown words {?}
            if "unknown" not in metadata: metadata["unknown"] = []
            sub = sentence[:end]
            metadata["unknown"].append(len(sub.split())-1)
        else:
            for unit in METADATA_UNIT_PATTERN.finditer(match.group(1)):
                speaker_name = SPEAKER_NAME_PATTERN.fullmatch(unit.group(1))
                if speaker_name:
                    metadata["speaker"] = speaker_name.group(1)
                    continue
                
                key_val = KEYVAL_PATTERN.fullmatch(unit.group(1))
                if key_val:
                    key, val = key_val.group(1), key_val.group(2)

                    if key in _VALID_PARAMS:
                        if ',' in val:
                            val = [v.strip() for v in val.split(',') if v.strip()]
                            if len(val) == 1:
                                val = val[0]
                        metadata[key_val.group(1)] = val

                    else:
                        speaker_name_depr = SPEAKER_ID_PATTERN_DEPR.fullmatch(unit.group(1))
                        if speaker_name_depr:
                            metadata["speaker"] = speaker_name_depr.group(1)
                            if speaker_name_depr.group(2) in 'fm':
                                metadata["gender"] = speaker_name_depr.group(2)
                            continue    
                        else:
                            print(f"Wrong metadata: {unit.group(0)}")

        sentence = sentence[:start] + sentence[end:]
        match = METADATA_PATTERN.search(sentence)
    
    return sentence.strip(), metadata
