from typing import Tuple, List, Dict
import os.path
import re

# For eaf (Elan) file conversion
from xml.dom import minidom
import datetime, pytz

from colorama import Fore

from ..utils import read_file_drop_comments



Segment = Tuple[int, int]

def load_segments_data(split_filename: str) -> Tuple[List[Segment], str]:
    """ Load audio segments delimiters from a `.split` file
        Return a list of segments and a header string
    """

    segments = []
    header = ""
    first = True
    with open(split_filename, 'r') as f:
        for l in f.readlines():
            l = l.strip()
            if l:
                if first and l.startswith('#'):
                    header = l
                else:
                    t = l.split()
                    start = int(t[0])
                    stop = int(t[1])
                    segments.append((start, stop))
                first = False
    
    return segments, header



def load_text_data(filename) -> List[Tuple[str, Dict]]:
    """ return list of sentences with metadata

        Return
        ------
            list of tuple (text sentences, metadata)
    """
    utterances = []
    current_speaker = 'unknown'
    current_gender = 'unknown'
    no_lm = False
    for l in read_file_drop_comments(filename):
        # Extract speaker id and other metadata
        l, metadata = extract_metadata(l)
        if "speaker" in metadata:
            current_speaker = metadata["speaker"]
        else:
            metadata["speaker"] = current_speaker
        
        if "gender" in metadata:
            current_gender = metadata["gender"]
        else:
            metadata["gender"] = current_gender
        
        if "parser" in metadata:
            if "no-lm" in metadata["parser"]: no_lm = True
            elif "add-lm" in metadata["parser"]: no_lm = False
        else:
            if no_lm:
                metadata["parser"] = ["no-lm"]
        if l:
            utterances.append((l, metadata))
    return utterances



def splitToEafFile(split_filename, type="wav"):
    """ Convert wav + txt + split files to a eaf (Elan) file """

    record_id = os.path.abspath(split_filename).split(os.path.extsep)[0]
    print(f"{split_filename=}{record_id=}")
    audio_filename = os.path.extsep.join((record_id, 'wav'))
    if type == "mp3":
        mp3_file = os.path.extsep.join((record_id, 'mp3'))
        if not os.path.exists(mp3_file):
            convert_to_mp3(audio_filename, mp3_file)
        audio_filename = mp3_file

    text_filename = os.path.extsep.join((record_id, 'txt'))
    eaf_filename = os.path.extsep.join((record_id, 'eaf'))

    segments, _ = load_segments_data(split_filename)
    utterances = load_text_data(text_filename)

    doc = minidom.Document()

    root = doc.createElement('ANNOTATION_DOCUMENT')
    root.setAttribute('AUTHOR', 'split2eaf (Gweltaz DG)')
    root.setAttribute('DATE', datetime.datetime.now(pytz.timezone('Europe/Paris')).isoformat(timespec='seconds'))
    root.setAttribute('FORMAT', '3.0')
    root.setAttribute('VERSION', '3.0')
    root.setAttribute('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
    root.setAttribute('xsi:noNamespaceSchemaLocation', 'http://www.mpi.nl/tools/elan/EAFv3.0.xsd')
    doc.appendChild(root)

    header = doc.createElement('HEADER')
    header.setAttribute('MEDIA_FILE', '')
    header.setAttribute('TIME_UNITS', 'milliseconds')
    root.appendChild(header)

    media_descriptor = doc.createElement('MEDIA_DESCRIPTOR')
    media_descriptor.setAttribute('MEDIA_URL', 'file://' + os.path.abspath(audio_filename))
    if type == "mp3":
        media_descriptor.setAttribute('MIME_TYPE', 'audio/mpeg')
    else:
        media_descriptor.setAttribute('MIME_TYPE', 'audio/x-wav')
    media_descriptor.setAttribute('RELATIVE_MEDIA_URL', './' + os.path.basename(audio_filename))
    header.appendChild(media_descriptor)

    time_order = doc.createElement('TIME_ORDER')
    for i, (s, e) in enumerate(segments):
        time_slot = doc.createElement('TIME_SLOT')
        time_slot.setAttribute('TIME_SLOT_ID', f'ts{2*i+1}')
        time_slot.setAttribute('TIME_VALUE', str(s))
        time_order.appendChild(time_slot)
        time_slot = doc.createElement('TIME_SLOT')
        time_slot.setAttribute('TIME_SLOT_ID', f'ts{2*i+2}')
        time_slot.setAttribute('TIME_VALUE', str(e))
        time_order.appendChild(time_slot)
    root.appendChild(time_order)

    tier_trans = doc.createElement('TIER')
    tier_trans.setAttribute('LINGUISTIC_TYPE_REF', 'transcript')
    tier_trans.setAttribute('TIER_ID', 'Transcription')

    for i, (sentence, _) in enumerate(utterances):
        annotation = doc.createElement('ANNOTATION')
        alignable_annotation = doc.createElement('ALIGNABLE_ANNOTATION')
        alignable_annotation.setAttribute('ANNOTATION_ID', f'a{i+1}')
        alignable_annotation.setAttribute('TIME_SLOT_REF1', f'ts{2*i+1}')
        alignable_annotation.setAttribute('TIME_SLOT_REF2', f'ts{2*i+2}')
        annotation_value = doc.createElement('ANNOTATION_VALUE')
        #text = doc.createTextNode(get_cleaned_sentence(sentence, rm_bl=True, keep_dash=True, keep_punct=True)[0])
        text = doc.createTextNode(sentence.replace('*', ''))
        annotation_value.appendChild(text)
        alignable_annotation.appendChild(annotation_value)
        annotation.appendChild(alignable_annotation)
        tier_trans.appendChild(annotation)
    root.appendChild(tier_trans)

    linguistic_type = doc.createElement('LINGUISTIC_TYPE')
    linguistic_type.setAttribute('GRAPHIC_REFERENCES', 'false')
    linguistic_type.setAttribute('LINGUISTIC_TYPE_ID', 'transcript')
    linguistic_type.setAttribute('TIME_ALIGNABLE', 'true')
    root.appendChild(linguistic_type)

    language = doc.createElement('LANGUAGE')
    language.setAttribute("LANG_ID", "bre")
    language.setAttribute("LANG_LABEL", "Breton (bre)")
    root.appendChild(language)

    constraint_list = [
        ("Time_Subdivision", "Time subdivision of parent annotation's time interval, no time gaps allowed within this interval"),
        ("Symbolic_Subdivision", "Symbolic subdivision of a parent annotation. Annotations refering to the same parent are ordered"),
        ("Symbolic_Association", "1-1 association with a parent annotation"),
        ("Included_In", "Time alignable annotations within the parent annotation's time interval, gaps are allowed")
    ]
    for stereotype, description in constraint_list:
        constraint = doc.createElement('CONSTRAINT')
        constraint.setAttribute('DESCRIPTION', description)
        constraint.setAttribute('STEREOTYPE', stereotype)
        root.appendChild(constraint)

    xml_str = doc.toprettyxml(indent ="\t", encoding="UTF-8")

    with open(eaf_filename, "w") as f:
        f.write(xml_str.decode("utf-8"))



def eafToSplitFile(eaf_filename):
    """ Write a split file and a text file from an eaf file """
    
    abs_path = os.path.abspath(eaf_filename)
    rep, eaf_filename = os.path.split(abs_path)
    
    print(rep, eaf_filename)
    print(abs_path)
    doc = minidom.parse(abs_path)
    root = doc.firstChild

    segments = []

    def getText(nodelist):
        rc = []
        for node in nodelist:
            if node.nodeType == node.TEXT_NODE:
                rc.append(node.data)
        return ''.join(rc)

    header = root.getElementsByTagName("HEADER")[0]
    md = header.getElementsByTagName("MEDIA_DESCRIPTOR")[0]
    wav_rel_path = md.getAttribute("RELATIVE_MEDIA_URL")

    wav_filename = os.path.normpath(os.path.join(rep, wav_rel_path))
    record_id = wav_filename.split(os.path.extsep)[0]
    text_filename = os.path.extsep.join((record_id, 'txt'))
    split_filename = os.path.extsep.join((record_id, 'split'))
    
    if os.path.exists(split_filename):
        print("Split file already exists.")
        while True:
            r = input("Replace (y/n)? ")
            if r.startswith('n'):
                print("Aborting...")
                return
            elif r.startswith('y'):
                break
    if not os.path.exists(wav_filename):
        print(f"Couldn't find '{wav_filename}'. Aborting...")
        return

    print("rep", rep)
    print("path", text_filename)

    time_order = root.getElementsByTagName("TIME_ORDER")[0]
    time_slots = time_order.getElementsByTagName("TIME_SLOT")
    time_slot_dict = {}
    for ts in time_slots:
        time_slot_dict[ts.getAttribute("TIME_SLOT_ID")] = int(ts.getAttribute("TIME_VALUE"))

    tiers = root.getElementsByTagName("TIER")
    for tier in tiers:
        if tier.getAttribute("TIER_ID").lower() in ("transcription", "default") :
            annotations = tier.getElementsByTagName("ANNOTATION")
            for annotation in annotations:
                aa = annotation.getElementsByTagName("ALIGNABLE_ANNOTATION")[0]
                ts1 = aa.getAttribute("TIME_SLOT_REF1")
                ts2 = aa.getAttribute("TIME_SLOT_REF2")
                time_seg = (time_slot_dict[ts1], time_slot_dict[ts2])
                text = getText(aa.getElementsByTagName("ANNOTATION_VALUE")[0].childNodes)
                segments.append((time_seg, text))
                #print(f"SEG: {time_seg} {text}")

    with open(text_filename, 'w') as f:
        f.write('#\n' * 4 + '\n' * 6)
        for _, sentence in segments:
            f.write(sentence + '\n')
    with open(split_filename, 'w') as f:
        for (s, e), _ in segments:
            f.write(f"{s} {e}\n")




##############################  METADATA  ##############################

METADATA_PATTERN = re.compile(r'{\s*(.+?)\s*}')
METADATA_UNIT_PATTERN = re.compile(r"\s*([\w\s:,_'/.-]+)\s*")
SPEAKER_NAME_PATTERN = re.compile(r"(?:spk\s*:\s*)?([\w '_-]+?)")
SPEAKER_ID_PATTERN_DEPR = re.compile(r'([-\'\w]+):*([mf])*')
KEYVAL_PATTERN = re.compile(r"([\w_'-]+)\s*:\s*([\w ,_'.:/-]+?)\s*")

_VALID_PARAMS = {
    "source", "source-audio",
    "tags",
    "parser",
    "author",
    "licence",
    "speaker", "spk",
    "gender",
    "accent",
#    "phon",
}


def extract_metadata(sentence: str) -> Tuple[str, dict]:
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
                    metadata["speaker"] = speaker_name.group(1).replace(' ', '_').lower()
                    continue
                
                key_val = KEYVAL_PATTERN.fullmatch(unit.group(1))
                if key_val:
                    key, val = key_val.group(1), key_val.group(2)

                    if key in _VALID_PARAMS:
                        if ',' in val:
                            val = [v.strip().replace(' ', '_') for v in val.split(',') if v.strip()]
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
                            print(Fore.RED + f"Wrong metadata: {unit.group(0)}" + Fore.RESET)

        sentence = sentence[:start] + sentence[end:]
        match = METADATA_PATTERN.search(sentence)
    
    return sentence.strip(), metadata
