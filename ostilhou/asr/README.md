# Automatic Speech Recognition module

## `corrected_tokens.tsv`

Dictionary file containing tokens to be replaced before training the STT model with the data. Could be to correct spelling mistakes or to normalize various words in order to reduce the LM vocabulary size. Also the best place to add your own autocratic language reforming rules !

Left column should contain only single words (with no spaces) found in the raw data. They are case-insensitive.
Right column can contain many words, separated by spaces. Proper names in this column should be capitalized.

## `postproc_sub.tsv`

Dictionary file containing tokens to be replaced in the decoding output of the STT model. There we can correct missing hyphens or apostrophes, capitalize compounded proper names and so on...

Left column should contain only single words (with no spaces) found in the raw data. They are case-insensitive.
Right column can contain many words, separated by spaces. Proper names in this column should be capitalized.
