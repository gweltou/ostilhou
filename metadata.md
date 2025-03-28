# Metadata specification

Kinda like CSS for metadata integration in text corpuses.
All metadata are optional.

## Header

```
{source: url_to_text_data}
{source-audio: url_to_audio}
{audio-path: path_to_audio_file}
{author: author_of_audiofile, other_author...}
{transcription: author_of_transcription}
{modifications: author_of_corrections}
{licence: }
{tags: tag1, tag2, tag3...}

{parser: no-lm/add-lm}	# Exclude or include text into language model

```

## Speaker name

`{spk: Marc'harid Lagadeg}`

Sentence scope.

Applies for the whole sentence and until another `spk` property is found or end of document is reached.

As its usage is frequent, a metadata with no attribute should be interpreted as a speaker name, with the exception of the `{?}` (unknown word) metadata.

Names are case-insensitive.

`{Marc'harid Lagadeg}`

When the speaker name is not known, `{unknown}` can be used.

## Speaker gender

`{gender: f/m}`

Global scope.

The speaker gender attribute applies to the current speaker. As such it should be be put on the same line as the speaker name metadata, or on a subsequent line where the speaker name still applies.

It is enough to specify the speaker's gender only once. It will be taken into account for the whole document and even accros documents when parsing a corpus.

Different attribute can be chained in the same metadata with the `;` character :

`{spk: Marc'harid Lagadeg; gender: f}`

## Language

`{lang: br|fr}`

## Accent

`{accent: gwenedeg}`

Sentence scope.

Accent metadata applies until another `accent` property is found or end of document is reached.

Possible values : gwened(eg), leon(eg), treger(ieg), kerne(veg), gwenrann(eg), goueloù, bear, fañch...

You can specify a list of values for an attribute, by separating them with a comma `,` :

`{accent: kerneveg, kemper}`

## Authors

Names of people and software responsible for transcribing the text (in order if possible)

`{author: vosk-br, Katell Lagadeg, Yann Kloareg}`

Document scope.

Transcriber metadata applies until another `author` property is found or end of document is reached.

Names are case-insensitive.

## Parser

Parser commands.

`{parser: no-lm/add-lm}`

Sentence scope. Applies until another `{parser: no-lm/add-lm}` is found or end of document is reached.

Exclude/add sentence to language model training dataset. Defaults to `add-lm` (add).

`{parser: ignore/add}`

Text between a `{parser: ignore}` and a `{parser: add}` will be removed from the utterance. Defaults to `add`.