# Ostilhoù

A lightweight and simple NLP toolkit for the breton language, in Python.

## Setup

After cloning the repository :

```sh
pip install -r requirements.txt
```

## Working with text

Sentence splitting, simple pre-tokenizer, text normalization, text inverse-normalization.

Spelling error detection with An Drouizig's hunspell dictionary.

## [Dictionaries](ostilhou/dicts/README.md)

Various dictionary files (tsv format) for proper nouns, first names, last names, nouns (with gender), acronyms.

## Phonetizer

`asr.phonetize_word` function.

No API transcription for now...

## Recognizer

Using a Vosk model.

Text transcriptions can be infered from audio file with the functions `asr.recognizer.transcribe_file(path)` and  `asr.recognizer.transcribe_file_timecoded(path)`.

If working with pydub.AudioSegment, the functions `asr.recognizer.transcribe_segment(audiosegment)` and `asr.transcribe_segment_timecoded(audiosegment)`.

No post-processing is applied by default.

Speech-to-Text post-processing steps:

Raw infered text \
  -> Verbal fillers removal (optional) \
  -> n-token substitution (from 'asr/postproc_sub.tsv') \
  -> Numbers and units inverse-normalization (optional) \
  -> Regional adaptation, using a look-up table (optional)

The 'n-token substitution' step adds necessary hypens, composed name and brand name capitalization.

## Audio file manipulation

Audio data augmentation functions.

## [Toy corpora](ostilhou/corpora/)

The library comes with a few toy corpora from the public domain.
