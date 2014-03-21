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