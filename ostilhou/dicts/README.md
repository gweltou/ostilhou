## proper_noun_phon.tsv

Composed proper nouns (including an hyphen) should be put split before adding them to this list.

Ex: Marie-Françoise ->  \
	Françoise F R AN S O A Z \
	Marie M A R I

## 'noun_f.tsv' and 'noun_m.tsv'

Female and male nouns were extracted from br.wikipedia (*see main.py/test_wiki150*), with additions from apertium-br

Nouns are kept lowercase with no mutations

## corrected_tokens.tsv

Common mistakes and corrections.

The first column must contain only single words/tokens (without any embedded spaces). All tokens in this column should be lowercase.

The second column is for the replacement token(s). Those tokens should be capitalized if necessary. Many words can be put there, separated by a single space. A "wrong" token can therefore be replaced by multiple "correct" tokens.

## Other files

| stopwords | Words that are unambiguously not Breton |
