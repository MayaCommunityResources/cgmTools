#=========================================================================      
#=========================================================================         
from Red9.core import Red9_Meta as r9Meta
reload(r9Meta)
from Red9.core.Red9_Meta import *
r9Meta.registerMClassInheritanceMapping()    
#========================================================================
import random
import re
import copy
import time
import logging

from cgm.lib import distance

logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

from cgm.core import cgmMeta
reload(cgmMeta)
from cgm.core.cgmMeta import *

import maya.cmds as mc

def TestAllTheThings():
    """"
    Catch all test for meta stuff
    """
    cgmMeta_Test()

class cgmMeta_Test():
    def __init__(self):
        start = time.clock()
        self.test_Setup()
        self.test_attributeHandling()
        
        self.test_cgmNode()
        self.test_cgmObject()
        
        log.info('Initialization time =  %0.3f' % (time.clock()-start))       
        self.MetaInstance.select()
    
    
    def test_Setup(self):
        '''
        Tests proper creation of objects from flag calls
        '''        
        mc.file(new=True,f=True)
        function = 'test_Setup'
        log.info("-"*20  + "  Testing '%s' "%function + "-"*20 ) 
        start = time.clock()
        
        #Make a few objects
        #==============              
  
        
        #Test name and node argument passing
        #==============      
        log.info("Testing no arguments passed")
        self.MetaInstance = cgmMeta()
        assert mc.objExists(self.MetaInstance.mNode)        
        
        self.test_functionCalls()
        #Initial instance deleted at end of function call
        
        log.info("Testing name 'Hogwarts' being passed")
        self.MetaInstance = cgmMeta(name = 'Hogwarts')
        assert mc.objExists(self.MetaInstance.mNode)        
        assert self.MetaInstance.getShortName() == 'Hogwarts'     
        
        log.info("Pass node, no name...")        
        self.MetaInstance = cgmMeta(node = 'Hogwarts')
        assert mc.objExists(self.MetaInstance.mNode)                
        assert self.MetaInstance.getShortName() == 'Hogwarts'     
        
        log.info("Testing existing 'Hogwarts' node, new 'cgmTransform' name")
        self.MetaInstance = cgmMeta(node = 'Hogwarts', name = 'cgmTransform')
        assert mc.objExists(self.MetaInstance.mNode)
        assert self.MetaInstance.getShortName() == 'cgmTransform'
        
        log.info(">"*20 + "  Node creation test complete")         
        log.info('Simple name logic =  %0.3f' % (time.clock()-start))
        
        #Create nodeType
        #============== 
        #Need to create a Node and an object for separate tests
        
        self.MetaNode = cgmMeta(name = 'cgmNetwork', nodeType = 'network')
        assert mc.nodeType(self.MetaNode.mNode)=='network'
        
        self.MetaObject = cgmMeta(name = 'cgmTransform',nodeType = 'transform')
        assert mc.nodeType(self.MetaObject.mNode)=='transform'
        
        self.ObjectSet = cgmMeta(name = 'cgmObjectSet',nodeType = 'objectSet')
        assert mc.nodeType(self.ObjectSet.mNode)=='objectSet'
        
        #Create Test Objects and initialize
        #============== 
        nurbsCubeCatch = mc.nurbsCube()
        polyCubeCatch = mc.polyCube()  
        
        self.pCube = cgmMeta(polyCubeCatch[0],name = 'pCube')
        self.nCube = cgmMeta(nurbsCubeCatch[0],name = 'nCube')
        
        self.setup = True
        
        log.info(">"*20  +"Testing call '%s' took =  %0.3f'" % (function,(time.clock()-start)))
        
    def test_attributeHandling(self):
        '''
        Modified from Mark Jackson's testing for Red9
        This tests the standard attribute handing in the MetaClass.__setattr__ 
        '''
        if not self.MetaInstance:
            self.MetaInstance = cgmMeta()
            
        function = 'test_attributeHandling'
        log.info("-"*20  + "  Testing '%s' "%function + "-"*20 ) 
        start = time.clock()
        
        node=self.MetaInstance
        
        #standard attribute handling
        node.addAttr('stringTest', "this_is_a_string")  #create a string attribute
        node.addAttr('fltTest', 1.333)        #create a float attribute
        node.addAttr('intTest', 3)            #create a int attribute
        node.addAttr('boolTest', False)       #create a bool attribute
        node.addAttr('enumTest','A:B:D:E:F', attrType ='enum') #create an enum attribute
        
        #create a string attr with JSON serialized data
        testDict={'jsonFloat':1.05,'jsonInt':3,'jsonString':'string says hello','jsonBool':True}
        node.addAttr('jsonTest',testDict,attrType = 'string')

        #test the hasAttr call in the baseClass
        assert node.hasAttr('stringTest')
        assert node.hasAttr('fltTest')
        assert node.hasAttr('intTest')
        assert node.hasAttr('boolTest')
        assert node.hasAttr('enumTest')
        assert node.hasAttr('jsonTest')
        
        #test the actual Maya node attributes
        #------------------------------------
        assert mc.getAttr('%s.stringTest' % node.mNode, type=True)=='string'
        assert mc.getAttr('%s.fltTest' % node.mNode, type=True)=='double' or 'float', "Type is '%s'"%mc.getAttr('%s.fltTest' % node.mNode, type=True)
        assert mc.getAttr('%s.intTest' % node.mNode, type=True)=='long'
        assert mc.getAttr('%s.boolTest' % node.mNode, type=True)=='bool'
        assert mc.getAttr('%s.enumTest' % node.mNode, type=True)=='enum'
        assert mc.getAttr('%s.jsonTest' % node.mNode, type=True)=='string'
        
        assert mc.getAttr('%s.stringTest' % node.mNode)=='this_is_a_string'
        assert mc.getAttr('%s.fltTest' % node.mNode)==1.333,"Value is %s"%mc.getAttr('%s.fltTest' % node.mNode)
        assert mc.getAttr('%s.intTest' % node.mNode)==3
        assert mc.getAttr('%s.boolTest' % node.mNode)==False
        assert mc.getAttr('%s.enumTest' % node.mNode)==0
        assert mc.getAttr('%s.jsonTest' % node.mNode)=='{"jsonFloat": 1.05, "jsonBool": true, "jsonString": "string says hello", "jsonInt": 3}',"Value is '%s'%"%self.jsonTest
        
        #now check the MetaClass __getattribute__ and __setattr__ calls
        #--------------------------------------------------------------
        assert node.intTest==3       
        node.intTest=10     #set back to the MayaNode
        assert node.intTest==10
        #float
        assert node.fltTest==1.333
        node.fltTest = 3.55   #set the float attr
        assert node.fltTest==3.55,"Value is %s"%node.fltTest
        #string
        assert node.stringTest=='this_is_a_string'
        node.stringTest="change the text"   #set the string attr
        assert node.stringTest=='change the text'
        #bool
        assert node.boolTest==False
        node.boolTest=True  #set bool
        assert node.boolTest==True
        #enum
        assert node.enumTest==0
        node.enumTest='B'
        assert node.enumTest==1
        node.enumTest=2
        assert node.enumTest==2
        #json string handlers
        assert type(node.jsonTest)==dict
        assert node.jsonTest=={'jsonFloat':1.05,'jsonInt':3,'jsonString':'string says hello','jsonBool':True}
        assert node.jsonTest['jsonFloat']==1.05
        assert node.jsonTest['jsonInt']==3 
        assert node.jsonTest['jsonString']=='string says hello'
        assert node.jsonTest['jsonBool']==True 
       
        del(node.boolTest)
        assert mc.objExists(node.mNode)
        assert not node.hasAttr('boolTest')
        assert not mc.attributeQuery('boolTest',node=node.mNode,exists=True)
        
        log.info(">"*20  +"Testing call '%s' took =  %0.3f'" % (function,(time.clock()-start)))

        
    def test_functionCalls(self):
        function = 'test_functionCalls'
        log.info("-"*20  + "  Testing '%s' "%function + "-"*20 ) 
        start = time.clock()        
      
        #select
        name = self.MetaInstance.getShortName()
        assert mc.objExists(name)
        
        mc.select(cl=True)
        self.MetaInstance.select()
        assert mc.ls(sl=True)[0]== name
        
        #rename
        self.MetaInstance.rename('FooBar')
        assert self.MetaInstance.getShortName() =='FooBar',"mNode is '%s'"%self.MetaInstance.mNode
        self.MetaInstance.select()
        assert mc.ls(sl=True)[0]=='FooBar'
        
        #convert
        #new=self.MetaInstance.convertMClassType('MetaRig')
        #assert isinstance(new,r9Meta.MetaRig)
        #assert self.MetaInstance.mClass=='MetaRig'
        
        #delete
        self.MetaInstance.delete()
        assert not mc.objExists(name)
        
        log.info(">"*20  +"Testing call '%s' took =  %0.3f'" % (function,(time.clock()-start)))

        
    def test_cgmNode(self):
        function = 'test_cgmNode'
        log.info("-"*20  + "  Testing '%s' "%function + "-"*20 ) 
        start = time.clock()
        
        if not self.MetaNode:
            self.MetaNode = cgmMeta(name = 'cgmNode',nodeType = 'network')
            
        #Assert some info
        #----------------------------------------------------------   
        assert self.MetaNode.referencePrefix is not None
        
        #cgmNode functions
        #---------------------------------------------------------- 
        self.MetaNode.doName()
        assert self.MetaNode.hasAttr('cgmName') is True
        
        self.MetaObject.copyNameTagsFromObject(self.MetaNode.mNode)
        assert self.MetaObject.cgmName == self.MetaNode.cgmName,"CGM Name copying faild"
        
        self.MetaNode.doStore('stored',self.nCube.mNode)
        assert self.MetaNode.stored[0] == self.nCube.mNode,"'%s' is stored"%self.MetaNode.stored
        
        self.MetaNode.doRemove('stored')
        assert self.MetaNode.hasAttr('stored') is False
        
        log.info(">"*20  +"Testing call '%s' took =  %0.3f'" % (function,(time.clock()-start)))
    
    def test_cgmObject(self):
        function = 'test_cgmObject'
        log.info("-"*20  + "  Testing '%s' "%function + "-"*20 ) 
        start = time.clock()
        
        #Assert some info
        #---------------------------------------------------------- 
        
        #Let's move our test objects around and and see what we get
        #----------------------------------------------------------  
        self.MetaObject.rotateOrder = 0 #To have  base to check from
        
        #Randomly move stuff
        for attr in 'translateX','translateY','translateZ','rotateX','rotateY','rotateZ':
            self.pCube.__setattr__(attr,random.choice(range(1,10)))
        for attr in 'scaleX','scaleY','scaleZ':
            self.pCube.__setattr__(attr,random.choice([1,.5,.75]))
        self.pCube.rotateOrder = random.choice(range(1,5))#0 not an option for accurate testing
        
        for attr in 'translateX','translateY','translateZ','rotateX','rotateY','rotateZ':
            self.nCube.__setattr__(attr,random.choice(range(1,10)))
        for attr in 'scaleX','scaleY','scaleZ':
            self.nCube.__setattr__(attr,random.choice([1,.5,.75]))
        self.nCube.rotateOrder = random.choice(range(1,5))
        
        #Parent and assert relationship
        mc.parent(self.pCube.mNode,self.nCube.mNode)#parent pCube to nCube
        assert self.pCube.getParent() == self.nCube.mNode,"nCube is not parent"
        assert self.pCube.getShortName() in self.nCube.getChildren(),"pCube is not in children - %s"%self.nCube.getChildren()
        assert self.pCube.getShapes() is not None,"No Shapes found on pCube" #Check for shapes on nurbs
        assert self.nCube.getTransformAttrs() == self.pCube.getTransformAttrs(), "Transform attribute lists don't match"
        
        #Roate order match
        log.info("Testing rotate order match function")        
        self.MetaObject.copyRotateOrder(self.pCube.mNode)
        assert self.MetaObject.rotateOrder == self.pCube.rotateOrder,"Copy rotate order failed"
        
        self.MetaObject.copyRotateOrder = self.nCube.rotateOrder #Just set it
        assert self.MetaObject.copyRotateOrder == self.nCube.rotateOrder
        
        #Group
        log.info("Testing grouping function")
        previousPos = distance.returnWorldSpacePosition(self.pCube.mNode)
        self.pCube.doGroup(True)
        #assert previousPos == distance.returnWorldSpacePosition(self.pCube.mNode),"previous %s != %s"%(previousPos,distance.returnWorldSpacePosition(self.pCube.mNode))
        assert self.pCube.getParent() != self.nCube.mNode,"nCube shouldn't be the parent"
        
        #setDrawingOverrideSettings
        log.info("Testing drawing override functions")   
        self.pCube.overrideEnabled = 1     
        TestDict = {'overrideColor':20,'overrideVisibility':1}
        self.pCube.setDrawingOverrideSettings(TestDict, pushToShapes=True)
        
        assert self.pCube.overrideEnabled == 1
        assert self.pCube.overrideColor == 20
        assert self.pCube.overrideVisibility == 1
        
        for shape in self.pCube.getShapes():
            for a in TestDict.keys():
                assert attributes.doGetAttr(shape,a) == TestDict[a],"'%s.%s' is not %s"%(shape,a,TestDict[a])
            
        #Copy pivot
        log.info("Testing copy pivot function")        
        self.MetaObject.copyPivot(self.pCube.mNode)

        #Let's move our test objects around and and see what we get
        #----------------------------------------------------------           
        log.info(">"*20  +"Testing call '%s' took =  %0.3f'" % (function,(time.clock()-start)))

















class Test_MetaClass():
    def testAll(self):
        pass
    
    def setup(self):
        mc.file(new=True,f=True)
        self.MClass=r9Meta.MetaClass(name='MetaClass_Test')

    def teardown(self):
        self.setup()
    
    def test_initNew(self):
        assert isinstance(self.MClass,r9Meta.MetaClass)
        assert self.MClass.mClass=='MetaClass'
        assert self.MClass.mNode=='MetaClass_Test'
        assert mc.nodeType(self.MClass.mNode)=='network'
    
    def test_functionCalls(self):
        
        #select
        mc.select(cl=True)
        self.MClass.select()
        assert mc.ls(sl=True)[0]=='MetaClass_Test'
        
        #rename
        self.MClass.rename('FooBar')
        assert self.MClass.mNode=='FooBar'
        self.MClass.select()
        assert mc.ls(sl=True)[0]=='FooBar'
        
        #convert
        new=self.MClass.convertMClassType('MetaRig')
        assert isinstance(new,r9Meta.MetaRig)
        assert self.MClass.mClass=='MetaRig'
        
        #delete
        self.MClass.delete()
        assert not mc.objExists('MetaClass_Test')
        
    def test_MObject_Handling(self):
        #mNode is now handled via an MObject
        assert self.MClass.mNode=='MetaClass_Test'
        mc.rename('MetaClass_Test','FooBar')
        assert self.MClass.mNode=='FooBar'
        
    def test_addChildMetaNode(self):
        '''
        add a new MetaNode as a child of self
        '''
        newMFacial=self.MClass.addChildMetaNode('MetaFacialRig',attr='Facial',nodeName='FacialNode') 
        assert isinstance(newMFacial,r9Meta.MetaFacialRig)
        assert newMFacial.mNode=='FacialNode'
        assert mc.listConnections('%s.Facial' % self.MClass.mNode)==['FacialNode'] 
        assert isinstance(self.MClass.Facial,r9Meta.MetaFacialRig)
        
    def test_getChildMetaNodes(self):
        pass    
        
    def test_connectionsToMetaNodes(self):   
        '''
        Test how the code handles connections to other MetaNodes
        '''
        facialNode=r9Meta.MetaFacialRig(name='FacialNode')
        self.MClass.connectChild(facialNode,'Facial')
        
        assert self.MClass.Facial.mNode=='FacialNode'
        assert isinstance(self.MClass.Facial, r9Meta.MetaFacialRig)
        assert self.MClass.hasAttr('Facial')
        assert facialNode.hasAttr('Facial')
        assert mc.listConnections('%s.Facial' % self.MClass.mNode)==['FacialNode']
        
        self.MClass.disconnectChild(self.MClass.Facial, deleteSourcePlug=True, deleteDestPlug=True)
        assert not self.MClass.hasAttr('Facial')
        assert not facialNode.hasAttr('Facial')       
    
    
    def test_connectionsToMayaNode(self):
        '''
        Test how the code handles connections to standard MayaNodes
        '''
        cube1=mc.ls(mc.polyCube()[0],l=True)[0]
        cube2=mc.ls(mc.polyCube()[0],l=True)[0]
        cube3=mc.ls(mc.polyCube()[0],l=True)[0]
        cube4=mc.ls(mc.polyCube()[0],l=True)[0]
        
        #Singular Child
        self.MClass.connectChild(cube1,'Singluar')
        assert self.MClass.Singluar==[cube1]
        #Multi Children
        self.MClass.connectChildren([cube2,cube3],'Multiple')
        assert sorted(self.MClass.Multiple)==[cube2,cube3]
        
        #get the MetaNode back from the cube1 connection and retest
        found=r9Meta.getConnectedMetaNodes(cube1)[0]
        assert isinstance(found,r9Meta.MetaClass)
        assert found.mNode=='MetaClass_Test'
        assert found.mClass=='MetaClass'
        assert sorted(found.Multiple)==[cube2,cube3]
    
        #connect something else to Singluar
        self.MClass.connectChild(cube2,'Singluar')
        assert self.MClass.Singluar==[cube2]
        assert not mc.attributeQuery('Singluar',node=cube1,exists=True) #cleaned up after ourselves?
        
        self.MClass.connectChildren([cube3,cube4],'Singluar')
        assert sorted(self.MClass.Singluar)==[cube2,cube3,cube4]
        self.MClass.Singluar=cube1
        assert self.MClass.Singluar==[cube1]
        try:
            #still thinking about this....if the attr isn't a multi then
            #the __setattr__ will fail if you pass in a lots of nodes
            self.MClass.Singular=[cube1,cube2,cube3]
        except:
            assert True
        
        self.MClass.Multiple=[cube1,cube4]
        assert sorted(self.MClass.Multiple)==[cube1,cube4]
        
    def test_connectParent(self):
        pass
    
    def test_attributeHandling(self):
        '''
        This tests the standard attribute handing in the MetaClass.__setattr__ 
        '''
        node=self.MClass
        
        #standard attribute handling
        node.addAttr('stringTest', "this_is_a_string")  #create a string attribute
        node.addAttr('fltTest', 1.333)        #create a float attribute
        node.addAttr('intTest', 3)            #create a int attribute
        node.addAttr('boolTest', False)       #create a bool attribute
        node.addAttr('enum', 'A:B:D:E:F', type='enum') #create an enum attribute
        
        #create a string attr with JSON serialized data
        testDict={'jsonFloat':1.05,'jsonInt':3,'jsonString':'string says hello','jsonBool':True}
        node.addAttr('jsonTest',testDict)

        #test the hasAttr call in the baseClass
        assert node.hasAttr('stringTest')
        assert node.hasAttr('fltTest')
        assert node.hasAttr('intTest')
        assert node.hasAttr('boolTest')
        assert node.hasAttr('enum')
        assert node.hasAttr('jsonTest')
        
        #test the actual Maya node attributes
        #------------------------------------
        assert mc.getAttr('%s.stringTest' % node.mNode, type=True)=='string'
        assert mc.getAttr('%s.fltTest' % node.mNode, type=True)=='double'
        assert mc.getAttr('%s.intTest' % node.mNode, type=True)=='long'
        assert mc.getAttr('%s.boolTest' % node.mNode, type=True)=='bool'
        assert mc.getAttr('%s.enum' % node.mNode, type=True)=='enum'
        assert mc.getAttr('%s.jsonTest' % node.mNode, type=True)=='string'
        
        assert mc.getAttr('%s.stringTest' % node.mNode)=='this_is_a_string'
        assert mc.getAttr('%s.fltTest' % node.mNode)==1.333
        assert mc.getAttr('%s.intTest' % node.mNode)==3
        assert mc.getAttr('%s.boolTest' % node.mNode)==False
        assert mc.getAttr('%s.enum' % node.mNode)==0
        assert mc.getAttr('%s.jsonTest' % node.mNode)=='{"jsonFloat": 1.05, "jsonBool": true, "jsonString": "string says hello", "jsonInt": 3}'
        
        #now check the MetaClass __getattribute__ and __setattr__ calls
        #--------------------------------------------------------------
        assert node.intTest==3       
        node.intTest=10     #set back to the MayaNode
        assert node.intTest==10
        #float
        assert node.fltTest==1.333
        node.fltTest=3.55   #set the float attr
        assert node.fltTest==3.55
        #string
        assert node.stringTest=='this_is_a_string'
        node.stringTest="change the text"   #set the string attr
        assert node.stringTest=='change the text'
        #bool
        assert node.boolTest==False
        node.boolTest=True  #set bool
        assert node.boolTest==True
        #enum
        assert node.enum==0
        node.enum='B'
        assert node.enum==1
        node.enum=2
        assert node.enum==2
        #json string handlers
        assert type(node.jsonTest)==dict
        assert node.jsonTest=={'jsonFloat':1.05,'jsonInt':3,'jsonString':'string says hello','jsonBool':True}
        assert node.jsonTest['jsonFloat']==1.05
        assert node.jsonTest['jsonInt']==3 
        assert node.jsonTest['jsonString']=='string says hello'
        assert node.jsonTest['jsonBool']==True 
       
        del(node.boolTest)
        assert mc.objExists(node.mNode)
        assert not node.hasAttr('boolTest')
        assert not mc.attributeQuery('boolTest',node=node.mNode,exists=True)
    
    
    def test_longJsonDumps(self):
        '''
        Test the handling of LONG serialized Json data - testing the 16bit string attrTemplate handling
        NOTE: if you set a string to over 32,767 chars and don't lock the attr once made, selecting
        the textField in the AttributeEditor will truncate the data, hence this test!
        '''
        data= "x" * 40000
        self.MClass.addAttr('json_test', data)
        assert len(self.MClass.json_test)==40000
        
        #save the file and reload to ensure the attr is consistent
        mc.file(rename=os.path.join(r9Setup.red9ModulePath(),'tests','testFiles','deleteMe'))
        mc.file(save=True,type='mayaAscii')
        mc.file(new=True,f=True)
        mc.file(os.path.join(r9Setup.red9ModulePath(),'tests','testFiles','deleteMe.ma'),open=True,f=True)
        
        mClass=r9Meta.getMetaNodes()[0]
        assert len(mClass.json_test)

 
    def test_messageAttrHandling(self):
        '''
        test the messageLink handling in the __setattr__ block
        '''
        node=self.MClass
                
        #make sure we collect LONG names for these as all wrappers deal with longName
        cube1=mc.ls(mc.polyCube()[0],l=True)[0]
        cube2=mc.ls(mc.polyCube()[0],l=True)[0]
        cube3=mc.ls(mc.polyCube()[0],l=True)[0]
        cube4=mc.ls(mc.polyCube()[0],l=True)[0]
        cube5=mc.ls(mc.polyCube()[0],l=True)[0]
        cube6=mc.ls(mc.polyCube()[0],l=True)[0]
 
        node.addAttr('msgMultiTest', value=[cube1,cube2], type='message')   #multi Message attr
        node.addAttr('msgSingleTest', value=cube3, type='messageSimple')    #non-multi message attr
        
        assert node.hasAttr('msgMultiTest')
        assert node.hasAttr('msgSingleTest')
        
        assert mc.getAttr('%s.msgMultiTest' % node.mNode, type=True)=='message'
        assert mc.getAttr('%s.msgSingleTest' % node.mNode, type=True)=='message'
        assert mc.attributeQuery('msgMultiTest',node=node.mNode, multi=True)==True
        assert mc.attributeQuery('msgSingleTest',node=node.mNode, multi=True)==False
        
        #NOTE : cmds returns shortName, but all MetaClass attrs are always longName
        assert sorted(mc.listConnections('%s.msgMultiTest' % node.mNode))==['pCube1','pCube2']
        assert mc.listConnections('%s.msgSingleTest' % node.mNode)==['pCube3'] 
   
        assert sorted(node.msgMultiTest)==[cube1,cube2]
        assert node.msgSingleTest==[cube3]
        
        #test the reconnect handler via the setAttr
        node.msgMultiTest=[cube5,cube6]
        assert sorted(node.msgMultiTest)==[cube5,cube6]
        assert sorted(mc.listConnections('%s.msgMultiTest' % node.mNode))==['pCube5','pCube6']
        
        node.msgMultiTest=[cube1,cube2,cube4,cube6]
        assert sorted(node.msgMultiTest)==[cube1,cube2,cube4,cube6]
        assert sorted(mc.listConnections('%s.msgMultiTest' % node.mNode))==['pCube1','pCube2','pCube4','pCube6']
        
        node.msgSingleTest=cube4
        assert node.msgSingleTest==[cube4] 
        assert mc.listConnections('%s.msgSingleTest' % node.mNode)==['pCube4'] #cmds returns a list
        node.msgSingleTest=cube3
        assert node.msgSingleTest==[cube3] 
        assert mc.listConnections('%s.msgSingleTest' % node.mNode)==['pCube3'] #cmds returns a list
        
        

