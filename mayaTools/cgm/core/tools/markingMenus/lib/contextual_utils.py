"""
------------------------------------------
contextual_utils: cgm.core.tools.markingMenus.lib.contextual_utils
Author: Josh Burton
email: jjburton@cgmonks.com
Website : http://www.cgmonks.com
------------------------------------------

"""
# From Python =============================================================
import copy
import re

#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

# From Maya =============================================================
import maya.cmds as mc


from cgm.core import cgm_Meta as cgmMeta
from cgm.core.lib import name_utils as NAMES
from cgm.core.lib import search_utils as SEARCH
from cgm.core.lib import shape_utils as SHAPE
from cgm.core.lib import rigging_utils as RIGGING

def get_list(context = 'selection', mType = None):
    """
    Get contextual data for updating a transform
    
    :parameters
        context(string): 
            selection
            children
            heirarchy
            scene
            buffer

    :returns
        list(list)
    """ 
    _str_func = "get_list"    
    _l_context = []
    _context = context.lower()
    
    log.debug("|{0}| >> context: {1} | mType: {2}".format(_str_func,_context,mType))  
    
    if _context == 'selection':
        log.debug("|{0}| >> selection mode...".format(_str_func))
        _l_context = mc.ls(sl=True)
    elif _context == 'scene':
        log.debug("|{0}| >> scene mode...".format(_str_func))        
        if mType is not None:
            _l_context = mc.ls(type=mType)
        else:
            raise Exception,"Really shouldn't use this without a specific object type..."
        
    elif _context == 'children':
        log.debug("|{0}| >> children mode...".format(_str_func)) 
        
        _sel = mc.ls(sl=True)
        for o in _sel:
            if mType:
                if mc.ls(o,type=mType):
                    _l_context.append(o)
            else:_l_context.append(o)
            
            if mType:
                try:_buffer = mc.listRelatives (o, allDescendents=True, type = mType) or []
                except:_buffer = []
            else:_buffer = mc.listRelatives (o, allDescendents=True) or []
            for o2 in _buffer:
                if o2 not in _l_context:
                    _l_context.append(o2)
       
    elif _context == 'heirarchy':
        log.debug("|{0}| >> heirarchy mode...".format(_str_func))  
        
        _sel = mc.ls(sl=True)
        for o in _sel:
            if mType:
                if mc.ls(o,type=mType):
                    _l_context.append(o)
            else:_l_context.append(o)
            
            _parents = SEARCH.get_all_parents(o)
            if _parents:
                root = _parents[-1]#...get the top of the tree
                if mType:
                    if mc.ls(root,type=mType):
                        _l_context.append(root)
                else:_l_context.append(root)   
                
                if mType:
                    try:_buffer = mc.listRelatives (root, allDescendents=True, type = mType) or []
                    except:_buffer = []
                    else:_buffer = mc.listRelatives (root, allDescendents=True) or []
                for o2 in _buffer:
                    if o2 not in _l_context:
                        _l_context.append(o2)
            else:
                if mType:
                    try:_buffer = mc.listRelatives (o, allDescendents=True, type = mType) or []
                    except:_buffer = []
                else:_buffer = mc.listRelatives (o, allDescendents=True) or []
                for o2 in _buffer:
                    if o2 not in _l_context:
                        _l_context.append(o2)                
                    
    else:
        log.warning("|{0}| >> context unkown: {1}...".format(_str_func,_context))        
        return False
    
    return _l_context

    
def set_attrs(self, attr = None, value = None, context = 'selection', mType = None):
    """
    Get data for updating a transform
    
    :parameters
        self(instance): cgmMarkingMenu

    :returns
        info(dict)
    """   
    _str_func = "set_attr"
    _context = context.lower()
    _l_context = get_list(_context, mType)
    
    log.debug("|{0}| >> attr: {1} | value: {2} | mType: {3} | context: {4}".format(_str_func,attr,value,mType,_context))             
        
    for o in _l_context:
        try:
            cgmMeta.cgmNode(o).__setattr__(attr,value)
        except Exception,err:
            log.error("|{0}| >> set fail. obj:{1} | attr:{2} | value:{3} | error: {4} | {5}".format(_str_func,NAMES.get_short(o),attr,value,err,Exception))
    
    mc.select(_l_context)
    return True

def color_override(value = None, context = 'selection', mType = None):
    """
    Get data for updating a transform
    
    :parameters
        self(instance): cgmMarkingMenu

    :returns
        info(dict)
    """   
    _str_func = "color_override"
    _context = context.lower()
    _l_context = get_list(_context, mType)
    _l_context.extend(get_list(_context,'joint'))
    log.debug("|{0}| >> value: {1} | mType: {2} | context: {3}".format(_str_func,value,mType,_context))             
        
    for o in _l_context:
        try:
            RIGGING.override_color(o,value)
        except Exception,err:
            log.error("|{0}| >> set fail. obj:{1} | value:{2} | error: {3} | {4}".format(_str_func,NAMES.get_short(o),value,err,Exception))
    
    mc.select(_l_context)
    return True

def select(context = 'selection', mType = None):
    """
    Get data for updating a transform
    
    :parameters
        self(instance): cgmMarkingMenu

    :returns
        info(dict)
    """   
    _str_func = "select"
    _context = context.lower()
    _l_context = get_list(_context, mType)
    log.debug("|{0}| >> List...".format(_str_func))   
    for o in _l_context:
        log.debug("|{0}| >> {1}".format(_str_func,o))   
        
    if not _l_context:
        log.warning("|{0}| >> no objects found. context: {1} | mType: {2}".format(_str_func,context,mType))
        return False
        
    mc.select(_l_context)
    
def func_enumrate_all_to_last(func,objects, mode = 'toFrom',**kws):
    """
    Get data for updating a transform
    
    :parameters
        self(instance): cgmMarkingMenu

    :returns
        info(dict)
    """   
    _str_func = "func_enumrate_all_to_last"
    
    log.debug("|{0}| >> func: {1}".format(_str_func, func.__name__))  
    log.debug("|{0}| >> kws: {1}".format(_str_func, kws))  
        
    for i,o in enumerate(objects[:-1]):
        log.debug("|{0}| >> {1} : {2}".format(_str_func,i,o))  
        try:
            if mode == 'toFrom':
                func(objects[-1],o,**kws)
            else:
                func(o,objects[-1],**kws)
        except Exception,err:
            log.error("|{0}| >> {1} : {2} failed! | err: {3}".format(_str_func,i,o,err))  
            
    #mc.select(objects[-1])

def func_all_to_last(func,objects, mode = 'toFrom',**kws):
    """
    Function for selection lists
    
    :parameters
        self(instance): cgmMarkingMenu

    :returns
        info(dict)
    """   
    _str_func = "func_all_to_last"
    
    log.debug("|{0}| >> func: {1}".format(_str_func, func.__name__))  
    log.debug("|{0}| >> kws: {1}".format(_str_func, kws))  
        
    #for i,o in enumerate(objects[:-1]):
        #log.debug("|{0}| >> {1} : {2}".format(_str_func,i,o))  
    try:
        if mode == 'toFrom':
            func(objects[-1],objects[:-1],**kws)
        else:
            func(objects[:-1],objects[-1],**kws)
    except Exception,err:
        log.error("|{0}| >> err: {2}".format(_str_func,err))  
        
    #mc.select(objects)
    
def func_process(func,objects, processMode = 'all', calledFrom = None, noSelect = True, **kws):
    """
    Process objects passed with fuction provided in different modes...
    
    :parameters
        func(function)
        objects(list)
        mode(str)
            all -- objects
            each -- func to each object
            eachToNext -- o,objects[i+1]
            fromPreviousEach -- objects[-1],o
            eachToLast -- o,objects[-1]
            firstToEach -- objects[0],o
            eachToFirst -- o,objects[0]
            eachToPrevious -- objects[i],objects[i-1]
            previousToEach -- objects[i-1],objects[i]
            lastFromRest - objects[-1],objects[:-1]
            restFromLast - objects[:-1],objects[-1]
            firstToRest - objects[0],objects[1:]
            restFromFirst - objects[1:],objects[0]
        calledFrom - String for debugging/
        kws(dict) -- pass through

    :returns
        info(dict)
        
        iterTo
    """   
    if calledFrom is not None:_str_func = "{0}".format(calledFrom)
    else:_str_func = "func_process"
    
    log.debug("|{0}| >> func: {1}".format(_str_func, func.__name__)) 
    log.debug("|{0}| >> mode: {1}".format(_str_func, processMode) )
    log.debug("|{0}| >> kws: {1}".format(_str_func, kws))  
    log.debug("|{0}| >> objects: {1}".format(_str_func, objects))  
    
    if processMode in ['each']:
        for i,o in enumerate(objects):
            log.debug("|{0}| >> {1} : {2}".format(_str_func,i,o))  
            
            if processMode == 'each':
                _res = func(o,**kws)    
                
            if _res:log.info( "|{0}.{1}| >> {2}".format( _str_func,processMode, _res ))
            
    elif processMode in ['eachToNext','fromPreviousEach','eachToLast']:
        for i,o in enumerate(objects[:-1]):
            log.debug("|{0}| >> {1} : {2}".format(_str_func,i,o))  
            try:
                if processMode == 'eachToNext':
                    _res = func(o,objects[i+1],**kws)
                elif processMode == 'fromPreviousEach':
                    _res = func(objects[-1],o,**kws)
                elif processMode == 'eachToLast':
                    _res = func(o,objects[-1],**kws)
                
                if _res:print( "|{0}| >> {1}".format( _str_func, _res ))
                
            except Exception,err:
                log.error("|{0}| >> {1} : {2} failed! | processMode:{4} | err: {3}".format(_str_func,i,o,err,processMode))
    elif processMode in ['firstToEach','eachToFirst','eachToPrevious','previousToEach']:
            for i,o in enumerate(objects[1:]):
                log.debug("|{0}| >> {1} : {2}".format(_str_func,i,o))  
                try:
                    if processMode == 'firstToEach':
                        _res = func(objects[0],o,**kws)
                    elif processMode == 'eachToFirst':
                        _res = func(o,objects[0],**kws) 
                        
                    elif processMode == 'eachToPrevious':
                        log.debug("|{0}| >> {1} < {2}".format(_str_func,o,objects[i-1]))  
                        _res = func(o,objects[i],**kws)     
                    elif processMode == 'previousToEach':
                        _res = func(objects[i],o,**kws)                       
                    if _res:print( "|{0}| >> {1}".format( _str_func, _res ))
                        
                except Exception,err:
                    log.error("|{0}| >> {1} : {2} failed! | processMode:{4} | err: {3}".format(_str_func,i,o,err,processMode))                 
    elif processMode in ['lastFromRest','restFromLast','firstToRest','restFromFirst','all']:
        if processMode == 'lastFromRest':
            _res = func(objects[-1],objects[:-1],**kws)  
        elif processMode == 'restFromLast':
            _res = func(objects[:-1],objects[-1],**kws)   
        elif processMode == 'all':
            _res = func(objects,**kws)   
        elif processMode == 'firstToRest':
            _res = func(objects[0],objects[1:],**kws)
        elif processMode == 'restFromFirst':
            _res = func(objects[1:],objects[0],**kws)               
        if _res:print( "|{0}| >> {1}".format( _str_func, _res ))
            
    else:
        raise ValueError,"|{0}.{1}| Unkown processMode: {2}".format(__name__,_str_func,processMode)
    
    if not noSelect:
        try:mc.select(objects)
        except:pass
            
def func_context_all(func,context = 'selection',mType = None, **kws):
    """
    
    :parameters
        self(instance): cgmMarkingMenu

    :returns
        info(dict)
    """   
    _str_func = "func_all"
    _context = context.lower()
    _l_context = get_list(_context, mType)  
        
    log.debug("|{0}| >> func: {1}".format(_str_func, func.__name__))  
    log.debug("|{0}| >> kws: {1}".format(_str_func, kws))  
        
    for i,o in enumerate(_l_context):
        log.debug("|{0}| >> {1} : {2}".format(_str_func,i,o))  
        try:
            func(o,**kws)
        except Exception,err:
            log.error("|{0}| >> {1} : {2} failed! | err: {3}".format(_str_func,i,o,err))
            
    try:mc.select(_l_context)
    except:pass