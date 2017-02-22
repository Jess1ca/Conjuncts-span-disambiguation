
Run: python src/candidates_extractor.py <sentences_path> <probs_path> <out_path> <coordinators_to_extract> <n_spans>


Where:

"sentences path" - a path to a file where each line includes a numerical id and a tokenized sentence (seperated by tab).

"probs path" - the path to the output of berkeley parser (https://github.com/Jess1ca/berkeleyparser) on the sentences in "sentences path".

"out path" - the folder where the candidates file will be stored.

"coordinators to extract" - list of the required coordinators separated by comma. e.g "and,or".

"n spans" - the maximum number of conjuncts in a candidate (minimum 2).
