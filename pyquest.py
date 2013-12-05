import wx.lib.agw.flatnotebook as fnb
from wx.lib.buttons import GenButton
from wx.lib.masked import NumCtrl
from wx.lib.pubsub import Publisher
import wx
import wxplot_util
from imports import *
import run_quest
import pyquest_M

_version = 0.02

def debug_msg(message):
    if message.topic != ('status','bar'):
        print "message.  topic:{}, data:{}".format(message.topic,message.data)

Publisher.subscribe(debug_msg,"")

class PyQuestApp(wx.App):
    def __init__(self):
        wx.App.__init__(self,False)        

    def OnInit(self):
        self.frame = PyQuestFrame(None,wx.ID_ANY)
        return True

class PyQuestFrame(wx.Frame):
    def __init__(self,parent,obj_id):
        wx.Frame.__init__(self,parent,obj_id,pos=(0,0))
        self.Maximize()
        
        Publisher.subscribe(self.layout,'panel.layout')
        Publisher.subscribe(self.set_status,'status.bar')

        self.status_bar = self.CreateStatusBar()
        self.SetTitle("PyQuest Questionnaire {}".format(_version))

        self.menu_bar = wx.MenuBar()
        self.file_menu = wx.Menu()
        
        file_items = [('&Load Data','Load a data file',self.on_load_data),
                      ('Load Session','Load a previous session',self.on_load_session),
                      ('&Save Session','Save this session',self.on_save_session),
                      ('E&xit','Exit the program',self.on_quit),]
        
        for item_data in file_items:
            menu_item = self.file_menu.Append(wx.ID_ANY,item_data[0],item_data[1])
            self.Bind(wx.EVT_MENU,item_data[2],menu_item)
        
        self.menu_bar.Append(self.file_menu,'&File')
        self.SetMenuBar(self.menu_bar)

        self.notebook_panel = PyQuestNotebookPanel(self)
        self.run_panel = PyQuestRunPanel(self)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.run_panel,2,wx.EXPAND)
        self.sizer.Add(self.notebook_panel,7,wx.EXPAND)
        self.SetSizer(self.sizer)

        self.Layout()
        self.Show(1)

    def set_status(self,message):
        self.SetStatusText(message.data)
        self.Refresh()
    
    def layout(self,message):
        self.Layout()
        self.Refresh()

    def on_save_session(self,evt):
        dialog = wx.FileDialog(self,"Save Session File","","",
                               "Session files (*.session)|*.session",
                               wx.FD_SAVE)
        if dialog.ShowModal() == wx.ID_CANCEL:
            dialog.Destroy()
            return
        else:
            Publisher.sendMessage("status.bar", "Saving session...")
            global_model.save(dialog.GetPath())
            Publisher.sendMessage("status.bar", "Ready.")
            dialog.Destroy()

    def on_load_session(self,evt):
        dialog = wx.FileDialog(self,"Open Data File","","",
                               "Session files (*.session)|*.session",
                               wx.FD_OPEN | wx.FILE_MUST_EXIST)
        if dialog.ShowModal() == wx.ID_CANCEL:
            dialog.Destroy()
            return
        else:
            Publisher.sendMessage("status.bar", "Loading session...")
            global_model.load(dialog.GetPath())
            dialog.Destroy()
            Publisher.sendMessage("status.bar", "Ready.")
        
    def on_load_data(self,evt):
        dialog = wx.FileDialog(self,"Open Data File","","",
                               "Numpy save files (*.npz)|*.npz",
                               wx.FD_OPEN | wx.FILE_MUST_EXIST)
        if dialog.ShowModal() == wx.ID_CANCEL:
            dialog.Destroy()
            return
        else:
            Publisher.sendMessage("status.bar", "Loading data...")
            global_model.load_data(dialog.GetPath())
            Publisher.sendMessage("status.bar", "Ready.")
            dialog.Destroy()
            
    def on_quit(self,evt):
        self.Close()

class PyQuestRunPanel(wx.Panel):
    def __init__(self,parent):
        wx.Panel.__init__(self,parent,wx.ID_ANY)
        Publisher.subscribe(self.on_data_load,"data.load")
        Publisher.subscribe(self.on_data_run,"data.run")
        
        self.loaded_data_txt = wx.StaticText(self,wx.ID_ANY,
                            label="Data file loaded: {}".format(global_model.path))

        self.t_sizer1 = wx.BoxSizer(wx.VERTICAL)
        self.t_sizer2 = wx.BoxSizer(wx.VERTICAL)
        self.t_sizer3 = wx.BoxSizer(wx.VERTICAL)
        
        self.hsizer = wx.BoxSizer(wx.HORIZONTAL)

        self.sizer = wx.BoxSizer(wx.VERTICAL)

        self.run_label = wx.StaticText(self,wx.ID_ANY,label="Saved Questionnaire Runs:")
        self.run_list_box = wx.ListBox(self,wx.ID_ANY,choices=global_model.quest_runs,
                                            style=wx.LB_SINGLE,size=(180,80))
        self.Bind(wx.EVT_LISTBOX, self.on_run_list_box, self.run_list_box)

        self.row_tree_label = wx.StaticText(self,wx.ID_ANY,label="Row Trees:")
        self.row_tree_list_box = wx.ListBox(self,wx.ID_ANY,choices=[],
                                            style=wx.LB_SINGLE,size=(130,80))
        self.Bind(wx.EVT_LISTBOX, self.on_row_list_box, self.row_tree_list_box)

        self.row_tree_label.Show(False)
        self.row_tree_list_box.Show(False)

        self.col_tree_label = wx.StaticText(self,wx.ID_ANY,label="Column Trees:")
        self.col_tree_list_box = wx.ListBox(self,wx.ID_ANY,choices=[],
                                            style=wx.LB_SINGLE,size=(130,80)) 
        self.Bind(wx.EVT_LISTBOX, self.on_col_list_box, self.col_tree_list_box)

        self.col_tree_label.Show(False)
        self.col_tree_list_box.Show(False)

        self.t_sizer1.Add(self.run_label,0,flag=wx.ALL,border=5)
        self.t_sizer1.Add(self.run_list_box,0,flag=wx.LEFT | wx.RIGHT,border=5)
        self.t_sizer2.Add(self.row_tree_label,0,flag=wx.ALL,border=5)
        self.t_sizer2.Add(self.row_tree_list_box,0,flag=wx.LEFT | wx.RIGHT,border=5)
        self.t_sizer3.Add(self.col_tree_label,0,flag=wx.ALL,border=5)
        self.t_sizer3.Add(self.col_tree_list_box,0,flag=wx.LEFT | wx.RIGHT,border=5)
        
        self.hsizer.Add(self.t_sizer1,0,flag=wx.LEFT|wx.RIGHT,border=5)
        self.hsizer.Add(self.t_sizer2,0,flag=wx.LEFT|wx.RIGHT,border=5)
        self.hsizer.Add(self.t_sizer3,0,flag=wx.LEFT|wx.RIGHT,border=5)
        
        self.sizer.Add(self.loaded_data_txt,0,flag=wx.LEFT|wx.TOP,border=5)
        self.sizer.Add(self.hsizer,1,wx.EXPAND)
        self.SetSizer(self.sizer)
        
        self.Layout()
        self.Show(1)

    def on_run_list_box(self,evt):
        run_selected = self.run_list_box.GetSelection()
        global_model.select_run(run_selected)

    def on_row_list_box(self,evt):
        tree = self.row_tree_list_box.GetSelection()
        global_model.select_tree("rowtree",tree)

    def on_col_list_box(self,evt):
        tree = self.col_tree_list_box.GetSelection()
        global_model.select_tree("coltree",tree)

    def on_data_run(self,message):
        self.run_list_box.Clear()
        for q_run in global_model.quest_runs:
            self.run_list_box.Append(q_run.run_desc)
        self.run_list_box.SetSelection(len(global_model.quest_runs)-1)
        global_model.select_run(len(global_model.quest_runs)-1)
        self.update()
        self.Layout()

    def on_data_load(self,message):
        self.loaded_data_txt.SetLabel("Data file loaded: {}".format(global_model.path))
        self.Refresh()

    def update(self):
        self.row_tree_list_box.Clear()
        self.col_tree_list_box.Clear()
        
        run_selected = global_model.selected_run

        for desc in run_selected.row_tree_descs:
            self.row_tree_list_box.Append(desc)
        for desc in run_selected.col_tree_descs:
            self.col_tree_list_box.Append(desc)

        self.row_tree_label.Show(True)
        self.row_tree_list_box.Show(True)
        self.col_tree_label.Show(True)
        self.col_tree_list_box.Show(True)
        self.row_tree_list_box.SetSelection(len(run_selected.row_trees)-1)
        self.col_tree_list_box.SetSelection(len(run_selected.col_trees)-1)
        self.Layout()
        self.Refresh()
        Publisher.sendMessage("panel.layout")

class PyQuestNotebookPanel(wx.Panel):
    def __init__(self,parent):
        wx.Panel.__init__(self,parent,wx.ID_ANY)
        self.notebook = fnb.FlatNotebook(self,wx.ID_ANY)
        
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.notebook,1,wx.EXPAND)
        self.SetSizer(self.sizer)
        
        self.params_page = PyQuestParamsPage(self)
        self.notebook.AddPage(self.params_page,"Parameters",True,-1)
        
        self.data_page = PyQuestDataPage(self)
        self.notebook.AddPage(self.data_page,"Data")
        self.affinity_page = PyQuestAffinityPage(self)
        self.notebook.AddPage(self.affinity_page,"Affinity")
        self.row_tree_page = PyQuestTreePage(self,"Row Tree","rowtree")
        self.notebook.AddPage(self.row_tree_page,"Row Tree")
        self.col_tree_page = PyQuestTreePage(self,"Column Tree","coltree")
        self.notebook.AddPage(self.col_tree_page,"Col Tree")
        self.row_embed_page = PyQuestEmbedPage(self,"Row Embedding",topic="embed.row")
        self.notebook.AddPage(self.row_embed_page,"Row Embedding")
        self.col_embed_page = PyQuestEmbedPage(self,"Col Embedding",topic="embed.col")
        self.notebook.AddPage(self.col_embed_page,"Col Embedding")
        
        self.Layout()
        self.Show(1)

    def get_params(self):
        return self.params_page.get_params()
        
class PyQuestParamsPage(wx.Panel):
    def __init__(self,parent):
        wx.Panel.__init__(self,parent,wx.ID_ANY)
        Publisher.subscribe(self.on_run_select, "run.select")

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.gbs = wx.GridBagSizer(10,15)
        
        self.init_aff_label = wx.StaticText(self,wx.ID_ANY,label="Initial Affinity (Rows):")
        choices = [("Cosine Similarity",run_quest.INIT_AFF_COS_SIM),
                   ("Gaussian kernel",run_quest.INIT_AFF_GAUSSIAN)]
        self.init_aff_combo = wx.ComboBox(self,wx.ID_ANY,choices=[],
                                                  style=wx.CB_READONLY)
        for (label,choice_id) in choices:
            self.init_aff_combo.Append(label,choice_id)
        
        self.init_aff_combo.SetSelection(0)

        self.gbs.Add(self.init_aff_label,pos=(0,0),flag=wx.ALL,border=0)
        self.gbs.Add(self.init_aff_combo,pos=(0,1),flag=wx.EXPAND|wx.ALL,border=0)

        self.init_aff_param_label = wx.StaticText(self,wx.ID_ANY,label="")
        self.init_aff_param_text = NumCtrl(self,wx.ID_ANY,fractionWidth=2,
                                           signedForegroundColour="Black",
                                           value=run_quest.DEFAULT_INIT_AFF_THRESHOLD)

        self.Bind(wx.EVT_COMBOBOX,self.on_opt_change,self.init_aff_combo)

        self.gbs.Add(self.init_aff_param_label,pos=(0,2),flag=wx.ALL,border=0)
        self.gbs.Add(self.init_aff_param_text,pos=(0,3),flag=wx.EXPAND|wx.ALL,border=0)

        self.tree_type_label = wx.StaticText(self,wx.ID_ANY,label="Tree Type:")
        choices = [("Binary/Eigenvector",run_quest.TREE_TYPE_BINARY),
                   ("Flexible Clustering",run_quest.TREE_TYPE_FLEXIBLE)]
        self.tree_type_combo = wx.ComboBox(self,wx.ID_ANY,choices=[],
                                                  style=wx.CB_READONLY)
        self.Bind(wx.EVT_COMBOBOX,self.on_opt_change,self.tree_type_combo)
        for (label,choice_id) in choices:
            self.tree_type_combo.Append(label,choice_id)
        
        self.tree_type_combo.SetSelection(1)
        
        self.gbs.Add(self.tree_type_label,pos=(1,0),flag=wx.ALL,border=0)
        self.gbs.Add(self.tree_type_combo,pos=(1,1),flag=wx.EXPAND|wx.ALL,border=0)

        self.tree_param_label = wx.StaticText(self,wx.ID_ANY,label="")
        self.tree_param_text = NumCtrl(self,wx.ID_ANY,fractionWidth=2,
                                       signedForegroundColour="Black",
                                       value=run_quest.DEFAULT_TREE_CONSTANT)

        self.gbs.Add(self.tree_param_label,pos=(1,2),flag=wx.ALL,border=0)
        self.gbs.Add(self.tree_param_text,pos=(1,3),flag=wx.EXPAND|wx.ALL,border=0)
        
        self.row_dual_label = wx.StaticText(self,wx.ID_ANY,label="Dual Affinity (Rows):")
        choices = [("Earth Mover Distance",run_quest.DUAL_EMD)]
        self.row_dual_combo = wx.ComboBox(self,wx.ID_ANY,choices=[],
                                                  style=wx.CB_READONLY)
        self.Bind(wx.EVT_COMBOBOX,self.on_opt_change,self.row_dual_combo)

        for (label,choice_id) in choices:
            self.row_dual_combo.Append(label,choice_id)
        
        self.row_dual_combo.SetSelection(0)

        
        self.gbs.Add(self.row_dual_label,pos=(2,0),flag=wx.ALL,border=0)
        self.gbs.Add(self.row_dual_combo,pos=(2,1),flag=wx.EXPAND|wx.ALL,border=0)
        

        self.col_dual_label = wx.StaticText(self,wx.ID_ANY,label="Dual Affinity (Columns):")
        choices = [("Earth Mover Distance",run_quest.DUAL_EMD)]
        self.col_dual_combo = wx.ComboBox(self,wx.ID_ANY,choices=[],
                                                  style=wx.CB_READONLY)
        self.Bind(wx.EVT_COMBOBOX,self.on_opt_change,self.col_dual_combo)

        for (label,choice_id) in choices:
            self.col_dual_combo.Append(label,choice_id)
        
        self.col_dual_combo.SetSelection(0)
        
        self.gbs.Add(self.col_dual_label,pos=(3,0),flag=wx.ALL,border=0)
        self.gbs.Add(self.col_dual_combo,pos=(3,1),flag=wx.EXPAND|wx.ALL,border=0)

        self.row_param1_label = wx.StaticText(self,wx.ID_ANY,label="")
        self.row_param1_text = NumCtrl(self,wx.ID_ANY,fractionWidth=2,
                                       signedForegroundColour="Black",
                                       value=run_quest.DEFAULT_DUAL_ALPHA)
        self.row_param2_label = wx.StaticText(self,wx.ID_ANY,label="")
        self.row_param2_text = NumCtrl(self,wx.ID_ANY,fractionWidth=2,
                                       signedForegroundColour="Black",
                                       value=run_quest.DEFAULT_DUAL_BETA)

        self.gbs.Add(self.row_param1_label,pos=(2,2),flag=wx.ALL,border=0)
        self.gbs.Add(self.row_param1_text,pos=(2,3),flag=wx.EXPAND|wx.ALL,border=0)
        self.gbs.Add(self.row_param2_label,pos=(2,4),flag=wx.ALL,border=0)
        self.gbs.Add(self.row_param2_text,pos=(2,5),flag=wx.EXPAND|wx.ALL,border=0)

        self.col_param1_label = wx.StaticText(self,wx.ID_ANY,label="")
        self.col_param1_text = NumCtrl(self,wx.ID_ANY,fractionWidth=2,
                                       signedForegroundColour="Black",
                                       value=run_quest.DEFAULT_DUAL_ALPHA)
        self.col_param2_label = wx.StaticText(self,wx.ID_ANY,label="")
        self.col_param2_text = NumCtrl(self,wx.ID_ANY,fractionWidth=2,
                                       signedForegroundColour="Black",
                                       value=run_quest.DEFAULT_DUAL_BETA)

        self.gbs.Add(self.col_param1_label,pos=(3,2),flag=wx.ALL,border=0)
        self.gbs.Add(self.col_param1_text,pos=(3,3),flag=wx.EXPAND|wx.ALL,border=0)
        self.gbs.Add(self.col_param2_label,pos=(3,4),flag=wx.ALL,border=0)
        self.gbs.Add(self.col_param2_text,pos=(3,5),flag=wx.EXPAND|wx.ALL,border=0)

        self.iters_label = wx.StaticText(self,wx.ID_ANY,label="Iterations per set of Trees:")
        self.iters_text = NumCtrl(self,wx.ID_ANY,allowNegative=False,
                                  integerWidth=20,
                                  value=run_quest.DEFAULT_N_ITERS)
#                                  value=3)

        self.runs_label = wx.StaticText(self,wx.ID_ANY,label="Sets of Trees to Run:")
        self.runs_text = NumCtrl(self,wx.ID_ANY,allowNegative=False,
                                 integerWidth=20,
                                 value=run_quest.DEFAULT_N_TREES)
        
        self.gbs.Add(self.iters_label,pos=(4,0),flag=wx.ALL,border=0)
        self.gbs.Add(self.iters_text,pos=(4,1),flag=wx.EXPAND|wx.ALL,border=0)
        self.gbs.Add(self.runs_label,pos=(5,0),flag=wx.ALL,border=0)
        self.gbs.Add(self.runs_text,pos=(5,1),flag=wx.EXPAND|wx.ALL,border=0)

        self.sizer.Add(self.gbs,0,wx.EXPAND|wx.ALL,15)
        
        self.run_button = GenButton(self,wx.ID_ANY,'Run Questionnaire')
        self.Bind(wx.EVT_BUTTON,self.on_run,self.run_button)
        self.sizer.Add(self.run_button,0,wx.wx.ALL,15)
        
        self.SetSizer(self.sizer)
        
        self.on_opt_change(None)
        self.Layout()

    def on_run(self,evt):
        params = self.get_params()
        global_model.run_questionnaire(params)
        
    def on_run_select(self,message):
        params = global_model.selected_run.params
        self.set_params(params)

    def on_opt_change(self,evt):
        col_EMD = (self.col_dual_combo.GetSelection() == 0)
        row_EMD = (self.row_dual_combo.GetSelection() == 0)
        tree_binary = (self.tree_type_combo.GetSelection() == 0)
        tree_flexible = (self.tree_type_combo.GetSelection() == 1)
        init_aff_CS = (self.init_aff_combo.GetSelection() == 0)
        init_aff_Gaussian = (self.init_aff_combo.GetSelection() == 1)

        self.init_aff_param_label.SetLabel("")
        self.init_aff_param_text.Show(False)
        self.tree_param_label.SetLabel("")
        self.tree_param_text.Show(False)
        self.col_param1_label.SetLabel("")
        self.col_param2_label.SetLabel("")
        self.col_param1_text.Show(False)
        self.col_param2_text.Show(False)
        self.row_param1_label.SetLabel("")
        self.row_param2_label.SetLabel("")
        self.row_param1_text.Show(False)
        self.row_param2_text.Show(False)

        if col_EMD:
            self.col_param1_label.SetLabel("Alpha:")
            self.col_param2_label.SetLabel("Beta:")
            self.col_param1_text.Show(True)
            self.col_param2_text.Show(True)
        
        if row_EMD:
            self.row_param1_label.SetLabel("Alpha:")
            self.row_param2_label.SetLabel("Beta:")
            self.row_param1_text.Show(True)
            self.row_param2_text.Show(True)
        
        if tree_binary:
            self.tree_param_label.SetLabel("Balance Constant:")
            self.tree_param_text.Show(True)

        if tree_flexible:
            self.tree_param_label.SetLabel("Tree Constant:")
            self.tree_param_text.Show(True)

        if init_aff_CS:
            self.init_aff_param_label.SetLabel("Threshold:")
            self.init_aff_param_text.Show(True)

        if init_aff_Gaussian:
            self.init_aff_param_label.SetLabel("Epsilon:")
            self.init_aff_param_text.Show(True)
        
        self.Layout()

    def get_data(self,ctl):
        return ctl.GetClientData(ctl.GetSelection())

    def get_params(self):
        kwargs = {}
        init_aff_type = self.get_data(self.init_aff_combo)
        if init_aff_type == run_quest.INIT_AFF_COS_SIM:
            kwargs["threshold"] = float(self.init_aff_param_text.Value)
        elif init_aff_type == run_quest.INIT_AFF_GAUSSIAN:
            kwargs["epsilon"] = float(self.init_aff_param_text.Value)
            
        tree_type = self.get_data(self.tree_type_combo)
        if tree_type == run_quest.TREE_TYPE_BINARY:
            kwargs["bal_constant"] = float(self.tree_param_text.Value)
        elif tree_type == run_quest.TREE_TYPE_FLEXIBLE:
            kwargs["tree_constant"] = float(self.tree_param_text.Value)
        
        dual_row_type = self.get_data(self.row_dual_combo)
        if dual_row_type == run_quest.DUAL_EMD:
            kwargs["row_alpha"] = float(self.row_param1_text.Value)
            kwargs["row_beta"] = float(self.row_param2_text.Value)
        elif dual_row_type == run_quest.DUAL_GAUSSIAN:
            kwargs["row_epsilon"] = float(self.row_param1_text.Value)

        dual_col_type = self.get_data(self.col_dual_combo)
        if dual_col_type == run_quest.DUAL_EMD:
            kwargs["col_alpha"] = float(self.col_param1_text.Value)
            kwargs["col_beta"] = float(self.col_param2_text.Value)
        elif dual_col_type == run_quest.DUAL_GAUSSIAN:
            kwargs["col_epsilon"] = float(self.col_param1_text.Value)

        kwargs["n_iters"] = int(self.iters_text.Value)
        kwargs["n_trees"] = int(self.runs_text.Value)
        
        params = run_quest.PyQuestParams(init_aff_type,tree_type,dual_row_type,
                                         dual_col_type,**kwargs)
        
        return params
    
    def set_params(self,params):
        self.init_aff_combo.SetSelection(params.init_aff_type)
        if params.init_aff_type == run_quest.INIT_AFF_COS_SIM:
            self.init_aff_param_text.SetValue(params.init_aff_threshold)
        elif params.init_aff_type == run_quest.INIT_AFF_GAUSSIAN:
            self.init_aff_param_text.SetValue(params.init_aff_epsilon)
        
        self.tree_type_combo.SetSelection(params.tree_type)
        if params.tree_type == run_quest.TREE_TYPE_BINARY:
            self.tree_param_text.SetValue(params.tree_bal_constant)
        elif params.init_aff_type == run_quest.TREE_TYPE_FLEXIBLE:
            self.tree_param_text.SetValue(params.tree_constant)
        
        print params.row_affinity_type
        self.row_dual_combo.SetSelection(min(params.row_affinity_type,
                                             self.row_dual_combo.GetCount()-1))
        if params.row_affinity_type == run_quest.DUAL_EMD:
            self.row_param1_text.SetValue(params.row_alpha)
            self.row_param2_text.SetValue(params.row_beta)
        elif params.row_affinity_type == run_quest.DUAL_GAUSSIAN:
            self.row_param1_text.SetValue(params.row_epsilon)
        
        self.col_dual_combo.SetSelection(min(params.col_affinity_type,
                                             self.col_dual_combo.GetCount()-1))
        if params.col_affinity_type == run_quest.DUAL_EMD:
            self.col_param1_text.SetValue(params.col_alpha)
            self.col_param2_text.SetValue(params.col_beta)
        elif params.col_affinity_type == run_quest.DUAL_GAUSSIAN:
            self.col_param1_text.SetValue(params.col_epsilon)
        
        self.iters_text = params.n_iters
        self.runs_text = params.n_trees
        self.on_opt_change(None)
        
        self.Refresh()
                
class PyQuestDataPage(wx.Panel):
    def __init__(self,parent):
        wx.Panel.__init__(self,parent,wx.ID_ANY)
        Publisher.subscribe(self.update, "data.load")

        items = []

        self.shuffled = wx.CheckBox(self,wx.ID_ANY,label="Shuffled")
        self.Bind(wx.EVT_CHECKBOX,self.update,self.shuffled)
        items.append((self.shuffled,0,wx.ALL,10))
        
        self.means_label = wx.StaticText(self,wx.ID_ANY,"True Probability Field:")
        items.append((self.means_label,0,wx.EXPAND))

        self.data_view = ImagePlot(self, wx.ID_ANY, None, cmap, cnorm)
        items.append((self.data_view,1,wx.EXPAND|wx.ALIGN_LEFT))

        self.data_label = wx.StaticText(self,wx.ID_ANY,"Data Realization:")
        items.append((self.data_label,0,wx.EXPAND))

        self.realized_view = ImagePlot(self, wx.ID_ANY, None, bwmap, bwnorm)
        items.append((self.realized_view,1,wx.EXPAND))

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.AddMany(items)
        self.SetSizer(self.sizer)

        self.draw()
        self.Layout()

    def update(self,evt):
        Publisher.sendMessage("status.bar", "Updating data page...")
        self.draw()
        Publisher.sendMessage("status.bar","Ready.")

    def draw(self):
        row_order = global_model.row_order
        col_order = global_model.col_order
        true_data = global_model.true_data
        data = global_model.data
        
        if self.shuffled.Value and true_data is not None:
            disp_true_data = true_data[row_order,:][:,col_order]
        else:
            disp_true_data = true_data
        if self.shuffled.Value and data is not None:
            disp_data = data[row_order,:][:,col_order]
        else:
            disp_data = data

        if true_data is None:
            self.means_label.Show(False)
            self.data_view.Show(False)
        else:
            self.means_label.Show(True)
            self.data_view.data = disp_true_data
            self.data_view.draw()
            self.data_view.Show(True)

        if data is None:
            self.data_label.Show(False)
            self.realized_view.Show(False)
        else:
            self.data_label.Show(True)
            self.realized_view.data = disp_data
            self.realized_view.draw()
            self.realized_view.Show(True)
    
class PyQuestAffinityPage(wx.Panel):
    def __init__(self,parent):
        wx.Panel.__init__(self,parent,wx.ID_ANY)
        Publisher.subscribe(self.on_data_load, "data.load")
        Publisher.subscribe(self.on_row_aff_calc,"affinity.calc.row")
        Publisher.subscribe(self.on_col_aff_calc,"affinity.calc.col")
        Publisher.subscribe(self.row_tree_select,"rowtree.select")
        Publisher.subscribe(self.col_tree_select,"coltree.select")
        Publisher.subscribe(self.view_refresh,"view.refresh")

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.row_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.col_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.row_tree = None
        self.col_tree = None
        
        self.left_row_panel = wx.BoxSizer(wx.VERTICAL)
        self.left_col_panel = wx.BoxSizer(wx.VERTICAL)

        self.options_list = [run_quest.INIT_AFF_COS_SIM,
                             run_quest.INIT_AFF_GAUSSIAN,
                             run_quest.DUAL_EMD]
        
        options_txt_list = ["Cosine Similarity",
                            "Gaussian kernel/Euclidean",
                            "Earth Mover Distance"]

        color_options_list = ["Black/White","Red/Blue"]

        self.row_affinity_type = wx.RadioBox(self,wx.ID_ANY,choices=options_txt_list,
                                    label="Row Affinity",style=wx.RA_VERTICAL)
        self.Bind(wx.EVT_RADIOBOX,self.on_row_opt_change,self.row_affinity_type)
        
        self.row_params = wx.StaticBox(self,wx.ID_ANY,"Parameters")
        self.row_param_sizer = wx.StaticBoxSizer(self.row_params,wx.VERTICAL)
        
        self.row_gbs = wx.GridBagSizer(hgap=5,vgap=5)
        
        self.row_emd_alpha_label = wx.StaticText(self,wx.ID_ANY,label="Alpha:")
        self.row_emd_alpha_text = NumCtrl(self,wx.ID_ANY,fractionWidth=2,signedForegroundColour="Black",value=1.0)
        self.row_emd_beta_label = wx.StaticText(self,wx.ID_ANY,label="Beta:")
        self.row_emd_beta_text = NumCtrl(self,wx.ID_ANY,fractionWidth=2,signedForegroundColour="Black",value=1.0)
        self.row_threshold_label = wx.StaticText(self,wx.ID_ANY,label="Threshold:")
        self.row_threshold_text = NumCtrl(self,wx.ID_ANY,fractionWidth=2,signedForegroundColour="Black",value=0.1)

        self.row_gbs.Add(self.row_emd_alpha_label,(0,0))
        self.row_gbs.Add(self.row_emd_alpha_text,(0,1))
        self.row_gbs.Add(self.row_emd_beta_label,(1,0))
        self.row_gbs.Add(self.row_emd_beta_text,(1,1))
        self.row_gbs.Add(self.row_threshold_label,(2,0))
        self.row_gbs.Add(self.row_threshold_text,(2,1))
        self.row_gbs.SetEmptyCellSize((0,0))

        self.row_param_sizer.Add(self.row_gbs,0)

        self.btn_calc_row = GenButton(self,wx.ID_ANY,"Calculate row affinity",
                                      style=wx.BORDER_RAISED)
        self.Bind(wx.EVT_BUTTON,self.recalc_row_click,self.btn_calc_row)

        self.row_color_type = wx.RadioBox(self,wx.ID_ANY,
                                          choices=color_options_list,
                                          label="Color",style=wx.RA_HORIZONTAL)
        self.Bind(wx.EVT_RADIOBOX,self.on_color_change,self.row_color_type)

        self.left_row_panel.Add(self.row_affinity_type,0,wx.TOP,5)
        self.left_row_panel.Add(self.row_param_sizer,0,wx.TOP,5)
        self.left_row_panel.Add(self.row_color_type,0,wx.TOP,5)
        self.left_row_panel.Add(self.btn_calc_row,0,wx.ALIGN_CENTER_HORIZONTAL)
        
        self.row_sizer.Add(self.left_row_panel,1)
        
        self.row_affinity_view = ImagePlot(self, wx.ID_ANY, None, bwmap, bwnorm)
        self.row_sizer.Add(self.row_affinity_view,4,flag=wx.EXPAND)

        self.col_affinity_type = wx.RadioBox(self,wx.ID_ANY,choices=options_txt_list,
                                     label="Column Affinity",style=wx.RA_VERTICAL)
        self.Bind(wx.EVT_RADIOBOX,self.on_col_opt_change,self.col_affinity_type)

        self.col_color_type = wx.RadioBox(self,wx.ID_ANY,
                                          choices=color_options_list,
                                          label="Color",style=wx.RA_HORIZONTAL)
        self.Bind(wx.EVT_RADIOBOX,self.on_color_change,self.col_color_type)

        self.col_params = wx.StaticBox(self,wx.ID_ANY,"Parameters")
        self.col_param_sizer = wx.StaticBoxSizer(self.col_params,wx.VERTICAL)
        
        self.col_gbs = wx.GridBagSizer()
        
        self.col_emd_alpha_label = wx.StaticText(self,wx.ID_ANY,label="Alpha:")
        self.col_emd_alpha_text = NumCtrl(self,wx.ID_ANY,fractionWidth=2,signedForegroundColour="Black",value=1.0)
        self.col_emd_beta_label = wx.StaticText(self,wx.ID_ANY,label="Beta:")
        self.col_emd_beta_text = NumCtrl(self,wx.ID_ANY,fractionWidth=2,signedForegroundColour="Black",value=1.0)
        self.col_threshold_label = wx.StaticText(self,wx.ID_ANY,label="Threshold:")
        self.col_threshold_text = NumCtrl(self,wx.ID_ANY,fractionWidth=2,signedForegroundColour="Black",value=0.1)

        self.col_gbs.Add(self.col_emd_alpha_label,(0,0))
        self.col_gbs.Add(self.col_emd_alpha_text,(0,1))
        self.col_gbs.Add(self.col_emd_beta_label,(1,0))
        self.col_gbs.Add(self.col_emd_beta_text,(1,1))
        self.col_gbs.Add(self.col_threshold_label,(2,0))
        self.col_gbs.Add(self.col_threshold_text,(2,1))
        self.col_gbs.SetEmptyCellSize((0,0))

        self.col_param_sizer.Add(self.col_gbs,0)

        self.btn_calc_col = GenButton(self,wx.ID_ANY,"Calculate col affinity",
                                      style=wx.BORDER_RAISED)
        self.Bind(wx.EVT_BUTTON,self.recalc_col_click,self.btn_calc_col)

        self.left_col_panel.Add(self.col_affinity_type,0,wx.TOP,5)
        self.left_col_panel.Add(self.col_param_sizer,0,wx.TOP,5)
        self.left_col_panel.Add(self.col_color_type,0,wx.TOP,5)
        self.left_col_panel.Add(self.btn_calc_col,0,wx.ALIGN_CENTER_HORIZONTAL)
        self.col_sizer.Add(self.left_col_panel,1)

        self.col_affinity_view = ImagePlot(self, wx.ID_ANY, None, bwmap, bwnorm)
        self.col_sizer.Add(self.col_affinity_view,4,wx.EXPAND)

        self.sizer.Add(self.row_sizer,1,wx.EXPAND)
        self.sizer.Add(self.col_sizer,1,wx.EXPAND)
        self.SetSizer(self.sizer)
        
        self.show_params()
        self.Layout()
        
    def show_params(self):
        row_aff_type = self.options_list[self.row_affinity_type.GetSelection()]
        col_aff_type = self.options_list[self.col_affinity_type.GetSelection()]
        if row_aff_type == run_quest.INIT_AFF_COS_SIM:
            self.row_emd_alpha_label.Show(False)
            self.row_emd_alpha_text.Show(False)
            self.row_emd_beta_label.Show(False)
            self.row_emd_beta_text.Show(False)
            self.row_threshold_label.Show(True)
            self.row_threshold_text.Show(True)
        if row_aff_type == run_quest.DUAL_EMD:
            self.row_emd_alpha_label.Show(True)
            self.row_emd_alpha_text.Show(True)
            self.row_emd_beta_label.Show(True)
            self.row_emd_beta_text.Show(True)
            self.row_threshold_label.Show(False)
            self.row_threshold_text.Show(False)
        if col_aff_type == run_quest.INIT_AFF_COS_SIM:
            self.col_emd_alpha_label.Show(False)
            self.col_emd_alpha_text.Show(False)
            self.col_emd_beta_label.Show(False)
            self.col_emd_beta_text.Show(False)
            self.col_threshold_label.Show(True)
            self.col_threshold_text.Show(True)
        if col_aff_type == run_quest.DUAL_EMD:
            self.col_emd_alpha_label.Show(True)
            self.col_emd_alpha_text.Show(True)
            self.col_emd_beta_label.Show(True)
            self.col_emd_beta_text.Show(True)
            self.col_threshold_label.Show(False)
            self.col_threshold_text.Show(False)
        if global_model.data is None:
            self.btn_calc_col.Disable()
            self.btn_calc_row.Disable()
        else:
            self.btn_calc_col.Enable()
            self.btn_calc_row.Enable()
        self.Layout()
        self.Refresh()
    
    def view_refresh(self,message):
        self.row_affinity_view.draw()
        self.col_affinity_view.draw()

    def on_data_load(self,message):
        self.data = global_model.data
        self.show_params()

    def recalc_col_click(self,evt):
        self.recalc("col")

    def recalc_row_click(self,evt):
        self.recalc("row")

    def row_tree_select(self,message):
        self.row_tree = global_model.row_tree

    def col_tree_select(self,message):
        self.col_tree = global_model.col_tree

    def recalc(self,direction):
        Publisher.sendMessage("status.bar", "Updating affinity page...")
        if direction == "row":
            row_aff_type = self.options_list[self.row_affinity_type.GetSelection()]
            if row_aff_type == run_quest.DUAL_EMD:
                if self.col_tree is None:
                    Publisher.sendMessage("status.bar", 
                                      "Must select column tree for row EMD.")
                    return
                else:
                    alpha = float(self.row_emd_alpha_text.Value)
                    beta = float(self.row_emd_beta_text.Value)
                    global_model.calc_row_affinity(row_aff_type,row_tree=self.col_tree,
                                                 alpha=alpha,beta=beta)
            elif row_aff_type == run_quest.INIT_AFF_COS_SIM:
                threshold = float(self.row_threshold_text.Value)
                global_model.calc_row_affinity(row_aff_type,threshold=threshold)
            else:
                global_model.calc_row_affinity(row_aff_type)
        elif direction == "col":
            col_aff_type = self.col_affinity_type.GetSelection()
            if col_aff_type == run_quest.DUAL_EMD:
                if self.col_tree is None:
                    Publisher.sendMessage("status.bar", 
                                      "Must select row tree for col EMD.")
                else:
                    alpha = float(self.col_emd_alpha_text.Value)
                    beta = float(self.col_emd_beta_text.Value)
                    global_model.calc_col_affinity(col_aff_type,row_tree=self.row_tree,
                                                 alpha=alpha,beta=beta)
            elif col_aff_type == run_quest.INIT_AFF_COS_SIM:
                threshold = float(self.col_threshold_text.Value)
                global_model.calc_col_affinity(col_aff_type,threshold=threshold)
            else:
                global_model.calc_col_affinity(col_aff_type)
        self.show_params()
        Publisher.sendMessage("status.bar", "Done.")

    def on_row_aff_calc(self,message):
        self.row_affinity_view.data = global_model.row_affinity
        self.row_affinity_view.draw()

    def on_col_aff_calc(self,message):
        self.col_affinity_view.data = global_model.col_affinity
        self.col_affinity_view.draw()

    def on_row_opt_change(self,evt):
        self.show_params()

    def on_col_opt_change(self,evt):
        self.show_params()
    
    def on_color_change(self,evt):
        if self.col_color_type.GetSelection() == 0:
            self.col_affinity_view.set_cmap(bwmap)
        if self.col_color_type.GetSelection() == 1:
            self.col_affinity_view.set_cmap(cmap)
        if self.row_color_type.GetSelection() == 0:
            self.row_affinity_view.set_cmap(bwmap)
        if self.row_color_type.GetSelection() == 1:
            self.row_affinity_view.set_cmap(cmap)
        self.row_affinity_view.draw()
        self.col_affinity_view.draw()

class PyQuestTreePage(wx.Panel):
    def __init__(self,parent,tree_title,tree_id=""):
        wx.Panel.__init__(self,parent,wx.ID_ANY)
        
        Publisher.subscribe(self.tree_select,tree_id+".select")
        Publisher.subscribe(self.node_select,tree_id+".node.select")
        Publisher.subscribe(self.tree_select,"view.refresh")
        
        self.title = tree_title
        self.tree_id = tree_id
        self.tree = None
        self.tree_plot = TreePanel(self,wx.ID_ANY,self.title,self.tree_id)
        self.recreate()
        
    def node_select(self,message):
        if self.tree is None:
            return
        if self.data.data_type == "descs":
            self.folder_label = u''
            for element in self.tree[global_model.tree_node(self.tree_id)].elements:
                self.folder_label += self.data.data[element] + "\n"
            self.row_data.SetValue(self.folder_label)
        self.Refresh()
        
    def tree_select(self,message):
        Publisher.sendMessage("status.bar", "Updating tree panel...")
        self.tree = global_model.tree(self.tree_id)
        self.data = global_model.tree_data(self.tree_id)
        self.recreate()
        global_model.node_select(self.tree_id,0)
        Publisher.sendMessage("status.bar", "Ready.")

    def recreate(self):
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.tree_plot,4,wx.EXPAND)
        if self.tree is not None:
            print self.data.data_type
            if self.data.data_type == "descs":
                self.row_data = wx.TextCtrl(self,wx.ID_ANY,
                                        style=wx.TE_MULTILINE|wx.TE_READONLY)
                self.sizer.Add(self.row_data,1,wx.EXPAND|wx.ALL,10)
            elif self.data.data_type == "scores":
                self.col_data = wx.StaticText(self,wx.ID_ANY,
                                        label="placeholder for score graph")
                self.sizer.Add(self.col_data,1,wx.EXPAND|wx.ALL,10)
        
        self.SetSizer(self.sizer)
        self.Layout()
        
class PyQuestEmbedPage(wx.Panel):
    def __init__(self,parent,embed_title="Embedding",topic=""):
        wx.Panel.__init__(self,parent,wx.ID_ANY)
        Publisher.subscribe(self.on_calc,topic+".calc")
        Publisher.subscribe(self.on_avg_calc,topic+".avg")
        Publisher.subscribe(self.on_node_select,"rowtree.node.select")
        Publisher.subscribe(self.on_node_select,"coltree.node.select")
        Publisher.subscribe(self.on_calc,"view.refresh")
        self.topic = topic
        self.vecs = None
        self.vals = None
        self.avgs = None

        self.embed_title = embed_title
        
        self.left_panel_sizer = wx.BoxSizer(wx.VERTICAL)
        self.tree_panel_sizer = wx.BoxSizer(wx.VERTICAL)
        self.param_sizer = wx.GridBagSizer(hgap=5,vgap=5)
        
        self.diff_time_label = wx.StaticText(self,wx.ID_ANY,label="Diffusion time:")
        self.diff_time_text = NumCtrl(self,wx.ID_ANY,fractionWidth=2,signedForegroundColour="Black",value=1.0)

        self.Bind(wx.lib.masked.EVT_NUM,self.on_diff_time,self.diff_time_text)
        
        self.x_vec_label = wx.StaticText(self,wx.ID_ANY,label="X Vector:")
        self.y_vec_label = wx.StaticText(self,wx.ID_ANY,label="Y Vector:")
        self.z_vec_label = wx.StaticText(self,wx.ID_ANY,label="Z Vector:")
        
        self.x_vec = wx.SpinCtrl(self,value="2",min=2,max=2)
        self.y_vec = wx.SpinCtrl(self,value="3",min=2,max=3)
        self.z_vec = wx.SpinCtrl(self,value="4",min=2,max=4)
        self.Bind(wx.EVT_SPINCTRL,self.on_spin,self.x_vec)
        self.Bind(wx.EVT_SPINCTRL,self.on_spin,self.y_vec)
        self.Bind(wx.EVT_SPINCTRL,self.on_spin,self.z_vec)
        
        self.folder_checkbox = wx.CheckBox(self,wx.ID_ANY,label="Highlight selected folder")
        self.Bind(wx.EVT_CHECKBOX,self.on_folder,self.folder_checkbox)

        color_options_list = ["Average Response",
                        "Difference from Parent",
                        "Color by Folder"]

        self.color_type = wx.RadioBox(self,wx.ID_ANY,choices=color_options_list,
                                    label="Color Options",style=wx.RA_VERTICAL)
        self.Bind(wx.EVT_RADIOBOX,self.on_color_type,self.color_type)

        self.param_sizer.Add(self.diff_time_label,(0,0))
        self.param_sizer.Add(self.diff_time_text,(0,1))
        self.param_sizer.Add(self.x_vec_label,(1,0))
        self.param_sizer.Add(self.y_vec_label,(2,0))
        self.param_sizer.Add(self.z_vec_label,(3,0))
        self.param_sizer.Add(self.x_vec,(1,1))
        self.param_sizer.Add(self.y_vec,(2,1))
        self.param_sizer.Add(self.z_vec,(3,1))
        
        self.row_tree_panel = TreePanel(self,wx.ID_ANY,"Row Tree","rowtree")
        self.col_tree_panel = TreePanel(self,wx.ID_ANY,"Column Tree","coltree")

        self.left_panel_sizer.Add(self.param_sizer,0,wx.ALL,5)
        self.left_panel_sizer.Add(self.color_type,0,wx.ALL,5)
        self.left_panel_sizer.Add(self.folder_checkbox,0,wx.ALL,5)
        
        self.tree_panel_sizer.Add(self.row_tree_panel,1,wx.EXPAND,5)
        self.tree_panel_sizer.Add(self.col_tree_panel,1,wx.EXPAND,5)
        
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.embed_plot = EmbedPlot(self,wx.ID_ANY,None,None,embed_title=embed_title)
        
        self.sizer.Add(self.left_panel_sizer,1,wx.EXPAND|wx.ALL,10)
        self.sizer.Add(self.tree_panel_sizer,2,wx.EXPAND|wx.ALL,10)
        self.sizer.Add(self.embed_plot,4,wx.EXPAND)

        self.SetSizer(self.sizer)
        self.Layout()
    
    def on_calc(self,message):
        Publisher.sendMessage("status.bar", "Updating embedding...")
        vecs = global_model.vecs(self.topic)
        vals = global_model.vals(self.topic)
        n_vecs = len(vals)
        self.x_vec.SetRange(2,n_vecs)
        self.y_vec.SetRange(2,n_vecs)
        self.z_vec.SetRange(2,n_vecs)
        self.on_color_type(None)
        
        self.embed_plot.update(vecs=vecs,vals=vals)
    
    def on_folder(self,evt):
        self.calc_edgecolors()

    def calc_edgecolors(self):
        if global_model.vecs(self.topic) is None:
            return
        
        edgecolors = ['none']*global_model.vecs(self.topic).shape[0]
        s = [20]*global_model.vecs(self.topic).shape[0]
        if self.folder_checkbox.GetValue():
            if self.topic.endswith("row"):
                t = self.row_tree_panel.tree[global_model.tree_node("rowtree")]
            elif self.topic.endswith("col"):
                t = self.col_tree_panel.tree[global_model.tree_node("coltree")]
            for idx in t.elements:
                edgecolors[idx] = "k"
                s[idx] = 40
        self.embed_plot.update(s=s,edgecolors=edgecolors)
            
    def on_diff_time(self,evt):
        self.embed_plot.update(diff_t=float(self.diff_time_text.Value))
        
    def on_spin(self,evt):
        self.embed_plot.update(x_vec=self.x_vec.Value-1,y_vec=self.y_vec.Value-1,
                               z_vec=self.z_vec.Value-1)
    def on_color_type(self,evt):
        color_type = self.color_type.GetSelection()
        #print "updating color type to {}".format(color_type)
        
        if color_type == 0: #average response
            if self.topic.endswith("row"):
                global_model.calc_avg_val_rows(global_model.tree("rowtree"),
                                               global_model.tree("coltree"))
            elif self.topic.endswith("col"):
                global_model.calc_avg_val_cols(global_model.tree("rowtree"),
                                               global_model.tree("coltree"))
        elif color_type == 1: #difference from parent
            if self.topic.endswith("row"):
                global_model.calc_avg_val_rows(global_model.tree("rowtree"),
                                               global_model.tree("coltree"))
            elif self.topic.endswith("col"):
                global_model.calc_avg_val_cols(global_model.tree("rowtree"),
                                               global_model.tree("coltree"))
        else:
            self.calc_c()

    def on_avg_calc(self,message):
        self.avgs = global_model.tree_avgs(self.topic)
        self.calc_c()

    def calc_c(self):
        color_type = self.color_type.GetSelection()
        row_level = self.row_tree_panel.tree[global_model.tree_node("rowtree")].level-1
        col_level = self.col_tree_panel.tree[global_model.tree_node("coltree")].level-1
        if color_type == 0:
            if self.topic.endswith("row"):
                c = self.avgs[:,row_level,global_model.tree_node("coltree")]
            elif self.topic.endswith("col"):
                c = self.avgs[:,col_level,global_model.tree_node("rowtree")]
        elif color_type == 1:
            if self.topic.endswith("row"):
                if row_level == 0:
                    c = self.avgs[:,row_level,global_model.tree_node("coltree")]
                else:
                    c = (self.avgs[:,row_level,global_model.tree_node("coltree")] - 
                        self.avgs[:,row_level-1,global_model.tree_node("coltree")]) 
            elif self.topic.endswith("col"):
                if col_level == 0:
                    c = self.avgs[:,col_level,global_model.tree_node("rowtree")]
                else:
                    c = (self.avgs[:,col_level,global_model.tree_node("rowtree")] - 
                         self.avgs[:,col_level-1,global_model.tree_node("rowtree")])
        elif color_type == 2:
            COLORS = "bgrcmyk"
            if self.topic.endswith("row"):
                c = [COLORS[x % len(COLORS)] for x in 
                     global_model.tree("rowtree").level_partition(row_level+1)]
            elif self.topic.endswith("col"):
                c = [COLORS[x % len(COLORS)] for x in 
                     global_model.tree("coltree").level_partition(col_level+1)]
                
        self.embed_plot.update(c=c)

    def on_node_select(self,evt):
        if self.avgs is None:
            pass
        else:
            self.calc_c()
            self.calc_edgecolors()
        
class TreePanel(wxplot_util.PlotPanel):
    def __init__(self,parent,obj_id,tree_title,tree_id):
        wxplot_util.PlotPanel.__init__(self,parent,obj_id)
        self.title = tree_title
        self.tree_id = tree_id
        self.tree = global_model.tree(tree_id)
        self.selected_node = global_model.tree_node(tree_id)
        self.calculate()
        self.init_draw()
        Publisher.subscribe(self.on_node_select,tree_id+".node.select")
        Publisher.subscribe(self.on_tree_select,tree_id+".select")

        self.click_id = self.canvas.mpl_connect("button_release_event", self.on_click)
        self.key_id = self.canvas.mpl_connect("key_release_event", self.on_key)

    def on_tree_select(self,message):
        self.tree = global_model.tree(self.tree_id)
        self.calculate()
        self.init_draw()

    def on_node_select(self,message):
        self.selected_node = global_model.tree_node(self.tree_id)
        self.draw()

    def calculate(self):
        if self.tree is None:
            return
        #calculate the node locations
        self.node_locs = np.zeros([self.tree.tree_size,2])
        self.node_order = []

        for level in xrange(1,self.tree.tree_depth+1):
            nodes = self.tree.dfs_level(level)
            self.node_order.extend([x.idx for x in nodes])
            node_idxs = np.array([node.idx for node in nodes])
            x_intervals = np.cumsum(np.array([0]+[node.size for node in nodes])*1.0/self.tree.size)
            node_xs = x_intervals[:-1] + np.diff(x_intervals)/2.0
            node_ys = (self.tree.tree_depth - level)*np.ones(np.shape(node_xs))
            self.node_locs[node_idxs,:] = np.hstack([node_xs[:,np.newaxis],node_ys[:,np.newaxis]])

    def init_draw(self):
        self.figure.clear()
        self.ax = self.figure.add_subplot(111)
        self.ax.set_title(self.title)
        if self.tree is not None:
            self.ax.scatter(self.node_locs[:,0],self.node_locs[:,1],marker='.',color='b',s=40)
            for node in self.tree.traverse():
                if node.parent is not None:
                    x1,y1 = self.node_locs[node.idx,:]
                    x2,y2 = self.node_locs[node.parent.idx,:]
                    self.ax.plot((x1,x2),(y1,y2),'r')
            self.ax.set_xlim([0.0,1.0])
            self.ax.set_ylim([-0.2,self.tree.tree_depth + 0.2])
            x1,y1 = self.node_locs[self.selected_node,:]
            self.marker = self.ax.plot(x1,y1,'s',markersize=6,markerfacecolor='None',markeredgecolor='k',markeredgewidth=2)
        self.canvas.draw()
                                    
    def draw(self):
        if self.tree is None:
            self.init_draw()
        else:
            self.ax.lines.remove(self.marker[0])
            x1,y1 = self.node_locs[self.selected_node,:]
            self.marker = self.ax.plot(x1,y1,'s',markersize=6,markerfacecolor='None',markeredgecolor='k',markeredgewidth=2)
            self.canvas.draw()
    
    def on_key(self,evt):
        if evt.key == "w":
            node = [x for x in self.tree if x.idx == self.selected_node]
            if node[0].parent is not None:
                self.selected_node = node[0].parent.idx
                global_model.node_select(self.tree_id,self.selected_node)
        if evt.key == "s":
            node = [x for x in self.tree if x.idx == self.selected_node]
            if node[0].children != []:
                self.selected_node = node[0].children[0].idx
                global_model.node_select(self.tree_id,self.selected_node)
        if evt.key == "d":
            node = self.selected_node
            idx = self.node_order.index(node)
            if idx == self.tree.tree_size-1:
                return
            if self.tree[idx].level != self.tree[idx+1].level:
                return
            self.selected_node = self.node_order[idx+1]
            global_model.node_select(self.tree_id,self.selected_node)
        if evt.key == "a":
            node = self.selected_node
            idx = self.node_order.index(node)
            if idx == 0:
                return
            if self.tree[idx].level != self.tree[idx-1].level:
                return
            self.selected_node = self.node_order[idx-1]
            global_model.node_select(self.tree_id,self.selected_node)
        
    def on_click(self,evt):
        if evt.xdata is None or evt.ydata is None:
            pass
        else:
            click_loc = np.array([evt.xdata,evt.ydata])
            distances = np.sum((self.node_locs - click_loc)**2,axis=1)
            self.selected_node = np.argmin(distances)
            global_model.node_select(self.tree_id,self.selected_node)

class EmbedPlot(wxplot_util.PlotPanel):
    def __init__(self,parent,obj_id,vecs,vals,x_vec=1,y_vec=2,z_vec=3,diff_t=1,
                 c=None,s=None,tree_level=1,embed_title="Embedding",edgecolors='none'):
        wxplot_util.PlotPanel.__init__(self,parent,obj_id)
        self.update(vecs=vecs,vals=vals,x_vec=x_vec,y_vec=y_vec,z_vec=z_vec,
                    diff_t=diff_t,c=None,s=None,tree_level=tree_level,
                    embed_title=embed_title,edgecolors=edgecolors)

    def draw(self):
        self.figure.clear()
        if self.vecs is None:
            return
        
        if self.diff_t <= 0: 
            self.diff_t = 1.0/(1-self.vals[1])
        
        x=self.vecs[:,self.x_vec] * (self.vals[self.x_vec] ** self.diff_t)
        y=self.vecs[:,self.y_vec] * (self.vals[self.y_vec] ** self.diff_t)
        z=self.vecs[:,self.z_vec] * (self.vals[self.z_vec] ** self.diff_t)

        if self.c is None:
            self.c = "b"
        if self.s is None:
            self.s = 20

        if hasattr(self,"ax"):
            old_elev,old_azim = self.ax.elev,self.ax.azim
        else:
            old_elev,old_azim = None,None

        self.ax = self.figure.add_subplot(111,projection="3d")
        self.ax.set_title(self.embed_title)

        self.ax.scatter3D(x,y,z,c=self.c,cmap=cmap,norm=cnorm,
                          edgecolors=self.edgecolors,s=self.s,linewidth=2)
        self.ax.view_init(old_elev,old_azim)
        
        self.canvas.draw()

    def update(self,**kwargs):
        if "vecs" in kwargs:
            self.vecs = kwargs["vecs"]
        if "vals" in kwargs:
            self.vals = kwargs["vals"]
        if "x_vec" in kwargs:
            self.x_vec = kwargs["x_vec"]
        if "y_vec" in kwargs:
            self.y_vec = kwargs["y_vec"]
        if "z_vec" in kwargs:
            self.z_vec = kwargs["z_vec"]
        if "diff_t" in kwargs:
            self.diff_t = kwargs["diff_t"]
        if "c" in kwargs:
            self.c = kwargs["c"]
        if "embed_title" in kwargs:
            self.embed_title = kwargs["embed_title"]
        if "edgecolors" in kwargs:
            self.edgecolors = kwargs["edgecolors"]
        if "s" in kwargs:
            self.s = kwargs["s"]
        self.draw()
        
class ImagePlot(wxplot_util.PlotPanel):
    def __init__(self,parent,obj_id,data,cmap=None,norm=None):
        wxplot_util.PlotPanel.__init__(self,parent,obj_id)
        self.data = data
        if cmap is not None:
            self.cmap = cmap
        if norm is not None:
            self.norm = norm
    
    def set_data(self,data):
        self.data = data
    
    def set_norm(self,norm):
        self.norm = norm

    def set_cmap(self,cmap):
        self.cmap = cmap
    
    def draw(self):
        self.figure.clear()
        self.ax = self.figure.add_subplot(111)
        if self.data is None:
            return
        else:
            self.ax.imshow(self.data,interpolation='nearest',aspect='auto',
                           cmap=self.cmap,norm=self.norm)
            self.canvas.draw()
            #self.figure.subplots_adjust(left=0.0,right=1.0,top=1.0,bottom=0.0)
            #self.figure.tight_layout()

if __name__ == "__main__":
    global_model = pyquest_M.PyQuestDataModel()
    app = PyQuestApp()
    app.MainLoop()
    
