"""
Writes out files to be used with the viewers.
"""

import cPickle

def write_tree_viewer(filename,tree,vecs,vals,descs=None,tree_desc=""):
    datadict = {}
    datadict['tree'] = tree
    datadict['vecs'] = vecs
    datadict['vals'] = vals
    if descs is None:
        datadict['data_descs'] = [str(i) for i in xrange(tree.size)]
    else:
        datadict['data_descs'] = descs
    datadict['tree_desc'] = tree_desc
    fout = open(filename,'wb')
    cPickle.dump(datadict,fout)
    fout.close()

def write_question_viewer(filename,data,row_tree,col_tree,row_vecs,
                          row_vals,col_vecs,col_vals,descs=None,
                          p_score_descs=None,p_scores=None):
    datadict = {}
    datadict["data"] = data
    if descs is None:
        datadict['q_descs'] = [str(i) for i in xrange(row_tree.size)]
    else:
        datadict['q_descs'] = descs
    datadict["p_score_descs"] = p_score_descs
    datadict["p_scores"] = p_scores
    datadict["col_tree"] = col_tree
    datadict["row_tree"] = row_tree
    datadict["col_vecs"] = col_vecs
    datadict["col_vals"] = col_vals
    datadict["row_vecs"] = row_vecs
    datadict["row_vals"] = row_vals
    fout = open(filename,'wb')
    cPickle.dump(datadict,fout)
    fout.close()