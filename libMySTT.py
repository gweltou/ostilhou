#! /usr/bin/env python3
# -*- coding: utf-8 -*-


"""
 Common functions for audio file playback and data parsing
 
 Author:  Gweltaz Duval-Guennoc
"""


from typing import Tuple
import os
import json
import re
from pydub import AudioSegment
#from pydub.playback import play
from pydub.utils import get_player_name
from tempfile import NamedTemporaryFile
import subprocess
import hunspell # https://www.systutorials.com/docs/linux/man/4-hunspell/
from colorama import Fore

# For eaf (Elan) file conversion
from xml.dom import minidom
import datetime, pytz

from ostilhou.asr import (
    sentence_post_process,
    lexicon_sub,
    verbal_fillers,
    acr2f,
    phonemes,
    load_text_data
)
from ostilhou.dicts import proper_nouns, acronyms
from ostilhou.text.tokenizer import is_word_inclusive, match_word_inclusive



ROOT = os.path.dirname(os.path.abspath(__file__))

HS_DIC_PATH = os.path.join(ROOT, "ostilhou", "dicts", os.path.join("hunspell-dictionary", "br_FR"))
HS_AFF_PATH = os.path.join(ROOT, "ostilhou", "dicts", os.path.join("hunspell-dictionary", "br_FR.aff"))
HS_ADD_PATH= os.path.join(ROOT, "ostilhou", "dicts", os.path.join("hunspell-dictionary", "add.txt"))

CORRECTED_PATH = os.path.join(ROOT, "corrected.txt")
JOINED_PATH = os.path.join(ROOT, "joined.txt")
ACRONYM_PATH = os.path.join(ROOT, "acronyms.txt")



punctuation = ',.;?!:«»"”“()…–—‚{}[]'

valid_chars = "aâàbcdeêfghijklmnñoprstuüùûvwyz'- "



def get_hunspell_dict():
    #hs = hunspell.HunSpell(HS_DIC_PATH+".dic", HS_AFF_PATH)
    hs = hunspell.Hunspell(HS_DIC_PATH) # for cyhunspell
    with open(HS_ADD_PATH, 'r') as f:
        for w in f.readlines():
            hs.add(w.strip())
    for w in verbal_fillers:
        hs.add(w)
    for w in lexicon_sub.keys():
        hs.add(w)
    return hs

hs_dict = get_hunspell_dict()



def get_corrected_dict():
    corrected = dict()
    corrected_sentences = dict()
    corrected_sentences["&ltbr&gt"] = "" # Special rule for sentences coming from wikipedia
    
    with open(CORRECTED_PATH, 'r') as f:
        for l in f.readlines():
            #l = l.strip()
            if not l.strip() or l.startswith('#'):
                continue
            k, v = l.replace('\n', '').split('\t')
            v = v.replace('-', ' ')
            #k = k.lower()
            if ' ' in k:
                corrected_sentences[k] = v
            else:
                corrected[k] = v
    return corrected, corrected_sentences

corrected, corrected_sentences = get_corrected_dict()




# def get_acronyms_dict():
#     """
#         Acronyms are stored in UPPERCASE in dictionary
#     """
#     acronyms = dict()
#     for l in "BCDFGHIJKLMPQRSTUVWXZ":
#         acronyms[l] = [acr2f[l]]
    
#     if os.path.exists(ACRONYM_PATH):
#         with open(ACRONYM_PATH, 'r') as f:
#             for l in f.readlines():
#                 if l.startswith('#') or not l: continue
#                 acr, *pron = l.split()
#                 if acr in acronyms:
#                     acronyms[acr].append(' '.join(pron))
#                 else:
#                     acronyms[acr] = [' '.join(pron)]
#     else:
#         print("Acronym dictionary not found... creating file")
#         open(ACRONYM_PATH, 'a').close()
#     return acronyms

# acronyms = get_acronyms_dict()





################################################################################
################################################################################
##
##                         TEXT PROCESSING FUNCTIONS
##
################################################################################
################################################################################



def filter_out(text, symbols):
    new_text = ""
    for l in text:
        if not l in symbols: new_text += l
    return new_text



def pre_process(sentence, keep_dash=False, keep_punct=False):
    """ Substitude parts of the sentence according to 'corrected_sentences' dictionary.
        Preserve letter case.
        Clean punctuation by default.
    """

    sentence = sentence.replace('‘', "'")
    sentence = sentence.replace('’', "'")
    sentence = sentence.replace('ʼ', "'")

    for mistake in corrected_sentences.keys():
        if mistake in sentence or mistake in sentence.lower():
             # Won't work if mistake is capitalized in original sentence
            sentence = sentence.replace(mistake, corrected_sentences[mistake])
    
    if not keep_punct:
        sentence = filter_out(sentence, punctuation)
    if not keep_dash:
        sentence = sentence.replace('-', ' ')   # Split words like "sav-heol"
    sentence = sentence.replace('/', ' ')
    sentence = sentence.replace('|', ' ')

    return sentence



def tokenize(sentence, post_proc=True, keep_dash=False, keep_punct=False):
    """ Return a list of token from a sentence (str)
        Preserve letter case
        The special character '*' will be kept
        
        Parameters
        ----------
            post_proc (Boolean):
                Apply corrections and capitalisation
            keep_dash (Boolean):
                Dashed words (like "sav-heol") won't be splitted
            keep_punct (Boolean):
                Keep punctuation
    """

    sentence = pre_process(sentence, keep_dash=keep_dash, keep_punct=keep_punct)

    tokens = []
    for t in sentence.split():
        if t.startswith("'"):
            tokens.append(t[1:])
        elif t.endswith("'"):
            tokens.append(t[:-1])
        else:
            tokens.append(t) 
    
    if post_proc:
        new_tokens = []
        for t in tokens:
            lowered = t.lower()
            if lowered in corrected:
                new_tokens.append(corrected[lowered])
            elif t in corrected:
                new_tokens.append(corrected[t])
            elif lowered in proper_nouns:
                new_tokens.append(t.capitalize())
            elif t in acronyms:
                new_tokens.append(t)
            else:
                new_tokens.append(lowered)
        tokens = new_tokens

    return list(filter(bool, tokens))



PARENTHESIS_PATTERN = re.compile(r"\([^\(]+\)")

def extract_parenthesis(sentence):
    """ Extract text between parenthesis
        TODO: refactor so it returns (sentence_wo_parenthesis, list_or_sentences_in_parenthesis)
    """
    in_parenthesis = []
    match = PARENTHESIS_PATTERN.search(sentence)
    while match:
        start, end = match.span()
        sentence = sentence[:start] + sentence[end:]
        in_parenthesis.append(match.group())
        match = PARENTHESIS_PATTERN.search(sentence)
        
    return [sentence] + in_parenthesis



def _split_line(s, splitter = '. '):
    length = len(splitter)
    if splitter in s:
        i = s.index(splitter)
        if len(s) > i + length and \
            i > length and \
            s[i-length] != ' ':          
            #(s[i+length].isupper() or not s[i+length].isalnum()) and \
                # Ignore last occurence
                # Next letter must be upper case
                # Ignore if at begining of sentence
                # Previous word must not be a single letter (to filter out acronyms)
                return [s[:i+length]] + _split_line(s[i+2:], splitter)
    return [s]



def split_line(sentence):
    """ Split line according to punctuation
        Put text between parenthesis at the end
        Keep punctuation
        Return a list of sentence
    """
    # sub = extract_parenthesis(sentence)
    sub = [sentence]
    splitters = ['. ', ': ', '! ', '? ', '; ']
    
    for splitter in splitters:
        new_sub = []
        for s in sub:
            new_sub.extend(_split_line(s, splitter))
        sub = new_sub
    
    # filter out sub-sentences shorter than 2 tokens
    return [s.strip() for s in sub if len(s.split()) > 1]
    #return sub



def get_cleaned_sentence(sentence, rm_bl=False, rm_verbal_ticks=False, keep_dash=False, keep_punct=False):
    """
        Return a cleaned and corrected sentence, proper to put in text files or corpus
        and a quality score (ratio of black-listed words, the lower the better)

        Parameters
        ----------
            rm_bl (Boolean):
                remove marked words
            rm_verbal_ticks (Boolean):
                remove verbal ticks
            keep_dash (Boolean):
                Dashed words (like "sav-heol") will be preserved
            keep_punct (Boolean):
                Keep punctuation
    """
    if not sentence:
        return '', 0
        
    tokens = []
    num_blacklisted = 0
    for token in tokenize(sentence, keep_dash=keep_dash, keep_punct=keep_punct):
        lowered_token = token.lower()
        # Skip black listed words
        if token.startswith('*'):
            if not rm_bl:
                tokens.append(token)
            num_blacklisted += 1
        elif rm_verbal_ticks and lowered_token in verbal_fillers:
            pass
        elif lowered_token in corrected:
            tokens.append(corrected[lowered_token])
        elif token in corrected:
            tokens.append(corrected[token])
        elif lowered_token in proper_nouns:
            tokens.append(token.capitalize())
        elif is_acronym(token):
            tokens.append(token)
            if not token in acronyms:
                num_blacklisted += 1
        else:
            tokens.append(lowered_token)
    if not tokens:
        return '', 1
    return ' '.join(tokens), float(num_blacklisted)/len(tokens)



def get_hspell_correction(sentence: str, allow_digits=True) -> Tuple[str, int]:
    """
        Return a string which is a colored correction of the sentence
        and the number of spelling mistakes in sentence (after correction)
    """
    
    sentence = sentence.strip()
    if not sentence:
        return '', 0
    
    num_errors = 0
    tokens = []
    for token in tokenize(sentence, post_proc=False):
        spell_error = False
        lowered_token = token.lower()
        # Ignore black listed words
        if token.startswith('*'):
            tokens.append(Fore.YELLOW + token + Fore.RESET)
        elif lowered_token in verbal_fillers:
            tokens.append(Fore.YELLOW + token + Fore.RESET)
        elif lowered_token in corrected:
            tokens.append(Fore.GREEN + corrected[lowered_token] + Fore.RESET)
        elif token in corrected:
            tokens.append(Fore.GREEN + corrected[token] + Fore.RESET)
        elif len(token) == 1 and token in "$€%":
            tokens.append(lowered_token)
        elif not allow_digits and token.isdigit():
            spell_error = True
            tokens.append(Fore.RED + token + Fore.RESET)
            
        # Check for hyphenated words
        
        elif is_acronym(token):
            if token in acronyms:
                tokens.append(Fore.BLUE + token + Fore.RESET)
            else:
                tokens.append(Fore.MAGENTA + token + Fore.RESET)
                spell_error = True
        elif lowered_token in proper_nouns:
            tokens.append(token.capitalize())
        elif is_word_inclusive(token):
            # Inclusive notation (ex: arvester·ez)
            # Check if the first part can be found in dictionary
            match = match_word_inclusive(token)
            if not hs_dict.spell(match.group(1)):
                spell_error = True
                tokens.append(Fore.RED + token + Fore.RESET)
            else:
                tokens.append(lowered_token)
        elif not hs_dict.spell(token):
            spell_error = True
            tokens.append(Fore.RED + token + Fore.RESET)
        else:
            tokens.append(lowered_token)
        
        # Maybe we should check in lexicon_sub as well...
        
        if spell_error:
            num_errors += 1
        
    return ' '.join(tokens), num_errors



def is_acronym(word):
    if len(word) == 1 and word in "BCDFGHIJKLPQRSTVXYZ":
        return True

    if len(word) < 2:
        return False
    
    valid = False
    for l in word:
        if l in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            valid = True
            continue
        if l not in "-0123456789":
            return False
    return valid



def prompt_acronym_phon(w, song, segments, idx):
    """
        w: Acronym
        i: segment number in audiofile (from 'split' file) 
    """
    
    guess = ' '.join([acr2f[l] for l in w if l in acr2f])
    print(f"Phonetic proposition for '{w}' : {guess}")
    while True:
        answer = input("Press 'y' to validate, 'l' to listen, 'x' to skip or write a different prononciation: ").strip().upper()
        if not answer:
            continue
        if answer == 'X':
            return None
        if answer == 'Y':
            return guess
        if answer == 'L':
            play_segment(idx, song, segments, 1.5)
            continue
        valid = True
        for phoneme in answer.split():
            if phoneme not in phonemes:
                print("Error : phoneme not in", ' '.join(phonemes))
                valid = False
        if valid :
            return answer



def extract_acronyms(text):
    extracted = set()
    for w in tokenize(text, post_proc=False):
        # Remove black-listed words (beggining with '*')
        if w.startswith('*'):
            continue
        if is_acronym(w):
            extracted.add(w)
    
    return list(extracted)



def extract_acronyms_from_file(text_filename):
    split_filename = text_filename[:-3] + 'split'
    segments = load_segments(split_filename)
    
    wav_filename = text_filename[:-3] + 'wav'
    song = AudioSegment.from_wav(wav_filename)
    
    extracted_acronyms = dict()
    
    with open(text_filename, 'r') as f:
        sentence_idx = 0
        for l in f.readlines():
            l = l.strip()
            if not l:
                continue
            if l.startswith('#'):
                continue
            
            l, _ = get_cleaned_sentence(l)
            
            # Remove metadata
            for match in METADATA_PATTERN.finditer(l):
                start, end = match.span()
                l = l[:start] + l[end:]
            
            l = l.strip()
            if not l:   # In case the speaker pattern is the only text on the line
                continue
            
            for acr in extract_acronyms(l):
                if not acr in acronyms and not acr in extracted_acronyms:
                    print(sentence_idx)
                    
                    phon = prompt_acronym_phon(acr, song, segments, sentence_idx)
                    if phon:
                        extracted_acronyms[acr] = phon
            sentence_idx += 1
    
    return extracted_acronyms




################################################################################
################################################################################
##
##          PYDUB AUDIO SEGMENT / SPLIT FILES MANIPULATION FUNCTIONS
##
################################################################################
################################################################################


def load_segments(split_filename):
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



def get_segment(i, song, segments):
    start = int(segments[i][0])
    stop = int(segments[i][1])
    seg = song[start: stop]
    return seg



def play_segment(i, song, segments, speed):
    play_with_ffplay(get_segment(i, song, segments), speed)



vosk_loaded = False

def load_vosk():
    from vosk import Model, KaldiRecognizer, SetLogLevel
    
    global recognizer
    global vosk_loaded

    SetLogLevel(-1)
    model = Model(os.path.normpath(os.path.join(ROOT, "../models/current")))
    recognizer = KaldiRecognizer(model, 16000)
    recognizer.SetWords(True)
    vosk_loaded = True



def transcribe_segment(segment):
    if not vosk_loaded:
        load_vosk()
    # seg = song[segments[idx][0]:segments[idx][1]]
    segment = segment.get_array_of_samples().tobytes()
    i = 0
    while i + 4000 < len(segment):
        recognizer.AcceptWaveform(segment[i:i+4000])
        i += 4000
    recognizer.AcceptWaveform(segment[i:])
    text = eval(recognizer.FinalResult())["text"]
    return sentence_post_process(text)


################################################################################
################################################################################
##
##                   AUDIO FILE MANIPULATION FUNCTIONS
##
################################################################################
################################################################################


def get_audiofile_info(filename):
    r = subprocess.check_output(['ffprobe', '-hide_banner', '-v', 'panic', '-show_streams', '-of', 'json', filename])
    r = json.loads(r)
    return r['streams'][0]



def get_audiofile_length(filename):
    """
        Get audio file length in seconds
    """
    return float(get_audiofile_info(filename)['duration'])


    
def play_with_ffplay(seg, speed=1.0):
    with NamedTemporaryFile("w+b", suffix=".wav") as f:
        seg.export(f.name, "wav")
        player = get_player_name()
        p = subprocess.Popen(
            [player, "-nodisp", "-autoexit", "-loglevel", "quiet", "-af", f"atempo={speed}", f.name],
        )
        print(p)
        p.wait()



def convert_to_wav(src, dst, verbose=True, keep_orig=True):
    """
        Convert to 16kHz mono pcm
        Validate filename

        Parameters
        ----------
            verbose (bool):
                Info text to stdout
            keep_orig (bool):
                keep  original file (or rename if src and dst are the same)
    """
    src = os.path.abspath(src)
    dst = os.path.abspath(dst)
    if src == dst:
        # Rename existing audio file
        rep, filename = os.path.split(src)
        basename, ext = os.path.splitext(filename)
        new_name = basename + "_orig" + ext
        new_src = os.path.join(rep, new_name)
        if verbose: print(f"AUDIO_CONV: renaming {filename} to {new_name}")
        os.rename(src, new_src)
        src = new_src

    if verbose:
        print(f"AUDIO_CONV: converting {src} to {dst}...")
    rep, filename = os.path.split(dst)
    dst = os.path.join(rep, filename)
    subprocess.call(['ffmpeg', '-v', 'panic',
                     '-i', src, '-acodec', 'pcm_s16le',
                     '-ac', '1', '-ar', '16000', dst])

    if not keep_orig:
        if verbose:
            print(f"AUDIO_CONV: Removing {src}")
        os.remove(src)


def convert_to_mp3(src, dst, verbose=True):
    """
        Convert to mp3
        Validate filename
    """
    if verbose:
        print(f"converting {src} to {dst}...")
    if os.path.abspath(src) == os.path.abspath(dst):
        print("ERROR: source and destination are the same, skipping")
        return -1
    rep, filename = os.path.split(dst)
    dst = os.path.join(rep, filename)
    subprocess.call(['ffmpeg', '-v', 'panic',
                     '-i', src,
                     '-ac', '1', dst])



def concatenate_audiofiles(file_list, out_filename, remove=False):
    """ Concatenate a list of audio files to a single audio file

        Parameters
        ----------
            remove (bool):
                remove original files
    """

    if len(file_list) <= 1:
        return
    
    file_list_filename = "audiofiles.txt"
    with open(file_list_filename, 'w') as f:
        f.write('\n'.join([f"file '{wav}'" for wav in file_list]))
    
    subprocess.call(['ffmpeg', '-v', 'panic',
                     '-f', 'concat',
                     '-safe', '0',
                     '-i', file_list_filename,
                     '-c', 'copy', out_filename])
    os.remove(file_list_filename)
    
    if remove:
        for fname in file_list:
            os.remove(fname)




################################################################################
################################################################################
##
##                        FILE MANIPULATION FUNCTIONS
##
################################################################################
################################################################################


def list_files_with_extension(ext, rep, recursive=True):
    file_list = []
    if os.path.isdir(rep):
        for filename in os.listdir(rep):
            filename = os.path.join(rep, filename)
            if os.path.isdir(filename) and recursive:
                file_list.extend(list_files_with_extension(ext, filename))
            elif os.path.splitext(filename)[1] == ext:
                file_list.append(filename)
    return file_list



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

    segments, _ = load_segments(split_filename)
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
