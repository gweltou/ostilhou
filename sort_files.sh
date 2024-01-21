#! /bin/bash

FILES="
ostilhou/dicts/proper_nouns_phon.tsv
ostilhou/dicts/noun_m.tsv
ostilhou/dicts/noun_f.tsv
ostilhou/dicts/acronyms.tsv
ostilhou/dicts/corrected_tokens.tsv
ostilhou/dicts/standard_tokens.tsv
ostilhou/dicts/gwenedeg_peurunvan.tsv
ostilhou/dicts/sarmonioù_peurunvan.tsv
ostilhou/dicts/interjections.tsv
ostilhou/hspell/add.txt
ostilhou/hspell/add_gwe.txt
ostilhou/asr/lexicon_add.tsv
ostilhou/asr/lexicon_sub.tsv
ostilhou/asr/postproc_sub.tsv
"

for file in $FILES
do
    sort $file -o $file
done
