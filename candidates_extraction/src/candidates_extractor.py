import sys
import json
from collections import defaultdict
from itertools import combinations
import os


PUNCT = [",",";","``","\"","'","''","...",":","-LRB-","-RRB-","(",")"]

def coordinators(sentences, coordinators_to_extract):
    keys = []
    for i,(ext_ind,sent) in sentences.iteritems():
        for j, word in enumerate(sent):
            if word in coordinators_to_extract:
                keys.append((i,ext_ind,j))
    return keys

def read_sentences(path):
    sentences = {}
    for i, line in enumerate(open(path)):
        external_ind, sent = line.strip().split("\t")
        sentences[i] = (int(external_ind), sent.lower().split())
    return sentences


def get_coords(probs):

    coords = {}
    ccs = {}
    ccps = {}

    trees_counter = -1
    ccps_ids = []
    for line in open(probs,'r'):
        line = line.strip()
        if line == "PROB-START":
            if trees_counter > -1:
                ccps[trees_counter] = ccps_ids
                ccps_ids = []
            trees_counter += 1
            continue
        d = json.loads(line)
        label = d["stateStr"][0].replace("@","")
        start = int(d["start"][0])
        end = int(d["end"][0])
        if "CCP" not in label.split("_") :
            continue
        ccps_ids.append((start,end))
    ccps[trees_counter] = ccps_ids

    trees_counter = -1
    cc_ids = []
    for line in open(probs,'r'):
        line = line.strip()
        if line == "PROB-START":
            if trees_counter > -1:
                ccs[trees_counter] = cc_ids
                cc_ids = []
            trees_counter += 1
            continue
        d = json.loads(line)
        label = d["stateStr"][0].replace("@","")
        start = int(d["start"][0])
        end = int(d["end"][0])
        if label != "CC_CC" :
            continue
        cc_ids.append(start)
    ccs[trees_counter] = cc_ids

    trees_counter = -1
    coords_probs = {}
    for line in open(probs,'r'):
        line = line.strip()
        if line == "PROB-START":
            if trees_counter > -1:

                coords[trees_counter] = coords_probs
                coords_probs = {}
            trees_counter += 1
            continue
        d = json.loads(line)
        label = d["stateStr"][0].replace("@","")
        start = int(d["start"][0])
        end = int(d["end"][0])
        probi = float(d["I"][0]) * (end-start)
        probo = float(d["O"][0]) * (end-start)

        if "COORD" not in label.split("_") :
            continue
        if (start,end) not in coords_probs:
            coords_probs[(start,end)] = {"I":0,"O":0}
        coords_probs[(start,end)]["I"] += probi
        coords_probs[(start,end)]["O"] += probo

    coords[trees_counter] = coords_probs

    return coords,ccs,ccps


def get_candidates(sentences, probs, n_coord, coordinators_to_extract):
    coords,ccs,ccps = get_coords(probs)
    candidates = defaultdict(list)
    count = 0
    for sent_id in coords.keys():
        ext_sent_id, sentence = sentences[sent_id]
        for s in combinations(sorted(coords[sent_id].keys()),2):
            start_0 = s[0][0]
            end_0 = s[0][1]
            start_2 = s[1][0]
            end_2 = s[1][1]

            coordinators =  [i for i in range(end_0,start_2) if sentence[i].lower() in coordinators_to_extract]
            only_punct_flag = True if len([1 for i in range(end_0,start_2) if sentence[i].lower() not in PUNCT])==1 else False

            if len(coordinators)==1 and only_punct_flag:
                cc_id = coordinators[0]
            else:
                continue

            key = (sent_id,cc_id)
            if (s,coords[sent_id][s[0]],coords[sent_id][s[1]]) not in candidates[key]:
                count+=1
                candidates[key].append((s,coords[sent_id][s[0]],coords[sent_id][s[1]]))

    if n_coord == 2:
        return candidates, ccps

    for i in range(n_coord-2):
        for sent_id in coords.keys():
            for coord in coords[sent_id]:
                for key in [k for k in candidates.keys() if int(k[0]) == sent_id]:
                    for s in candidates[key]:
                        p=s
                        s = s[0]
                        if len(s) > 2+i:
                            continue
                        start_0 = s[0][0]
                        if coord[1] + 1 == start_0 and sentences[sent_id][coord[1]] in coordinators_to_extract+PUNCT:
                            t = [coords[sent_id][coord]]+list(p[1:])
                            t = [tuple([coord]+list(s))] + t
                            t = tuple(t)
                            if t not in candidates[key]:
                                candidates[key].append(t)
    return candidates, ccps

def candidate_str(can,l):
    p = can[0]
    prob1 = can[1]
    prob2 = can[-1]
    s = ""
    #coordinates
    for b,e in [p[0],p[-1]]:
        s+= str(b)+"-"+str(e-1)+"\t"

    x1 = p[0][0]
    x4 = p[-1][1]
    #pre
    if x1>0:
        s+="0-"+str(x1-1)+"\t"
    else:
        s+="NA"+"\t"
    #post
    if x4<l:
        s+=str(x4)+"-"+str(l-1)+"\t"
    else:
        s+="NA"+"\t"

    s+= "\t".join([str(prob1["I"]),str(prob1["O"]),str(prob2["I"]),str(prob2["O"])]) + "\t"
    return s

def create_candidates_file(coordinators, sentences, probs, out_path, coordinators_to_extract, n_coord=2):
    candidates,ccps = get_candidates(sentences ,probs ,n_coord, coordinators_to_extract)
    f = open(out_path,'w')

    for i,ext_ind,cc_id in sorted(coordinators):
        _, sent = sentences[i]
        sent_with_tokens_numbers = " ".join([str(j)+"-"+w  for j,w in enumerate(sent)])
        header = "\t".join([str(ext_ind), str(cc_id), sent_with_tokens_numbers])
        f.write(header+"\n")
        l = len(sentences[i])
        for j,s in enumerate(candidates[(i,cc_id)]):
            f.write(candidate_str(s,l) + "\n")
    f.close()

def create_spans_file(cand_path,out_path):
    spans = {}

    f = open(out_path,'w')
    id = None
    for line in open(cand_path):
        line = line.split("\t")
        if "-" not in line[0]:
            id = int(line[0])
            if id not in spans:
                spans[id] = []
            continue
        c1,c2 = line[:2]
        spans[id].append(c1.split("-")[0] + "\t" + str(int(c1.split("-")[1])+1) )
        spans[id].append(c2.split("-")[0] + "\t" + str(int(c2.split("-")[1])+1) )

    for c,id in enumerate(sorted(spans.keys())):
        for s in sorted(set(spans[id])):
            f.write("\t".join([str(c),str(id),s]) + "\n")
    f.close()

if __name__ == "__main__":
    sentences_path = sys.argv[1]
    probs = sys.argv[2]
    out_path = sys.argv[3]
    coordinators_to_extract = sys.argv[4].split(",")
    n_spans = int(sys.argv[5])

    sentences = read_sentences(sentences_path)
    coordinators = coordinators(sentences, coordinators_to_extract)

    candidates_path = os.path.join(out_path,os.path.basename(sentences_path) + ".candidates")
    create_candidates_file(coordinators, sentences, probs, candidates_path, coordinators_to_extract, n_coord=n_spans)

    spans_path = os.path.join(out_path, os.path.basename(sentences_path) + ".spans")
    create_spans_file(candidates_path, spans_path)

