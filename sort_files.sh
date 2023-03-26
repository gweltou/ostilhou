#! /bin/bash

FILES="
ostilhou/dicts/acronyms.tsv
ostilhou/dicts/proper_nouns_phon.tsv
ostilhou/dicts/gwenedeg_peurunvan.tsv
ostilhou/dicts/hunspell-dictionary/add.txt
ostilhou/dicts/noun_m.tsv
ostilhou/dicts/noun_f.tsv
ostilhou/asr/lexicon_add.tsv
ostilhou/asr/lexicon_sub.tsv
"

for file in $FILES
do
    sort $file -o $file
done
