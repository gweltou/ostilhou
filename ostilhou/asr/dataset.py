from typing import Tuple, List, Dict
import os.path
import re
from hashlib import md5

# For eaf (Elan) file conversion
from xml.dom import minidom
import datetime, pytz

from colorama import Fore

from ..utils import read_file_drop_comments
from ..text import pre_process, normalize_sentence, filter_out_chars


header = "{source: }\n{source-audio: }\n{author: }\n{licence: }\n{tags: }\n\n\n\n\n\n"


Segment = Tuple[int, int]

def load_segments_data(segfile: str) -> Tuple[List[Segment], str]:
    """ Load audio segments delimiters from a `.seg` file
        Return a list of segments and a header string
    """

    segments = []
    with open(segfile, 'r') as f:
        for l in f.readlines():
            l = l.strip()
            if not l or l.startswith('#'):
                continue
            t = l.split()
            start = int(t[0])
            stop = int(t[1])
            segments.append((start, stop))
    
    return segments



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



def get_text_header(filename) -> Dict:
    #s=set()
    metadata = dict()
    for l in read_file_drop_comments(filename):
        l, md = extract_metadata(l)
        metadata.update(md)
        if l:
            # Stop a first sentence
            break
    return metadata



def parse_dataset(file_or_dir, args):
    if file_or_dir.endswith(".split") or file_or_dir.endswith(".seg"):   # Single data item
        return parse_data_file(file_or_dir, args)
    elif os.path.isdir(file_or_dir):
        data = {
            "path": file_or_dir,
            "wavscp": dict(),       # Wave filenames
            "utt2spk": [],      # Utterance to speakers
            "segments": [],     # Time segments
            "text": [],         # Utterances text
            "speakers": set(),  # Speakers names
            "lexicon": set(),   # Word dictionary
            "corpus": set(),    # Sentences for LM corpus
            "audio_length": {'m': 0, 'f': 0, 'u': 0},    # Audio length for each gender
            "subdir_audiolen": {}   # Size (total audio length) for every sub-folders
            }
        
        for filename in sorted(os.listdir(file_or_dir)):
            if filename.startswith('.'):
                # Skip hidden folders
                continue
            if os.path.isdir(os.path.join(file_or_dir, filename)) \
                    or filename.endswith(".split") \
                    or filename.endswith(".seg"):
                data_item = parse_dataset(os.path.join(file_or_dir, filename), args)
                data["wavscp"].update(data_item["wavscp"])
                data["utt2spk"].extend(data_item["utt2spk"])
                data["segments"].extend(data_item["segments"])
                data["text"].extend(data_item["text"])
                data["speakers"].update(data_item["speakers"])
                data["lexicon"].update(data_item["lexicon"])
                data["corpus"].update(data_item["corpus"])
                data["audio_length"]['f'] += data_item["audio_length"]['f']
                data["audio_length"]['m'] += data_item["audio_length"]['m']
                data["audio_length"]['u'] += data_item["audio_length"]['u']
                data["subdir_audiolen"][filename] = \
                    data_item["audio_length"]['f'] + \
                    data_item["audio_length"]['m'] + \
                    data_item["audio_length"]['u']
        
        return data
    else:
        print("File argument must be a split file or a directory")
        return
    


speakers_gender = {"unknown": "u"}

def parse_data_file(split_filename, args):
    # Kaldi doensn't like whitespaces in file path
    if ' ' in split_filename:
        raise "ERROR: whitespaces in path " + split_filename
    
    # basename = os.path.basename(split_filename).split(os.path.extsep)[0]
    # print(Fore.GREEN + f" * {split_filename[:-6]}" + Fore.RESET)
    text_filename = split_filename.replace('.split', '.txt')
    assert os.path.exists(text_filename), f"ERROR: no text file found for {split_filename}"
    wav_filename = os.path.abspath(split_filename.replace('.split', '.wav'))
    assert os.path.exists(wav_filename), f"ERROR: no wave file found for {split_filename}"
    recording_id = md5(wav_filename.encode("utf8")).hexdigest()
    
    substitute_corpus_filename = split_filename.replace('.split', '.cor')
    replace_corpus = os.path.exists(substitute_corpus_filename)
    
    data = {
        "wavscp": {recording_id: wav_filename},   # Wave filenames
        "utt2spk": [],      # Utterance to speakers
        "segments": [],     # Time segments
        "text": [],         # Utterances text
        "speakers": set(),  # Speakers names
        "lexicon": set(),   # Word dictionary
        "corpus": set(),    # Sentences for LM corpus
        "audio_length": {'m': 0, 'f': 0, 'u': 0},    # Audio length for each gender
        }
    
    ## PARSE TEXT FILE
    speaker_ids = []
    speaker_id = "unknown"
    sentences = []

    for sentence, metadata in load_text_data(text_filename):
        add_to_corpus = True
        if "parser" in metadata:
            if "no-lm" in metadata["parser"]:
                add_to_corpus = False
            elif "add-lm" in metadata["parser"]:
                add_to_corpus = True
            
        if "speaker" in metadata:
            speaker_id = metadata["speaker"]
            data["speakers"].add(speaker_id)
        
        if "gender" in metadata and speaker_id != "unknown":
            if speaker_id not in speakers_gender:
                # speakers_gender is a global variable
                speakers_gender[speaker_id] = metadata["gender"]
        
        cleaned = pre_process(sentence)
        if cleaned:
            sent = normalize_sentence(cleaned, autocorrect=True)
            sent = sent.replace('-', ' ').replace('/', ' ')
            sent = sent.replace('\xa0', ' ')
            sent = filter_out_chars(sent, PUNCTUATION)
            sentences.append(' '.join(sent.replace('*', '').split()))
            speaker_ids.append(speaker_id)
            
            # Add words to lexicon
            for word in sent.split():
                # Remove black-listed words (those beggining with '*')
                if word.startswith('*'):
                    pass
                elif word in ("<NTT>", "<C'HOARZH>", "<UNK>", "<HUM>", "<PASSAAT>"):
                    pass
                elif word == "'":
                    pass
                # elif word in verbal_fillers:
                #     pass
                # elif is_acronym(word):
                #     pass
                # elif word.lower() in proper_nouns:
                #     pass
                else: data["lexicon"].add(word)
        
        # Add sentence to language model corpus
        if add_to_corpus and not replace_corpus and not args.no_lm:
            for sub in split_sentences(cleaned, end=''):
                sent = normalize_sentence(sub, autocorrect=True)
                sent = sent.replace('-', ' ').replace('/', ' ')
                sent = sent.replace('\xa0', ' ')
                sent = filter_out_chars(sent, PUNCTUATION)
                if not sent:
                    continue

                n_stared = sent.count('*')
                tokens = sent.split()
                # Ignore if to many black-listed words in sentence
                if n_stared / len(tokens) > 0.2:
                    if args.verbose:
                        print(Fore.YELLOW + "LM exclude:" + Fore.RESET, sent)
                    continue
                # Remove starred words
                tokens = [tok for tok in tokens if not tok.startswith('*')]
                # Ignore if sentence is too short
                if len(tokens) < LM_SENTENCE_MIN_WORDS:
                    if args.verbose:
                        print(Fore.YELLOW + "LM exclude:" + Fore.RESET, sent)
                    continue
                data["corpus"].add(' '.join(tokens))
    
    if replace_corpus and not args.no_lm:
        for sentence, _ in load_text_data(substitute_corpus_filename):
            for sub in split_sentences(sentence):
                sub = pre_process(sub)
                sub = normalize_sentence(sub, autocorrect=True)
                sub = sub.replace('-', ' ').replace('/', ' ')
                sub = sub.replace('\xa0', ' ')
                sub = filter_out_chars(sub, PUNCTUATION)
                data["corpus"].add(' '.join(sub.split()))
    

    ## PARSE SPLIT FILE
    segments, _ = load_segments_data(split_filename)
    assert len(sentences) == len(segments), \
        f"number of utterances in text file ({len(data['text'])}) doesn't match number of segments in split file ({len(segments)})"

    for i, s in enumerate(segments):
        start = s[0] / 1000
        stop = s[1] / 1000
        if stop - start < UTTERANCES_MIN_LENGTH:
            # Skip short utterances
            continue

        if speaker_ids[i] in speakers_gender:
            speaker_gender = speakers_gender[speaker_ids[i]]
        else:
            print(Fore.RED + "unknown gender:" + Fore.RESET, speaker_ids[i])
            speaker_gender = 'u'
        
        if speaker_gender == 'm':
            data["audio_length"]['m'] += stop - start
        elif speaker_gender == 'f':
            data["audio_length"]['f'] += stop - start
        else:
            data["audio_length"]['u'] += stop - start
        
        utterance_id = f"{speaker_ids[i]}-{recording_id}-{floor(100*start):0>7}_{ceil(100*stop):0>7}"
        data["text"].append((utterance_id, sentences[i]))
        data["segments"].append(f"{utterance_id}\t{recording_id}\t{floor(start*100)/100}\t{ceil(stop*100)/100}\n")
        data["utt2spk"].append(f"{utterance_id}\t{speaker_ids[i]}\n")
    
    status = Fore.GREEN + f" * {split_filename[:-6]}" + Fore.RESET
    if data["audio_length"]['u'] > 0:
        status += '\t' + Fore.RED + "unknown speaker(s)" + Fore.RESET
    print(status)
    return data




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
                        if key in ("tags", "author", "accent"):
                            val = [v.strip().replace(' ', '_') for v in val.split(',') if v.strip()]
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