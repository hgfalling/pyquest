"""
Small script for loading MMPI data to run questionnaire from matlab .mat files.
Takes one optional command line argument:
    (nothing) = load MMPI2.mat  (the original file)
    aq        = load MMPI2_AntiQuestions.mat (the doubled questions file)
    de        = load MMPI2.Depolarized.mat (the depolarized file)
Fix the DEFAULT_DATA_PATH before using.
"""

import scipy.io
import sys

DEFAULT_DATA_PATH = "/users/jerrod/Google Drive/Yale_Research/Questionnaire_2D_20130614/Examples/"

if len(sys.argv) == 1:
    data_file = "MMPI2.mat"
elif sys.argv[1] == "aq":
    data_file = "MMPI2_AntiQuestions.mat"
elif sys.argv[1] == "de":
    data_file = "MMPI2_Depolarized.mat"

#scipy.io will handle matlab files and load them into numpy structures.
#to load the tree files into trees, use matlab_util.
mdict = scipy.io.loadmat(DEFAULT_DATA_PATH+data_file)

data = mdict["matrix"]
q_descs = [x[0][0] for x in mdict["sensors_dat"][0,0][0]]
p_score_descs = [x[0] for x in mdict["points_dat"][0,0][1][0]]
p_scores = mdict["points_dat"][0,0][0]