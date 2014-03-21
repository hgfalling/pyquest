"""
Small script for loading data to run questionnaire from .npz files
    (nothing) = load MMPI2.npz  (the original file)
    aq        = load MMPI2_AntiQuestions.npz (the doubled questions file)
    de        = load MMPI2.Depolarized.npz (the depolarized file)
    sn        = load SN_basic.npz 
Fix the DEFAULT_DATA_PATH before using.
"""

import numpy as np
import sys

def load_data(file_path):
    
    with np.load(file_path) as fdict:
        data = fdict["data"]
        q_descs = fdict["q_descs"]
        p_score_descs = fdict["p_score_descs"]
        p_scores = fdict["p_scores"]
    
    return data,q_descs,p_score_descs,p_scores 

def load_sn_data(file_path):
    with np.load(file_path) as mfile:
        data = mfile['matrix']
        #data = np.hstack([data[:,0:347],data[:,348:]])
        score_titles = [x[0] for x in mfile['score_titles'][0]]
        doc_titles = np.array([x[0] for x in mfile['doc_titles'][0]])
        #doc_titles = np.hstack([doc_titles[0:347] + doc_titles[348:]]) 
        words = np.array([x[0][0] for x in mfile['words']])
        doc_class = np.array(mfile['doc_class'][0,:])    
        #doc_class = np.hstack([doc_class[0,0:347], doc_class[0,348:]]) 
    return data,score_titles,doc_titles,words,doc_class 

if __name__ == "__main__":
    DEFAULT_DATA_PATH = "./"

    if len(sys.argv) == 1:
        file_path = DEFAULT_DATA_PATH + "MMPI2.npz"
        data,q_descs,p_score_descs,p_scores = load_data(file_path)
    elif sys.argv[1]=="aq":
        file_path = DEFAULT_DATA_PATH + "MMPI2_AntiQuestions.npz"
        data,q_descs,p_score_descs,p_scores = load_data(file_path)
    elif sys.argv[1]=="de":
        file_path = DEFAULT_DATA_PATH + "MMPI2_Depolarized.npz"
        data,q_descs,p_score_descs,p_scores = load_data(file_path)
    elif sys.argv[1]=="sn":
        file_path = DEFAULT_DATA_PATH + "SN_basic.npz"
        data,score_titles,doc_titles,words,doc_class = load_sn_data(file_path)


