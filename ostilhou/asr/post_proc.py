_postproc_sub = dict()
_postproc_sub_path = __file__.replace("__init__.py", "postproc_sub.tsv")

with open(_postproc_sub_path, 'r') as f:
    for l in f.readlines():
        l = l.strip()
        if l and not l.startswith('#'):
            k, v = l.split('\t')
            _postproc_sub[k] = v


def sentence_post_process(text):
    if not text:
        return ''
    
    # web adresses
    if "HTTP" in text or "WWW" in text:
        text = text.replace("pik", '.')
        text = text.replace(' ', '')
        return text.lower()
    
    for sub in _postproc_sub:
        text = text.replace(sub, _postproc_sub[sub])
    
    splitted = text.split(maxsplit=1)
    splitted[0] = splitted[0].capitalize()
    return ' '.join(splitted)
