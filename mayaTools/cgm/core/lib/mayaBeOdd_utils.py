"""
Maya be Odd
Josh Burton 
www.cgmonks.com

For use with meta instance data
"""
__MAYALOCAL = 'MAYABEODD'

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
import maya.mel as mel

# From Red9 =============================================================

# From cgm ==============================================================
from cgm.core import cgm_General as cgmGeneral
from cgm.core.cgmPy import validateArgs as cgmValid

from cgm.lib import attributes
from cgm.core.lib import attribute_utils as coreAttr

#>>> Utilities
#===================================================================
def killRoguePanel(method = ''):
    """
    hattip:
    https://forums.autodesk.com/t5/maya-forum/error-cannot-find-procedure-quot-dcf-updateviewportlist-quot/td-p/8342659?fbclid=IwAR3IhCeCqzZvEREmxo5eA7ECQu9n82MEN_vqCFTmdySwNNbsrYREdDcv_QA
    """
    #['DCF_updateViewportList', 'CgAbBlastPanelOptChangeCallback']
    EVIL_METHOD_NAMES = cgmValid.listArg(method)
    
    capitalEvilMethodNames = [name.upper() for name in EVIL_METHOD_NAMES]
    modelPanelLabel = mel.eval('localizedPanelLabel("ModelPanel")')
    processedPanelNames = []
    panelName = mc.sceneUIReplacement(getNextPanel=('modelPanel', modelPanelLabel))
    while panelName and panelName not in processedPanelNames:
        editorChangedValue = mc.modelEditor(panelName, query=True, editorChanged=True)
        parts = editorChangedValue.split(';')
        newParts = []
        changed = False
        for part in parts:
            for evilMethodName in capitalEvilMethodNames:
                if evilMethodName in part.upper():
                    changed = True
                    break
            else:
                newParts.append(part)
        if changed:
            mc.modelEditor(panelName, edit=True, editorChanged=';'.join(newParts))
        processedPanelNames.append(panelName)
        panelName = mc.sceneUIReplacement(getNextPanel=('modelPanel', modelPanelLabel))
        log.info("Processed: {0}".format(panelName))