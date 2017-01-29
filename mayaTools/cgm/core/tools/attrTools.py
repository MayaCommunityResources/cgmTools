"""
------------------------------------------
attrTools: cgm.core
Author: Josh Burton
email: jjburton@cgmonks.com

Website : http://www.cgmonks.com
------------------------------------------
2.0 rewrite
================================================================
"""
# From Python =============================================================
import copy
import re

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


import maya.cmds as mc


import cgm.core.classes.GuiFactory as cgmUI
reload(cgmUI)
mUI = cgmUI.mUI

from cgm.core.lib import shared_data as SHARED
from cgm.core.lib import search_utils as SEARCH
from cgm.core.lib import name_utils as NAMES
from cgm.core.cgmPy import validateArgs as VALID
from cgm.core import cgm_General as cgmGEN
from cgm.core import cgm_Meta as cgmMeta
from cgm.core.lib import attribute_utils as ATTR
from cgm.core.lib import list_utils as LISTS
reload(SEARCH)
#>>> Root settings =============================================================
__version__ = 'Alpha 2.0.01262017'

#__toolURL__ = 'www.cgmonks.com'
#__author__ = 'Josh Burton'
#__owner__ = 'CG Monks'
#__website__ = 'www.cgmonks.com'
#__defaultSize__ = 375, 350



class uiWin_addAttr(cgmUI.cgmGUI):
    USE_Template = 'cgmUITemplate'
    WINDOW_NAME = 'cgmAddAttr_ui'    
    WINDOW_TITLE = 'cgmAddAttr - {0}'.format(__version__)
    DEFAULT_MENU = None
    RETAIN = True
    MIN_BUTTON = True
    MAX_BUTTON = False
    FORCE_DEFAULT_SIZE = True  #always resets the size of the window when its re-created  
    DEFAULT_SIZE = 375,150
    
    def insert_init(self,*args,**kws):
            if kws:log.debug("kws: %s"%str(kws))
            if args:log.debug("args: %s"%str(args))
            log.info(self.__call__(q=True, title=True))
    
            self.description = 'Tool to add attributes'
            self.__version__ = __version__
            self.__toolName__ = 'cgmAddAttr'		
            self.l_allowedDockAreas = []
            self.WINDOW_TITLE = uiWin_addAttr.WINDOW_TITLE
            #self.DEFAULT_SIZE = __defaultSize__

    def buildMenu_help( self, *args):
            self.uiMenu_HelpMenu.clear()
            mUI.MelMenuItem( self.uiMenu_HelpMenu, l="Show Help",
                             cb=self.var_ShowHelp.value,
                             c= lambda *a: self.do_showHelpToggle())

    def build_menus(self):pass#...don't want em  
    
    def build_layoutWrapper(self,parent):
        _str_func = 'build_layoutWrapper'
        _MainForm = mUI.MelColumnLayout(parent)
        cgmUI.add_Header('Create')
        cgmUI.add_LineSubBreak()

        #>>>Create Row ---------------------------------------------------------------------------------------
        _row_attrCreate = mUI.MelHSingleStretchLayout(_MainForm,ut='cgmUISubTemplate',padding = 5)
        mUI.MelSpacer(_row_attrCreate)
    
        mUI.MelLabel(_row_attrCreate,l='Names:',align='right')
        self.AttrNamesTextField = mUI.MelTextField(_row_attrCreate,backgroundColor = [1,1,1],h=20,
                                                   #ec = lambda *a: attrToolsLib.doAddAttributesToSelected(self),
                                                   annotation = "Names for the attributes. Create multiple with a ','. \n Message nodes try to connect to the last object in a selection \n For example: 'Test1;Test2;Test3'")
        cgmUI.add_Button(_row_attrCreate,'Add',
                             #lambda *a: attrToolsLib.doAddAttributesToSelected(self),
                             "Add the attribute names from the text field")
        mUI.MelSpacer(_row_attrCreate,w=2)
    
        _row_attrCreate.setStretchWidget(self.AttrNamesTextField)
        _row_attrCreate.layout()  
        
        uiRow_attributeTypes(self,_MainForm)

        log.info("|{0}| >> Selected: {1}".format(_str_func, self.rc_attrTypes.getSelectedIndex()))
        
        
class uiWin_multiSetAttr(cgmUI.cgmGUI):
    USE_Template = 'cgmUITemplate'
    WINDOW_NAME = 'cgmMultiSetAttr_ui'    
    WINDOW_TITLE = 'cgmMultiSetAttr - {0}'.format(__version__)
    DEFAULT_MENU = None
    RETAIN = True
    MIN_BUTTON = True
    MAX_BUTTON = False
    FORCE_DEFAULT_SIZE = True  #always resets the size of the window when its re-created  
    DEFAULT_SIZE = 375,250
    _checkBoxKeys = ['shared','regular','user','numeric']
    
    def insert_init(self,*args,**kws):
            if kws:log.debug("kws: %s"%str(kws))
            if args:log.debug("args: %s"%str(args))
            log.info(self.__call__(q=True, title=True))
    
            self.__version__ = __version__
            self.__toolName__ = 'cgmMultiSet'		
            #self.l_allowedDockAreas = []
            self.WINDOW_TITLE = uiWin_multiSetAttr.WINDOW_TITLE
            self.DEFAULT_SIZE = uiWin_multiSetAttr.DEFAULT_SIZE
            self._d_attrs = {}
            self._ml_nodes = []
            self.uiPopUpMenu_attr = False

    def build_menus(self):
        self.uiMenu_HelpMenu = mUI.MelMenu( l='Help', pmc=self.buildMenu_help)           
        #pass#...don't want em  
    #def setup_Variables(self):pass
    
        
    def uiFunc_clear_loaded(self):
        _str_func = 'uiFunc_clear_loaded'  
        self._d_attrs = {}
        self._ml_nodes = []
           
        self.uiReport_objects()
        self.uiScrollList_attr.clear()
        self._d_uiCheckBoxes['shared'](edit = True, en=True)
        
    def uiFunc_report_loaded(self):
        _str_func = 'cgmMultiSetAttr'  
        
        if not self._ml_nodes:
            log.info("|{0}| >> No objects loaded".format(_str_func))
        else:
            log.info("|{0}| >> Loaded...".format(_str_func))            
            
            for i,mObj in enumerate(self._ml_nodes):
                _short = mObj.p_nameShort
                log.info("|{0}| >> {1} : {2} | attrs: {3}...".format(_str_func,i,_short, len(self._d_attrs[_short])))
    
    def uiFunc_load_selected(self):
        _str_func = 'uiFunc_load_selected'  
        self._d_attrs = {}
        self._ml_nodes = []
        
        _sel = mc.ls(sl=True)
        
        #Get our raw data
        for o in _sel:
            _type = VALID.get_mayaType(o)
            if VALID.is_transform(o) or VALID.is_shape(o):
                mNode = cgmMeta.validateObjArg(o)
                self._ml_nodes.append( mNode )
                _short = mNode.p_nameShort
                log.info("|{0}| >> Good obj: {1}".format(_str_func, _short))
                self._d_attrs[_short] = mc.listAttr(_short)
            else:
                log.info("|{0}| >> Bad obj: {1}".format(_str_func, NAMES.get_short(o)))
                
        if len(self._ml_nodes) < 2:
            self._d_uiCheckBoxes['shared'](edit = True, en=False)
        else:
            self._d_uiCheckBoxes['shared'](edit = True, en=True)    
        self.uiReport_objects()
        self.uiFunc_updateScrollAttrList()

    def uiFunc_updateScrollAttrList(self):
        _str_func = 'uiFunc_updateScrollAttrList'          
        self._l_attrsToLoad = []
        _d_processed = {}
        
        if not self._ml_nodes:
            return False      
        
        #for k in uiWin_multiSetAttr._checkBoxKeys:
            #log.info("{0} : {1}".format(k, self._d_uiCheckBoxes[k].getValue()))
        #['shared','keyable','transforms','user','other']
        
        _shared = self._d_uiCheckBoxes['shared'].getValue()
        #_keyable = self._d_uiCheckBoxes['keyable'].getValue()
        _regular = self._d_uiCheckBoxes['regular'].getValue()
        _user = self._d_uiCheckBoxes['user'].getValue()
        _numeric = self._d_uiCheckBoxes['numeric'].getValue()
        _sort = self._d_uiCheckBoxes['sort'].getValue()
        
        
        #_transforms = self._d_uiCheckBoxes['trans'].getValue()        
        #_other = self._d_uiCheckBoxes['other'].getValue()
        
        for mObj in self._ml_nodes:
            _short = mObj.p_nameShort
            _d_processed[_short] = []
            _l_processed = _d_processed[_short] 
            
            #_d_kws = {'ud':_user,"keyable":_keyable, 'settable':True}
            
            
            _l_raw = []
            if _regular:
                _l_raw.extend( mc.listAttr(mObj.mNode, keyable=True) or [])
                if VALID.getTransform(mObj.mNode):
                    _l_raw.extend(SHARED._d_attrCategoryLists['transform'])
                _l_raw.extend(mc.listAttr(mObj.mNode, ud=True) or [])
                _l = LISTS.get_noDuplicates(_l_raw)
            else:
                _l = mc.listAttr(mObj.mNode, settable=True) or []

            
            for a in _l:
                try:
                    _d = ATTR.validate_arg(mObj.mNode,a)
                    if _numeric:
                        if ATTR.is_numeric(_d):
                            _l_processed.append(a)
                    else:
                        _l_processed.append(a)
                except Exception,err:
                    log.warning("|{0}| >> Failed to process: {1} : {2} || err:{3}".format(_str_func, _short, a,err))

        if _shared and len(self._ml_nodes)>1:
            self._l_attrsToLoad = _d_processed[self._ml_nodes[0].p_nameShort]#...start with our first object
             
            for mObj in self._ml_nodes[1:]:
                _l = _d_processed[mObj.p_nameShort]
                for a in self._l_attrsToLoad:
                    if a not in _l:
                        log.info("|{0}| >> {1} not shared. removing...".format(_str_func, a))                           
                        self._l_attrsToLoad.remove(a)
        else:
            for k,l in _d_processed.iteritems():
                self._l_attrsToLoad.extend(l)
                
        self._l_attrsToLoad = LISTS.get_noDuplicates(self._l_attrsToLoad)
        
        if _sort:
            self._l_attrsToLoad.sort()
        
        """for a in self._l_attrsToLoad:
            log.info("|{0}| >> {1} : {2}".format(_str_func, _short, a))   
        log.info(cgmGEN._str_subLine)"""

        #...menu...
        log.debug("|{0}| >> List....".format(_str_func,))                
        self.uiScrollList_attr.clear()
        _len = len(self._ml_nodes)
        
        if not self._l_attrsToLoad:
            return False
        
        _progressBar = cgmUI.doStartMayaProgressBar(len(self._l_attrsToLoad),"Processing...")
        try:
            for a in self._l_attrsToLoad:
                
                mc.progressBar(_progressBar, edit=True, status = ("{0} Processing attribute: {1}".format(_str_func,a)), step=1)                    
                
                try:
                    if _len == 1:
                        _short = self._ml_nodes[0].p_nameShort
                        _d = ATTR.validate_arg(_short,a)
                        
                        _l_report = [a+'   ']
                        
                        _l_flags = []
                        
                        if ATTR.is_keyable(_d):
                            _l_flags.append('K')                          
                        if ATTR.is_locked(_d):
                            _l_flags.append('L')
                        if ATTR.is_hidden(_d):
                            _l_flags.append('H')
                        if ATTR.is_readable(_d):
                            _l_flags.append('R')
                        if ATTR.is_writable(_d):
                            _l_flags.append('W')
                        if _l_flags:
                            _l_report.append(''.join(_l_flags))
                            
                        _l_report.append("{0}".format(ATTR.get_type(_d))) 
                            
                        if ATTR.is_numeric(_d):
                            _d_flags = ATTR.get_numericFlagsDict(_d)
                            if _d_flags.get('default') is not None:
                                _l_report.append("dv={0}".format(_d_flags.get('default')))
                            if _d_flags.get('min') is not None:
                                _l_report.append("m={0}".format(_d_flags.get('min'))) 
                            if _d_flags.get('max') is not None:
                                _l_report.append("M={0}".format(_d_flags.get('max')))     
                            if _d_flags.get('softMin') is not None:
                                _l_report.append("sm={0}".format(_d_flags.get('softMin')))
                            if _d_flags.get('softMax') is not None:
                                _l_report.append("sM={0}".format(_d_flags.get('softMax')))                                
                        _l_report.append("{0}".format(ATTR.get(_d)))
                        
                        #_str = " -- ".join(_l_report)
                        self.uiScrollList_attr.append("/ ".join(_l_report))
                    else:
                        self.uiScrollList_attr.append(a)
                except:
                    log.info("|{0}| >> {1}.{2} | failed to query. Removing".format(_str_func, _short, a))  
                    self._l_attrsToLoad.remove(a)
                log.debug("|{0}| >> {1} : {2}".format(_str_func, _short, a))  
        except Exception,err:
            try:cgmUI.doEndMayaProgressBar(_progressBar)
            except:pass
            raise Exception,err

        #menu(edit=True,cc = uiAttrUpdate)
        cgmUI.doEndMayaProgressBar(_progressBar)
        
        return False
    
        if self.SourceObject and self.SourceObject.update(self.SourceObject.nameLong):
            if self.HideNonstandardOptionVar.value:
                self._l_attrsToLoad.extend(self.SourceObject.transformAttrs)
                self._l_attrsToLoad.extend(self.SourceObject.userAttrs)
                self._l_attrsToLoad.extend(self.SourceObject.keyableAttrs)
    
                self._l_attrsToLoad = lists.returnListNoDuplicates(self._l_attrsToLoad)
            else:
                self._l_attrsToLoad.extend( mc.listAttr(self.SourceObject.nameLong) )
    
            if self.HideTransformsOptionVar.value:
                for a in self.SourceObject.transformAttrs:
                    if a in self._l_attrsToLoad:
                        self._l_attrsToLoad.remove(a)
    
            if self.HideUserDefinedOptionVar.value:
                for a in self.SourceObject.userAttrs:
                    if a in self._l_attrsToLoad:
                        self._l_attrsToLoad.remove(a)	
    
            if self.HideParentAttrsOptionVar.value:
                for a in self._l_attrsToLoad:
                    if (mc.attributeQuery(a, node = self.SourceObject.nameLong, listChildren=True)) is not None:
                        self._l_attrsToLoad.remove(a)
    
            if self.HideCGMAttrsOptionVar.value:
                buffer = []
                for a in self._l_attrsToLoad:
                    if 'cgm' not in a:
                        buffer.append(a)
                if buffer:
                    self._l_attrsToLoad = buffer
    
        if self._l_attrsToLoad:	    
            return True
    
        return False        
            
        
    def uiReport_objects(self):
        if self._d_attrs:
            if len(self._ml_nodes) == 1:
                _short = self._ml_nodes[0].p_nameShort
                _str_report = ' | '.join([_short,
                                         "attrs: {0}".format(len(self._d_attrs[_short]))])
            else:
                _l = [mObj.p_nameBase for mObj in self._ml_nodes]                
                _str_report = ' , '.join(_l)
                if len(_str_report) >= 100:
                    _str_report = "{0} Objects. Report to see them all".format(len(self._ml_nodes))
            self.uiField_attrReport(edit=True, label = _str_report)   
        else:
            self.uiField_attrReport(edit=True, label = '...')
        
    def build_layoutWrapper(self,parent):
        _str_func = 'build_layoutWrapper'
        self._d_uiCheckBoxes = {}
        
        _MainForm = mUI.MelFormLayout(parent,ut='cgmUISubTemplate')
        
        _header = cgmUI.add_Header('Objects')
        #cgmUI.add_LineSubBreak()
        
        
        _row_attrReport = mUI.MelHLayout(_MainForm ,ut='cgmUIInstructionsTemplate',h=20)
        self.uiField_attrReport = mUI.MelLabel(_row_attrReport,
                                               bgc = SHARED._d_gui_state_colors.get('help'),
                                               label = '...',
                                               h=20)
        _row_attrReport.layout()
        
        #mc.setParent()
        #cgmUI.add_LineBreak()
        #mc.setParent()        
        #cgmUI.add_SectionBreak()
        

        #>>>Objects Buttons Row ---------------------------------------------------------------------------------------
        _row_attrCreate = mUI.MelHLayout(_MainForm,ut='cgmUITemplate',padding = 5)
    
        cgmUI.add_Button(_row_attrCreate,'Load Selected',
                         cgmGEN.Callback(self.uiFunc_load_selected),
                         #lambda *a: attrToolsLib.doAddAttributesToSelected(self),
                         "Add the attribute names from the text field")
        cgmUI.add_Button(_row_attrCreate,'Report',
                         cgmGEN.Callback(self.uiFunc_report_loaded),                         
                         "Add the attribute names from the text field")        

        cgmUI.add_Button(_row_attrCreate,'Clear',
                         cgmGEN.Callback(self.uiFunc_clear_loaded),                         
                         "Add the attribute names from the text field")
        _row_attrCreate.layout()  
        
        #Flags ---------------------------------------------------------------------------------------------
        _row_attrFlags = mUI.MelHSingleStretchLayout(_MainForm,ut='cgmUISubTemplate',padding = 5)
        
        mUI.MelSpacer(_row_attrFlags,w=5)
        self._d_uiCheckBoxes['sort'] = mUI.MelCheckBox(_row_attrFlags,label = 'Sort',
                                                       v=True,
                                                       cc = cgmGEN.Callback(self.uiFunc_updateScrollAttrList))                

        mUI.MelLabel(_row_attrFlags,l = 'Show')
        _row_attrFlags.setStretchWidget( mUI.MelSeparator(_row_attrFlags) )
        for item in uiWin_multiSetAttr._checkBoxKeys:
            if item in ['shared','regular','user']:_cb = True
            else:_cb = False
            self._d_uiCheckBoxes[item] = mUI.MelCheckBox(_row_attrFlags,label = item,
                                                         v = _cb,
                                                         cc = cgmGEN.Callback(self.uiFunc_updateScrollAttrList))
        _row_attrFlags.layout()
        
        #>>>Manage Attribute Section ---------------------------------------------------------------------------------------
        self.uiScrollList_attr = mUI.MelObjectScrollList(_MainForm, allowMultiSelection=True,
                                                         selectCommand = self.uiFunc_selectAttr)
        
        #>>>SetValue Row --------------------------------------------------------------------------------------------
        self.row_setValue = mUI.MelHLayout(_MainForm,ut='cgmUISubTemplate',padding = 5)
        mUI.MelLabel(self.row_setValue ,l = 'Set value: ')
        
        
        _MainForm(edit = True,
                  af = [(_header,"top",0),
                        (_header,"left",0),
                        (_header,"right",0),
                        (self.uiScrollList_attr,"left",0),
                        (self.uiScrollList_attr,"right",0),
                        (_row_attrReport,"left",5),
                        (_row_attrReport,"right",5),
                        (_row_attrCreate,"left",5),
                        (_row_attrCreate,"right",5),
                        (_row_attrFlags,"left",5),
                        (_row_attrFlags,"right",5),   
                        (self.row_setValue,"left",5),
                        (self.row_setValue,"right",5),                          
                        (self.row_setValue,"bottom",5),
                        ],
                  ac = [(_row_attrReport,"top",2,_header),
                        (_row_attrCreate,"top",2,_row_attrReport),
                        (_row_attrFlags,"top",2,_row_attrCreate),
                        (self.uiScrollList_attr,"top",2,_row_attrFlags),
                        (self.uiScrollList_attr,"bottom",5,self.row_setValue)],
                  attachNone = [(self.row_setValue,"top")])	        
            
        

        
        """MelMenuItem(popUpMenu ,
                    label = 'Make Keyable',
                    c = lambda *a: attrToolsLib.uiManageAttrsKeyable(self))
    
        MelMenuItem(popUpMenu ,
                    label = 'Make Unkeyable',
                    c = lambda *a: attrToolsLib.uiManageAttrsUnkeyable(self))
    
        MelMenuItemDiv(popUpMenu)
    
        MelMenuItem(popUpMenu ,
                    label = 'Hide',
                    c = lambda *a: attrToolsLib.uiManageAttrsHide(self))
    
        MelMenuItem(popUpMenu ,
                    label = 'Unhide',
                    c = lambda *a: attrToolsLib.uiManageAttrsUnhide(self))
    
        MelMenuItemDiv(popUpMenu)
        MelMenuItem(popUpMenu ,
                    label = 'Lock',
                    c = lambda *a: attrToolsLib.uiManageAttrsLocked(self))
    
        MelMenuItem(popUpMenu ,
                    label = 'Unlock',
                    c = lambda *a: attrToolsLib.uiManageAttrsUnlocked(self))
    
        MelMenuItemDiv(popUpMenu)
        MelMenuItem(popUpMenu ,
                    label = 'Delete',
                    c = lambda *a: attrToolsLib.uiManageAttrsDelete(self))      """  
    
        _sel = mc.ls(sl=True)
        if _sel:
            self.uiFunc_load_selected()        

    def uiFunc_selectAttr(self): 
        _str_func = 'uiFunc_selectAttr'        
        if self.uiPopUpMenu_attr:
            self.uiPopUpMenu_attr.clear()
            self.uiPopUpMenu_attr.delete()
            
        self.uiPopUpMenu_attr = mUI.MelPopupMenu(self.uiScrollList_attr,button = 3)

        _popUp = self.uiPopUpMenu_attr   
        
        _numeric = False
        _numberChanges = False
        
        _indices = self.uiScrollList_attr.getSelectedIdxs()
        _short = self._ml_nodes[0].p_nameShort
        
        for i in _indices:
            _a = self._l_attrsToLoad[i]
            _d = ATTR.validate_arg(_short, _a)
            if ATTR.is_numeric(_d) and ATTR.is_dynamic(_d):
                _numberChanges = True
                log.warning("|{0}| >> {1}.{2}...setting up value change popup".format(_str_func, _short,_a))                           

        
        #>>>Pop up menu--------------------------------------------------------------------------------------------        
        _l_boolToMake = ['keyable','lock','hidden']
        
        for item in _l_boolToMake:
            _menu = mUI.MelMenuItem(_popUp, subMenu = True,
                                label = item.capitalize())
            mUI.MelMenuItem(_menu,
                        label ='True',
                        c = cgmGEN.Callback(self.uiFunc_attrManage_fromScrollList,**{item:True}))        
            mUI.MelMenuItem(_menu,
                        label ='False',
                        c = cgmGEN.Callback(self.uiFunc_attrManage_fromScrollList,**{item:False}))            
        mUI.MelMenuItem(_popUp,l='test')
        
        
        
        
        _l_toDo = ['min','max','softMin','softMax','default','alias','rename']
        
    def uiFunc_attrManage_fromScrollList(self,**kws):
        _str_func = 'attrManage_fromScrollList'
        _indices = self.uiScrollList_attr.getSelectedIdxs()
        
        _keyable = kws.get('keyable',None)
        _lock = kws.get('lock',None)
        _hidden = kws.get('hidden',None)
        
        for i in _indices:
            _a = self._l_attrsToLoad[i]
            for mNode in self._ml_nodes:
                _short = mNode.p_nameShort
                _d = ATTR.validate_arg(_short,_a)
                if not _d:
                    log.warning("|{0}| >> not validated. skipping: {1}.{2}".format(_str_func, _short,_a))                           
                    continue
                
                if _keyable is not None:
                    log.warning("|{0}| >> {1}.{2} keyable: {3}".format(_str_func, _short,_a,_keyable))                                               
                    ATTR.set_keyable(_d,_keyable)
                if _lock is not None:
                    log.warning("|{0}| >> {1}.{2} lock: {3}".format(_str_func, _short,_a,_lock))                           
                    ATTR.set_lock(_d,_lock)        
                if _hidden is not None:
                    log.warning("|{0}| >> {1}.{2} hidden: {3}".format(_str_func, _short,_a,_hidden))                                               
                    ATTR.set_hidden(_d,_hidden)
                    
        
        self.uiFunc_updateScrollAttrList()
                    
    
def uiRow_attributeTypes(self,parent):	
    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    # Attr type row
    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    self.attrTypes = ['string','float','int','double3','bool','enum','message']
    attrShortTypes = ['str','float','int','[000]','bool','enum','msg']

    self.rc_attrTypes = mUI.MelRadioCollection()

    #build our sub section options
    _row = mUI.MelHLayout(parent,ut='cgmUISubTemplate',padding = 5)
    for cnt,item in enumerate(self.attrTypes):
        if item == 'float':_rb = True
        else:_rb = False
        self.rc_attrTypes.createButton(_row,label=attrShortTypes[cnt],sl=_rb)
                                                                      #onCommand = Callback(self.CreateAttrTypeOptionVar.set,item)))
        mUI.MelSpacer(_row,w=2)

    #if self.CreateAttrTypeOptionVar.value:
        #mc.radioCollection(self.rc_attrTypes ,edit=True,sl= (self.rc_attrTypeChoices[ self.attrTypes.index(self.CreateAttrTypeOptionVar.value) ]))

    _row.layout()
    

def uiScrollListFUNC_update(self,menu,selectAttr = None):
    def uiAttrUpdate(item):
        #uiSelectActiveAttr(self,item)
        pass
    
    menu.clear()
    attrs=[]
    for a in self.loadAttrs:
        if a not in ['attributeAliasList']:
            attrs.append(a)

    if attrs:
        if self.SortModifyOptionVar.value:
            attrs.sort()    
        # Get the attributes list
        if attrs:
            for a in attrs:
                menu.append(a)
            #uiSelectActiveAttr(self,attrs[-1])
        else:
            menu.clear()
        #Select if we can
        if selectAttr in attrs:            
            index = attrs.index(selectAttr)
            self.ObjectAttributesOptionMenu.selectByIdx(index ) 
            #uiSelectActiveAttr(self,selectAttr)
        else:
            pass
            #uiSelectActiveAttr(self,attrs[0])
        menu(edit=True,cc = uiAttrUpdate)    
    
    
def uiUpdateObjectAttrMenu(self,menu,selectAttr = False):
    """ 
    Updates the attribute menu of a loaded object in the modify section

    Keyword arguments:
    menu(string) -- Menu name
    selectAttr(string) -- Name of an attr (False ignores)
    """ 
    def uiAttrUpdate(item):
        uiSelectActiveAttr(self,item)

    menu.clear()
    attrs=[]
    for a in self.loadAttrs:
        if a not in ['attributeAliasList']:
            attrs.append(a)

    if attrs:
        if self.SortModifyOptionVar.value:
            attrs.sort()    
        # Get the attributes list
        if attrs:
            for a in attrs:
                menu.append(a)
            uiSelectActiveAttr(self,attrs[-1])
        else:
            menu.clear()
        #Select if we can
        if selectAttr in attrs:            
            index = attrs.index(selectAttr)
            self.ObjectAttributesOptionMenu.selectByIdx(index ) 
            uiSelectActiveAttr(self,selectAttr)
        else:
            uiSelectActiveAttr(self,attrs[0])
        menu(edit=True,cc = uiAttrUpdate)
        

