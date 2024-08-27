from typing import Tuple, List, Dict
import os.path
import re
from math import floor, ceil

from hashlib import md5
from uuid import uuid4
from colorama import Fore

from ..utils import read_file_drop_comments
from ..text import (
    pre_process, normalize_sentence, filter_out_chars,
    split_sentences,
    PUNCTUATION
)


datafile_header = \
"""{source: }
{source-audio: }
{audio-path: }
{author: }
{licence: }
{tags: }\n\n\n\n\n
"""


# Special tokens, found in transcriptions
special_tokens = {
    "<UNK>": "SPN",
    "<SPOKEN_NOISE>": "SPN",
    "<NTT>": "SPN",
    "<C'HOARZH>": "LAU",
    "<HUM>": "SPN",
    "<PASAAT>": "SPN",
    "<SONEREZH>": "NSN",
    "<PAS>": "SPN",
    "<FRONAL>": "SPN",
}



Segment = Tuple[int, int]

def load_segments_data(segfile: str) -> List[Segment]:
    """ Load audio segments delimiters from a `.seg` file
        Return a list of segments
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
    """ 
        Return list of sentences with metadata.
        Metadata dictionaries will always have, at least, the "speaker" and "gender" keys.

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
    metadata = dict()
    for l in read_file_drop_comments(filename):
        l, md = extract_metadata(l)
        metadata.update(md)
        if l:
            # Stop a first sentence
            break
    return metadata


def load_ali_file(filepath) -> Dict:
    """returns a dictionary containing a list of sentences and a list of segments"""
    audio_path = None
    sentences = []
    raw_sentences = []
    segments = []
    metadatas = []

    with open(filepath, 'r') as f:
        # Find associated audio file in metadata
        current_speaker = 'unknown'
        current_gender = 'unknown'
        no_lm = False

        for line in f.readlines():
            text, metadata = extract_metadata(line)
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

            # match = re.search(r"{\s*start\s*:\s*([0-9\.]+)\s*;\s*end\s*:\s*([0-9\.]+)\s*}", line)
            # if match:
            if "start" in metadata and "end" in metadata:
                segments.append([metadata["start"]*1000, metadata["end"]*1000])
                sentences.append(text.strip())
                raw_sentences.append(line.strip())
                metadatas.append(metadata)

            if not audio_path and "audio-path" in metadata:
                dir = os.path.split(filepath)[0]
                audio_path = os.path.join(dir, metadata["audio-path"])
                audio_path = os.path.normpath(audio_path)
    
    return {
        "audio_path": audio_path,
        "sentences": sentences,
        "raw_sentences": raw_sentences,
        "segments": segments,
        "metadata": metadatas,
    }



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
                item_data = parse_dataset(os.path.join(file_or_dir, filename), args)
                data["wavscp"].update(item_data["wavscp"])
                data["utt2spk"].extend(item_data["utt2spk"])
                data["segments"].extend(item_data["segments"])
                data["text"].extend(item_data["text"])
                data["speakers"].update(item_data["speakers"])
                data["lexicon"].update(item_data["lexicon"])
                data["corpus"].update(item_data["corpus"])
                data["subdir_audiolen"][filename] = \
                    item_data["audio_length"]['f'] + \
                    item_data["audio_length"]['m'] + \
                    item_data["audio_length"]['u']
                for k, dur in item_data["audio_length"].items():
                    if k in data["audio_length"]:
                        data["audio_length"][k] += dur
                    else:
                        data["audio_length"][k] = dur

        return data
    else:
        print("File argument must be a split file or a directory")
        return
    


speakers_gender = {"unknown": 'u'}

def parse_data_file(seg_filename, args):
    # Kaldi doesn't like whitespaces in file path
    if ' ' in seg_filename:
        raise "ERROR: whitespaces in path " + seg_filename
    
    # basename = os.path.basename(split_filename).split(os.path.extsep)[0]
    # print(Fore.GREEN + f" * {split_filename[:-6]}" + Fore.RESET)
    seg_ext = os.path.splitext(seg_filename)[1] # Could be '.split' or '.seg'
    text_filename = seg_filename.replace(seg_ext, '.txt')
    assert os.path.exists(text_filename), f"ERROR: no text file found for {seg_filename}"
    audio_filename = os.path.abspath(seg_filename.replace(seg_ext, '.wav'))
    if not os.path.exists(audio_filename):
        audio_filename = os.path.abspath(seg_filename.replace(seg_ext, '.mp3'))
    assert os.path.exists(audio_filename), f"ERROR: no wave file found for {seg_filename}"
    recording_id = md5(audio_filename.encode("utf8")).hexdigest()
    
    substitute_corpus_filename = seg_filename.replace(seg_ext, '.cor')
    replace_corpus = os.path.exists(substitute_corpus_filename)
    
    data = {
        "wavscp": {recording_id: audio_filename},   # Wave filenames
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
    sentences = []

    # Use a single random speaker id per file for unknown speakers
    file_speaker_id = str(uuid4()).replace('-', '')

    for sentence, metadata in load_text_data(text_filename):
        add_to_corpus = True
        if "parser" in metadata:
            if "no-lm" in metadata["parser"]:
                add_to_corpus = False
            elif "add-lm" in metadata["parser"]:
                add_to_corpus = True
            
        speaker_id = metadata["speaker"]
        if speaker_id == "unknown":
            if args.hash_id:
                #speaker_id = str(uuid4()).replace('-', '')
                speaker_id = file_speaker_id
        else:
            if args.hash_id:
                speaker_id = md5(speaker_id.encode('utf-8')).hexdigest()
            data["speakers"].add(speaker_id)
        
        if speaker_id not in speakers_gender:
            # speakers_gender is a global variable
            speakers_gender[speaker_id] = metadata["gender"]
        
        cleaned = pre_process(sentence)
        if cleaned:
            sent = normalize_sentence(cleaned, autocorrect=True, norm_case=True)
            sent = sent.replace('-', ' ').replace('/', ' ')
            sent = sent.replace('\xa0', ' ') # Non-breakable spaces
            sent = filter_out_chars(sent, PUNCTUATION)
            sentences.append(' '.join(sent.replace('*', '').split()))
            speaker_ids.append(speaker_id)
            
            # Add words to lexicon
            for word in sent.split():
                # Remove black-listed words (those beggining with '*')
                if word.startswith('*'):
                    pass
                elif word in special_tokens:
                    pass
                elif word == "'":
                    pass
                else: data["lexicon"].add(word)
        
        # Add sentence to language model corpus
        if add_to_corpus and not replace_corpus and not args.no_lm:
            for sub in split_sentences(cleaned, end=''):
                sent = normalize_sentence(sub, autocorrect=True, norm_case=True)
                sent = sent.replace('-', ' ').replace('/', ' ')
                sent = sent.replace('\xa0', ' ')
                sent = filter_out_chars(sent, PUNCTUATION)
                if not sent.strip():
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
                if len(tokens) < args.lm_min_token:
                    if args.verbose:
                        print(Fore.YELLOW + "LM exclude:" + Fore.RESET, sent)
                    continue
                data["corpus"].add(' '.join(tokens))
    
    if replace_corpus and not args.no_lm:
        for sentence, _ in load_text_data(substitute_corpus_filename):
            for sub in split_sentences(sentence):
                sub = pre_process(sub)
                sub = normalize_sentence(sub, autocorrect=True, norm_case=True)
                sub = sub.replace('-', ' ').replace('/', ' ')
                sub = sub.replace('\xa0', ' ')
                sub = filter_out_chars(sub, PUNCTUATION)
                data["corpus"].add(' '.join(sub.split()))
    

    ## PARSE SPLIT FILE
    segments = load_segments_data(seg_filename)
    assert len(sentences) == len(segments), \
        f"number of utterances in text file ({len(data['text'])}) doesn't match number of segments in split file ({len(segments)})"

    for i, s in enumerate(segments):
        start = s[0] / 1000
        end = s[1] / 1000
        if end - start < args.utt_min_len:
            # Skip short utterances
            continue

        speaker_gender = speakers_gender[speaker_ids[i]]
        # if speaker_gender not in ('f', 'm'):
        #     print(Fore.YELLOW + "unknown gender:" + Fore.RESET, speaker_ids[i])
        
        if speaker_gender == 'm':
            data["audio_length"]['m'] += end - start
        elif speaker_gender == 'f':
            data["audio_length"]['f'] += end - start
        else:
            data["audio_length"]['u'] += end - start
        
        utterance_id = f"{speaker_ids[i]}-{recording_id}-{floor(100*start):0>7}_{ceil(100*end):0>7}"
        data["text"].append((utterance_id, sentences[i]))
        data["segments"].append(f"{utterance_id}\t{recording_id}\t{floor(start*100)/100}\t{ceil(end*100)/100}\n")
        data["utt2spk"].append(f"{utterance_id}\t{speaker_ids[i]}\n")
    
    status = Fore.GREEN + f" * {seg_filename[:-6]}" + Fore.RESET
    if data["audio_length"]['u'] > 0:
        status += '\t' + Fore.RED + "unknown speaker(s)" + Fore.RESET
    print(status)
    return data




##############################  METADATA  ##############################

METADATA_PATTERN = re.compile(r'{\s*(.+?)\s*}')
METADATA_UNIT_PATTERN = re.compile(r"\s*([\w\s:,_'’/.-]+)\s*")
SPEAKER_NAME_PATTERN = re.compile(r"(?:(?:spk|speaker)\s*:\s*)?([\w '_-]+?)")
SPEAKER_ID_PATTERN_DEPR = re.compile(r'([-\'\w]+):*([mf])*')
KEYVAL_PATTERN = re.compile(r"([\w_'-]+)\s*:\s*([\w ,_'’.:/-]+?)\s*")

_VALID_PARAMS = {
    "source",
    "source-audio", "audio-source",
    "audio-path",
    "tags",
    "parser",
    "author", "authors",
    "licence",
    "speaker", "spk",
    "gender",
    "accent",
    "modifications",
    "transcription",
    "start", "end",
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
                spk_match = SPEAKER_NAME_PATTERN.fullmatch(unit.group(1))
                if spk_match:
                    speaker_name = spk_match.group(1)
                    # Keep all-caps names (Acronyms)
                    if not speaker_name.isupper():
                        speaker_name = speaker_name.replace(' ', '_').lower()
                    metadata["speaker"] = speaker_name
                    continue
                
                key_val = KEYVAL_PATTERN.fullmatch(unit.group(1))
                if key_val:
                    key, val = key_val.group(1), key_val.group(2)

                    if key in _VALID_PARAMS:
                        if key in ("tags", "author", "accent"):
                            val = [v.strip().replace(' ', '_') for v in val.split(',') if v.strip()]
                        if key in ("start", "end"):
                            val = float(val)
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
