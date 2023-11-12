# Ostilhoù

A lightweight Python NLP toolkit for the breton language.

## Setup

```sh
pip install -r requirements.txt
```

## Working with text

Sentence splitting, tokenizer, text normalization, text inverse-normalization

Spelling error detection with An Drouizig's hunspell dictionary.

## Word dictionaries

Proper nouns, nouns with gender, acronyms

## Recognizer

Text transcriptions can be infered from audio file with the functions `asr.recognizer.transcribe_file(path)` and  `asr.recognizer.transcribe_file_timecoded(path)`.
If working with pydub.AudioSegment, the functions `asr.recognizer.transcribe_segment(audiosegment)` and `asr.transcribe_segment_timecoded(audiosegment)`.

No post-processing is applied by default.

Speech-to-Text post-processing steps:

Raw infered text
  -> Verbal fillers removal (optional)
  -> n-token substitution (from 'asr/postproc_sub.tsv')
  -> Numbers and units inverse normalization (optional)
  -> Regional adaptation (optional)

The 'n-token substitution' step adds necessary hypens, composed name and brand capitalization.

## Toy corpora

The library comes with a few toy corpora from the public domain.

## Text corpus annotation

Metadata

Special tokens :
`<UNK>`, `<C'HOARZH>`, `<NTT>`

Verbal fillers

## Audio file manipulation

Audio data augmentation
