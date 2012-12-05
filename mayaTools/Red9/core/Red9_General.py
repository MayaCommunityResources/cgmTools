'''

------------------------------------------
Red9 Studio Pack : Maya Pipeline Solutions
email: rednineinfo@gmail.com
------------------------------------------

This is the General library of utils used throughout the modules
These are abstract general functions

NOTHING IN THIS MODULE SHOULD REQUIRE RED9
================================================================

'''

import maya.cmds as cmds
import maya.mel as mel
import os
import time
import inspect
import sys
import ctypes


import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)



# Generic Utility Functions
#---------------------------------------------------------------------------------


def forceToString(text):    
    '''
    simple function to ensure that data can be passed correctly into
    textFields for the UI (ensuring lists are converted)
    '''       
    if issubclass(type(text),list):
        return ','.join(text)
    else:
        return text
    

def itersubclasses(cls,_seen=None):
    """
    itersubclasses(cls)
    http://code.activestate.com/recipes/576949-find-all-subclasses-of-a-given-class/
    Iterator to yield full inheritance from a given class, including subclasses. This
    is used in the MetaClass to build the RED9_META_REGISTERY inheritance dict
    """
    if _seen is None: _seen = set()
    try:
        subs = cls.__subclasses__()
    except TypeError: # fails only when cls is type
        subs = cls.__subclasses__(cls)
    for sub in subs:
        if sub not in _seen:
            _seen.add(sub)
            yield sub
            for sub in itersubclasses(sub, _seen):
                yield sub
                

def inspectFunctionSource(value):
    '''
    This is a neat little wrapper over the mel "whatIs" and Pythons inspect
    module that finds the given functions source filePath, either Mel or Python
    and opens the original file in the default program. 
    Great for developers
    Supports all Mel functions, and Python Class / functions
    '''
    path=None
    #sourceType=None
    #Inspect for MEL
    log.debug('inspecting given command: %s' % value)
    #if issubclass(sourceType(value),str):
    try:
        path=mel.eval('whatIs("%s")' % value)
        if path and not path=="Command":
            path=path.split("in: ")[-1]
            #if path:
                #sourceType='mel'
        elif path=="Command":
            cmds.warning('%s : is a Command not a script' % value )
            return False
    except StandardError, error:
        log.info(error)
    #Inspect for Python
    if not path or not os.path.exists(path):
        log.info('This is not a known Mel command, inspecting Python libs for : %s' % value)
        try:
            log.debug( 'value :  %s' % value)
            log.debug ('value isString : ', isinstance(value,str))
            log.debug ('value callable: ', callable(value))
            log.debug ('value is module : ', inspect.ismodule(value))
            log.debug ('value is method : ', inspect.ismethod(value))
            if isinstance(value,str):
            #if not callable(value):
                value=eval(value)
            path=inspect.getsourcefile(value)
            if path:
                #sourceType='python'
                log.info('path : %s' % path)
        except StandardError, error:
            log.exception(error)
            
    #Open the file with the default editor 
    #FIXME: If Python and you're a dev then the .py file may be set to open in the default
    #Python runtime/editor and won't open as expected. Need to look at this.
    if path and os.path.exists(path):
        log.debug('NormPath : %s' % os.path.normpath(path))
        os.startfile(os.path.normpath(path))
        return True
    else:
        log.warning('No valid path or functions found matches selection')
        return False
    

def getScriptEditorSelection():
        '''
        this is a hack to bypass an issue with getting the data back from the
        ScriptEditorHistory scroll. We need to copy the selected text to the
        clipboard then pull it back afterwards.
        '''
        import Red9.packages.pyperclip as pyperclip
        control=mel.eval("$v=$gLastFocusedCommandControl")
        executer=mel.eval("$v=$gLastFocusedCommandExecuter")
        reporter=mel.eval("$v=$gLastFocusedCommandReporter")
        func=""
        if control==executer:
            func=cmds.cmdScrollFieldExecuter(control, q=True, selectedText=True)
        elif control==reporter:
            cmds.cmdScrollFieldReporter(reporter,e=True,copySelection=True)
            #func=Clipboard.getText()  
            #pyperclip.py : IN TESTING : Platform independant clipboard support
            func=pyperclip.paste()
        log.info('command caught: %s ' % func)
        return func

        

# Context Managers and Decorators
#---------------------------------------------------------------------------------

def Timer(func):
    '''
    Simple timer decorator    
    '''
    def wrapper( *args, **kws):
        t1 = time.time()
        res=func(*args,**kws) 
        t2 = time.time()
        log.debug('%s: took %0.3f ms' % (func.func_name, (t2-t1)*1000.0))
        return res
    return wrapper  


def runProfile(func):
    '''

    '''
    import cProfile
    from time import gmtime, strftime

    def wrapper(*args, **kwargs):
        currentTime = strftime("%d-%m-%H.%M.%S", gmtime())
        dumpFileName = 'c:/%s(%s).profile' % (func.__name__, currentTime)
        def command():
            func(*args, **kwargs)
        profile = cProfile.runctx("command()",globals(),locals(),dumpFileName)
        return profile
    return wrapper
    
class AnimationContext(object):
    """
    Simple Context Manager for restoring Animation settings
    """
    def __init__(self):
        self.autoKeyState=None
        self.timeStore=None
        
    def __enter__(self):
        self.autoKeyState=cmds.autoKeyframe(query=True,state=True)
        self.timeStore=cmds.currentTime(q=True)
        cmds.undoInfo(openChunk=True)

    def __exit__(self, exc_type, exc_value, traceback):
        # Close the undo chunk, warn if any exceptions were caught:
        cmds.autoKeyframe(state=self.autoKeyState)  
        cmds.currentTime(self.timeStore)
        log.info('autoKeyState restored: %s' % self.autoKeyState)
        log.info('currentTime restored: %f' % self.timeStore)
        cmds.undoInfo(closeChunk=True)
        if exc_type:
            log.exception('%s : %s'%(exc_type, exc_value))
        # If this was false, it would re-raise the exception when complete
        return True 

    
class HIKContext(object):
    """
    Simple Context Manager for restoring HIK Animation settings and managing HIK callbacks
    """
    def __init__(self, NodeList):
        self.objs=cmds.ls(sl=True,l=True)
        self.NodeList=NodeList
        self.managedHIK = False

    def __enter__(self):
        try:
            #We set the keying group mainly for the copyKey code, stops the entire rig being
            #manipulated on copy of single effector data
            self.keyingGroups=cmds.keyingGroup(q=True, fil=True)
            if [node for node in self.NodeList if cmds.nodeType(node) == 'hikIKEffector'\
                or cmds.nodeType(node) == 'hikFKJoint']:
                self.managedHIK = True
                
            if self.managedHIK:
                cmds.keyingGroup(fil="NoKeyingGroups")
                log.info('Processing HIK Mode >> using HIKContext Manager:')
                cmds.select(self.NodeList)
                mel.eval("hikManipStart 1 1")  
        except:
            self.managedHIK = False

    def __exit__(self, exc_type, exc_value, traceback):
        if self.managedHIK:
            cmds.keyingGroup(fil=self.keyingGroups)
            cmds.select(self.NodeList)
            mel.eval("hikManipStop")
            log.info('Exit HIK Mode >> HIKContext Manager:')
        if exc_type:
            log.exception('%s : %s'%(exc_type, exc_value))
        cmds.select(self.objs)
        return True 
                
                
# General
#---------------------------------------------------------------------------------
  
def thumbNailScreen(filepath,width,height):
    '''
    Generate a ThumbNail of the screen
    Note: 'cf' flag is broken in 2012
    @param filepath: path to Thumbnail
    @param width: width of capture
    @param height: height of capture   
    '''
    filepath=os.path.splitext(filepath)[0]
    filename=os.path.basename(filepath)
    filedir=os.path.dirname(filepath)
    
    #get modelPanel and camera
    win=cmds.playblast(activeEditor=True).split('|')[-1]
    cam=cmds.modelPanel(win,q=True,camera=True)
    if not cmds.nodeType(cam)=='camera': 
        cam=cmds.listRelatives(cam)[0]
    
    storedformat = cmds.getAttr('defaultRenderGlobals.imageFormat')
    storedResolutionGate=cmds.getAttr('%s.filmFit' % cam)
    
    cmds.setAttr('defaultRenderGlobals.imageFormat', 20)
    cmds.setAttr('%s.filmFit' % cam, 2) #set to Vertical so we don't get so much overscan
    cmds.playblast( startTime=cmds.currentTime(q=True),
                          endTime=cmds.currentTime(q=True),
                          format="image", 
                          filename=filepath,
                          width=width,
                          height=height,
                          percent=100,
                          quality=90,
                          forceOverwrite=True,
                          framePadding=0,
                          showOrnaments=False,
                          compression="BMP",
                          viewer=False ) 
    cmds.setAttr('defaultRenderGlobals.imageFormat' ,storedformat)
    cmds.setAttr('%s.filmFit' % cam, storedResolutionGate)
    #Why do this rename? In Maya2012 the 'cf' flag fails which means you have to use
    #the 'f' flag and that adds framePadding, crap I know! So we strip it and rename
    #the file after it's made.
    try:
        newfile=[f for f in os.listdir(filedir) 
                 if f.split('.bmp')[0].split('.')[0] == filename and not
                 '.pose' in f]
        log.debug('Original Playblast file : %s' % newfile)
        os.rename(os.path.join(filedir,newfile[0]),'%s.bmp' % filepath)
        log.debug('Thumbnail Renamed : %s' % ('%s.bmp' % filepath))
        return '%s.bmp' % filepath
    except:
        pass

def thumbnailApiFromView(filename, width, height, compression='bmp', modelPanel='modelPanel4'):
    '''
    grab the thumbnail direct from the buffer?
    TODO: not yet figured out how you crop the data here? 
    '''
    import maya.OpenMaya as OpenMaya
    import maya.OpenMayaUI as OpenMayaUI
    
    #Grab the last active 3d viewport
    view = None
    if modelPanel is None:
        view = OpenMayaUI.M3dView.active3dView()
    else:
        view = OpenMayaUI.M3dView()
        OpenMayaUI.M3dView.getM3dViewFromModelEditor(modelPanel, view)
    
    #read the color buffer from the view, and save the MImage to disk
    image = OpenMaya.MImage()
    view.readColorBuffer(image, True)
    image.resize(width, height, True)
    image.writeToFile(filename, compression)
    
    

class Clipboard:
    '''
    Get or Set data to the Windows clipboard...Used in the inspect code to grab the 
    ScriptEditor's selected history
    '''
#    def __init__(self):
#        import sys
#        import ctypes

    @staticmethod
    def getText():
        '''
        Get clipboard text if available
        '''
        
        # declare win32 API
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        if not user32.OpenClipboard(0):
            return ''
        
        CF_TEXT = 1
        hClipMem = user32.GetClipboardData(CF_TEXT)
        kernel32.GlobalLock.restype = ctypes.c_char_p
        value = kernel32.GlobalLock(hClipMem)
        kernel32.GlobalUnlock(hClipMem)
        user32.CloseClipboard()

        if isinstance(value, str):
            return value
        elif hasattr(value, 'decode'):
            return value.decode(sys.getfilesystemencoding())        
        else:
            return ''

    @staticmethod
    def setText(value):
        '''
        Set clipbard text
        '''
        if not isinstance(value, str):
            raise TypeError('value should be of str type')

        # declare win32 API
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        GlobalLock = kernel32.GlobalLock
        memcpy = ctypes.cdll.msvcrt.memcpy

        CF_TEXT = 1
        GHND = 66

        buf = ctypes.c_buffer(value.encode(sys.getfilesystemencoding()))
        bufferSize = ctypes.sizeof(buf)
        hGlobalMem = kernel32.GlobalAlloc(GHND, bufferSize)
        GlobalLock.restype = ctypes.c_void_p
        lpGlobalMem = GlobalLock(hGlobalMem)
        memcpy(lpGlobalMem, ctypes.addressof(buf), bufferSize)
        kernel32.GlobalUnlock(hGlobalMem)
        
        if user32.OpenClipboard(0):
            user32.EmptyClipboard()
            user32.SetClipboardData(CF_TEXT, hGlobalMem)
            user32.CloseClipboard()
            return True


def pivotSnap(source, destination):
    rpPiv=cmds.xform(source,q=True,ws=True,rp=True)
    spPiv=cmds.xform(source,q=True,ws=True,rp=True)
    cmds.xform(destination,ws=True,rp=rpPiv)
    cmds.xform(destination,ws=True,rp=spPiv)

    