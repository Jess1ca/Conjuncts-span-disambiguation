from constituency_tree.tree_readers import read_trees_oneperline_file
import os
import sys

COORD = "COORD"
CC = "CC"
CCP = "CCP"

N_PRE_TRAIN = 3914
N_TRAIN = 39832
N_DEV = 1700

def divide_to_sets(file_path):
    train = open(file_path + ".train", 'w')
    dev = open(file_path + ".dev", 'w')
    test = open(file_path + ".test", 'w')
    for line in open(file_path):
        ind = int(line.split("\t")[0])
        if N_PRE_TRAIN < ind <= N_TRAIN:
            train.write(line)
        elif N_TRAIN+N_PRE_TRAIN <= ind <= N_TRAIN+N_PRE_TRAIN+N_DEV:
            dev.write(line)
        elif ind > N_TRAIN+N_PRE_TRAIN+N_DEV:
            test.write(line)

def remove_ids(input_file, output_file):
    output_file = open(output_file, 'w')
    for line in open(input_file):
        line = line.strip().split("\t")[-1]
        output_file.write(line + "\n")
    output_file.close()

def get_phrase_label(n):
    if COORD in n:
        return COORD
    if CC+"-"+CC in n:
        return CC
    return None

def gold_spans(trees_path, out_path, extraBrackets = True):
    trees = list(read_trees_oneperline_file(open(trees_path,'r'),extra_bracket=extraBrackets))
    f = open(out_path,'w')
    sentences_ids = []
    for i, tree in enumerate(trees):
        ccps = list(tree.search(lambda x:CCP in x.name))
        for ccp in ccps:
            l = [x.dep_id for x in list(ccp.collect_leaves(ignore_empties=True))]
            mi, ma = min(l), max(l)
            s = []
            cc = [ch for ch in ccp.childs if get_phrase_label(ch.name) == CC][-1]
            if cc.value[1].lower() not in ["and","or","nor","and\/or","but"]:
                continue
            elif i not in sentences_ids:
                sentences_ids.append(i)
            cc_id = list(cc.collect_leaves(ignore_empties=True))[0].dep_id - 1
            coords = [ch for ch in ccp.childs if get_phrase_label(ch.name) == COORD]
            for ch in coords:
                syntactic_label = ch.get_name().split("-")[0].split("=")[0]
                l = list(ch.collect_leaves(ignore_empties=True))
                start_ind = l[0].dep_id-1
                end_ind = l[-1].dep_id-1
                s.append(syntactic_label+"-"+str(start_ind)+"-"+str(end_ind))
            ccp_syntactic_label = ccp.get_name().split("-")[0].split("=")[0]
            f.write("\t".join([str(i), str(cc_id), ccp_syntactic_label, str(mi-1)+"-"+str(ma-1)]+s) + "\n")
    f.close()
    return [(i, trees[i].as_words()) for i in sentences_ids]


def sentences_with_coordination(sentences, sentences_with_coord_ids):
    sentences_with_coord_ids = open(sentences_with_coord_ids, 'w')
    for i, sent in sentences:
        sentences_with_coord_ids.write("\t".join([str(i), sent]) + "\n")
    sentences_with_coord_ids.close()



if __name__ == "__main__":

    # Usage: python coordination_for_training.py <constituency trees> <out folder>

    trees_path = sys.argv[1]
    out_path = sys.argv[2]

    # coordinations gold spans
    gold_spans_out = out_path+"gold_spans"
    sentences = gold_spans(trees_path, gold_spans_out)
    divide_to_sets(gold_spans_out)


    # sentences with coordination
    sentences_with_coord = out_path + "sentences_with_coord"
    sentences_with_coord_ids = out_path + "sentences_with_coord.ids"
    sentences_with_coordination(sentences, sentences_with_coord_ids)
    divide_to_sets(sentences_with_coord_ids)

    remove_ids(sentences_with_coord_ids, sentences_with_coord)
    remove_ids(sentences_with_coord_ids+".train", sentences_with_coord+".train")
    remove_ids(sentences_with_coord_ids + ".dev", sentences_with_coord + ".dev")
    remove_ids(sentences_with_coord_ids + ".test", sentences_with_coord + ".test")



