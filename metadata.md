# Metadata specification

Kinda like CSS for metadata integration in text corpuses.

## Speaker name

{spk:marc'harid lagadeg}

Sentence scope.

Applies for the whole sentence and until another `spk` property is found or end of document is reached.

As its usage is frequent, a metadata with no attribute should be interpreted as a speaker name, with the exception of the `{?}` (unknown word) metadata.

Names are case-insensitive.

{marc'harid lagadeg}

## Speaker gender

{gender:f/m}

Global scope.

The speaker gender attribute applies to the current speaker. As such it should be be put on the same line as the speaker name metadata, or on a subsequent line where the speaker name still applies.

It is enough to specify the speaker's gender only once. It like be taken into account for the whole document and even accros documents when parsing a corpus.

Different attribute can be chained in the same metadata with the `;` character :

{spk:marc'harid lagadeg; gender:f}

## Accent

{accent:gwenedeg}

Sentence scope.

Accent metadata applies until another `accent` property is found or end of document is reached.

Possible values : gwened(eg), leon(eg), treger(ieg), kerne(veg), gwenrann(eg), goueloù, bear...

You can specify a list of values for an attribute, by separating them with a comma `,` :

{accent:kerneveg, kemper}

## Authors

Names of people and software responsible for transcribing the text (in order if possible)

{author:vosk-br, karen treguier, gweltaz duval-guennoc}

Document scope.

Transcriber metadata applies until another `author` property is found or end of document is reached.

Names are case-insensitive.

## Parser

Parser commands.

`no-lm`/`add-lm`

Sentence scope.

Exclude/add sentence to language model training dataset. Defaults to `add-lm` (add).

