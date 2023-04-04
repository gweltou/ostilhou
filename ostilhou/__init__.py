import os
from typing import List
from ostilhou.text.tokenizer import tokenize, detokenize
from ostilhou.text.normalizer import normalize_sentence
from ostilhou.asr import phonetize



def list_files_with_extension(ext, rep, recursive=True) -> List[str]:
    file_list = []
    if os.path.isdir(rep):
        for filename in os.listdir(rep):
            filename = os.path.join(rep, filename)
            if os.path.isdir(filename) and recursive:
                file_list.extend(list_files_with_extension(ext, filename))
            elif os.path.splitext(filename)[1] == ext:
                file_list.append(filename)
    return file_list