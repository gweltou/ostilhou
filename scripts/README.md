# Various Scripts

## aligner.py

Create an `ali` file or a subtitles file by force-aligning a text file with a media file.

Usage: `python3 aligner.py audio_file text_file`

## ali_print_text.py

Prints the textual content of an ALI file to stdout.

Usage: `python3 ali_print_text.py file.ali`

## build_dataset.py

## build_kaldi.py

Build necessary files to train a model with the Kaldi toolkit.

Usage: `./build_kaldi.py -h`

## MCV_compare_tsv.py

Display informations about a `tsv` file, or compare two `tsv` files from a Mozilla Common Voice dataset archive.

Usage:
```
python3 MCV_compare_tsv.py dev.tsv
python3 MCV_compare_tsv.py train.tsv test.tsv
```

## MCV_unpack.py

Unpack a Mozilla Common Voice dataset archive and prepare data.

Usage: `python3 MCV_unpack.py train.tsv OUTPUT_FOLDER`

## 
