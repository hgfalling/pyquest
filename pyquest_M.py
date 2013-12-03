from wx.lib.pubsub import Publisher
import numpy as np
import threading
import run_quest
import affinity
import dual_affinity
import markov
import barcode
import cPickle
import tree_util

class TreeData(object):
    data = None
    data_type = None

class PyQuestDataModel(object):
    def __init__(self):
        self.quest_runs = []
        self.path = None
        self.true_data = None
        self.data = None
        self.row_data = TreeData()
        self.col_data = TreeData()
        self.row_affinity = None
        self.col_affinity = None
        self.row_vecs = None
        self.row_vals = None
        self.col_vecs = None
        self.col_vals = None
        self.row_order = None
        self.col_order = None
        self._selected_run = None
        self.selected_rowtree = None
        self.selected_coltree = None
        self.selected_nodes = {}
        self.othertrees = {}
        
    def save(self,filename):
        fout = open(filename,"wb")
        cPickle.dump(self.__dict__,fout)
        fout.close()
    
    def load(self,filename):
        fin = open(filename,"rb")
        self.__dict__ = cPickle.load(fin)
        fin.close()
        Publisher.sendMessage("data.load")
        Publisher.sendMessage("data.run")
        Publisher.sendMessage("rowtree.select")
        Publisher.sendMessage("coltree.select")
        Publisher.sendMessage("view.refresh")

    def reset_calcs(self):
        self.row_affinity = None
        self.col_affinity = None
        self.row_vecs = None
        self.row_vals = None
        self.col_vecs = None
        self.col_vals = None
        Publisher.sendMessage("embed.calc.row")
        Publisher.sendMessage("embed.calc.col")
        Publisher.sendMessage("affinity.calc.row")
        Publisher.sendMessage("affinity.calc.col")

    def load_data(self,file_path):
        self.path = file_path
        self.true_data = None
        with np.load(file_path) as fdict:
            self.data = fdict["data"]
            self.row_data = TreeData()
            self.col_data = TreeData()
            self.row_data.data = fdict["q_descs"]
            self.row_data.data_type = "descs"
            self.col_data.data = (fdict["p_score_descs"],fdict["p_scores"])
            self.col_data.data_type = "scores"
        
        self.row_order = np.arange(self.data.shape[0])
        self.col_order = np.arange(self.data.shape[1])
        np.random.shuffle(self.row_order)
        np.random.shuffle(self.col_order)
        self.reset_calcs()
        Publisher.sendMessage("data.load")
        
    def select_run(self,run_selected_idx):
        if run_selected_idx == self._selected_run:
            return
        elif run_selected_idx < len(self.quest_runs):
            self._selected_run = run_selected_idx
        else:
            self._selected_run = None
        
        Publisher.sendMessage("run.select")
        if self._selected_run is not None:
            self.select_tree("rowtree", len(self.selected_run.row_trees)-1)
            self.select_tree("coltree", len(self.selected_run.col_trees)-1)

    def select_tree(self,tree_id,tree_idx):
        sel_run = self.quest_runs[self._selected_run]
        if tree_id == "rowtree":
            if tree_idx > len(sel_run.row_trees):
                self.selected_rowtree = None
            else:
                self.selected_rowtree = tree_idx
        if tree_id == "coltree":
            if tree_idx > len(sel_run.col_trees):
                self.selected_coltree = None
            else:
                self.selected_coltree = tree_idx
        Publisher.sendMessage(tree_id+".select")

    def tree(self,tree_id):
        if tree_id == "rowtree":
            return self.row_tree
        elif tree_id == "coltree":
            return self.col_tree
        else:
            return self.othertrees[tree_id]

    def tree_data(self,tree_id):
        if tree_id == "rowtree":
            return self.row_data
        elif tree_id == "coltree":
            return self.col_data    
        else:
            return None

    @property
    def selected_run(self):
        return self.quest_runs[self._selected_run]

    @property
    def row_tree(self):
        if self._selected_run is None:
            return None
        elif self.selected_rowtree is None:
            return None
        else:
            sel_run = self.quest_runs[self._selected_run]
            return sel_run.row_trees[self.selected_rowtree]

    @property
    def col_tree(self):
        if self._selected_run is None:
            return None
        elif self.selected_coltree is None:
            return None
        else:
            sel_run = self.quest_runs[self._selected_run] 
            return sel_run.col_trees[self.selected_coltree]

    def vecs(self,topic):
        if "row" in topic:
            return self.row_vecs
        elif "col" in topic:
            return self.col_vecs
        else:
            return None

    def vals(self,topic):
        if "row" in topic:
            return self.row_vals
        elif "col" in topic:
            return self.col_vals
        else:
            return None

    def tree_avgs(self,topic):
        if "row" in topic:
            return self.avg_tree_rows
        elif "col" in topic:
            return self.avg_tree_cols
        else:
            return None

    def run_questionnaire(self,params):
        t = PyQuestRunThread(params,self)

    def _run_questionnaire(self,params):
        Publisher.sendMessage("status.bar", "Running questionnaire...")

        self.quest_runs.append(run_quest.pyquest(self.data,params))
        self.select_run(len(self.quest_runs)-1)
        #row_tree = self.quest_runs[-1][1].row_trees[-1]
        #col_tree = self.quest_runs[-1][1].col_trees[-1]

        Publisher.sendMessage("data.run")

        #the parameter is called row_tree either way, so the second arg is
        #not an error
        self.calc_row_affinity(params.row_affinity_type,
                               row_tree=self.tree("coltree"),
                               alpha=params.row_alpha,beta=params.row_beta)
        self.calc_col_affinity(params.row_affinity_type,
                               row_tree=self.tree("rowtree"),
                               alpha=params.row_alpha,beta=params.row_beta)

        Publisher.sendMessage("status.bar", "Ready.")
        
    def calc_row_embedding(self):
        self.row_vecs, self.row_vals = markov.markov_eigs(self.row_affinity, 8)
        Publisher.sendMessage("embed.row.calc")

    def calc_col_embedding(self):
        self.col_vecs, self.col_vals = markov.markov_eigs(self.col_affinity, 8)
        Publisher.sendMessage("embed.col.calc")
    
    def calc_row_affinity(self,affinity_type,**kwargs):
        self.row_affinity = self._calc_affinity(self.data.T,affinity_type,**kwargs)
        Publisher.sendMessage("affinity.calc.row")
        self.calc_row_embedding()
    
    def calc_col_affinity(self,affinity_type,**kwargs):
        self.col_affinity = self._calc_affinity(self.data,affinity_type,**kwargs)
        Publisher.sendMessage("affinity.calc.col")
        self.calc_col_embedding()
        
    def _calc_affinity(self,data,affinity_type,**kwargs):
        if affinity_type == run_quest.INIT_AFF_COS_SIM: #cosine similarity
            affinity_matrix = affinity.mutual_cosine_similarity(data,**kwargs)
        elif affinity_type == run_quest.DUAL_EMD: #EMD
            emd = dual_affinity.calc_emd(data,**kwargs)
            affinity_matrix = dual_affinity.emd_dual_aff(emd)
        return affinity_matrix
    
    def calc_avg_val_rows(self,row_tree,col_tree):
        if col_tree is None:
            print "empty column tree"
            pass
        else:
            avg_level_rows = barcode.level_avgs(self.data.T,row_tree).T
            avg_tree_rows = tree_util.tree_averages(avg_level_rows.T,col_tree).T
            self.avg_tree_rows = avg_tree_rows
            Publisher.sendMessage("embed.row.avg")
        return avg_tree_rows
    
    def calc_avg_val_cols(self,row_tree,col_tree):
        if row_tree is None:
            pass
        else:
            avg_level_cols = barcode.level_avgs(self.data,col_tree)
            avg_tree_cols = tree_util.tree_averages(avg_level_cols,row_tree).T
            self.avg_tree_cols = avg_tree_cols
            Publisher.sendMessage("embed.col.avg")
        return avg_tree_cols

    def node_select(self,tree_id,node):
        self.selected_nodes[tree_id] = node
        Publisher.sendMessage(tree_id + ".node.select",node)
        
    def tree_node(self,tree_id):
        if tree_id in self.selected_nodes:
            return self.selected_nodes[tree_id]
        else:
            return None
        
class PyQuestRunThread(threading.Thread):
    def __init__(self,params,model):
        threading.Thread.__init__(self)
        self.params = params
        self.model = model
        self.start()
    
    def run(self):
        self.model._run_questionnaire(self.params)
        