"""
author: Martin Weigert
email: mweigert@mpi-cbg.de
"""
import logging
logger = logging.getLogger(__name__)



from PyQt4 import QtCore

from spimagine.transform_matrices import *
from spimagine.quaternion import Quaternion

import numpy as np

from spimagine.keyframe_model import TransformData


class TransformModel(QtCore.QObject):
    _maxChanged = QtCore.pyqtSignal(int)
    _gammaChanged = QtCore.pyqtSignal(float)
    _boxChanged = QtCore.pyqtSignal(int)
    _perspectiveChanged = QtCore.pyqtSignal(int)
    # _rotationChanged = QtCore.pyqtSignal(float,float,float,float)
    _rotationChanged = QtCore.pyqtSignal()
    _dataPosChanged =  QtCore.pyqtSignal(int)
    _transformChanged = QtCore.pyqtSignal()
    _stackUnitsChanged = QtCore.pyqtSignal(float,float,float)

    def __init__(self):
        super(TransformModel,self).__init__()
        self.reset()

    def setModel(self,dataModel):
        self.dataModel = dataModel

    def reset(self,maxVal = 256.,stackUnits=None):
        logger.debug("reset")

        self.quatRot = Quaternion()
        self.translate = [0,0,0]
        self.cameraZ = 5
        self.scaleAll = 1.
        self.zoom = 1.
        self.dataPos = 0
        self.isPerspective = True
        self.setPerspective()
        self.setScale(0,maxVal)
        self.setGamma(1.)
        self.setBox(True)
        if not stackUnits:
            stackUnits = [.1,.1,.1]
        self.setStackUnits(*stackUnits)
        self.update()

    def setPos(self,pos):
        logger.debug("setPos(%s)",pos)
        self.dataPos = pos
        self.dataModel.setPos(pos) 
        self._transformChanged.emit()

    def setGamma(self, gamma):
        logger.debug("setGamma(%s)",gamma)

        self.gamma = gamma
        self._gammaChanged.emit(self.gamma)
        self._transformChanged.emit()

    def setScale(self,minVal,maxVal):
        self.minVal, self.maxVal = minVal, maxVal
        # print "maxVal: ", maxVal
        self._maxChanged.emit(self.maxVal)
        self._transformChanged.emit()


    def setStackUnits(self,px,py,pz):
        self.stackUnits = px,py,pz
        self._stackUnitsChanged.emit(px,py,pz)
        self._transformChanged.emit()

    def setBox(self,isBox = True):
        self.isBox = isBox
        self._boxChanged.emit(isBox)
        self._transformChanged.emit()

    def setZoom(self,zoom = 1.):
        self.zoom = np.clip(zoom,.5,2)
        self.update()

    def setRotation(self,angle,x,y,z):
        self.setQuaternion(Quaternion(np.cos(angle),np.sin(angle)*x,np.sin(angle)*y,np.sin(angle)*z))

    def setQuaternion(self,quat):
        logger.debug("set quaternion to %s",quat.data)
        self.quatRot = Quaternion.copy(quat)
        self._rotationChanged.emit()
        self._transformChanged.emit()


    def update(self):
        if self.isPerspective:
            self.cameraZ = 4*(1-np.log(self.zoom)/np.log(2.))
            self.scaleAll = 1.
        else:
            self.cameraZ = 0.
            self.scaleAll = 2.5**(self.zoom-1.)

    def setPerspective(self, isPerspective = True):
        self.isPerspective = isPerspective
        if isPerspective:
            self.projection = projMatPerspective(60.,1.,.1,10)
        else:
            self.projection = projMatOrtho(-2.,2.,-2.,2.,-1.5,1.5)

        self.update()
        self._perspectiveChanged.emit(isPerspective)
        self._transformChanged.emit()


    def getModelView(self):
        modelView = np.dot(transMatReal(0,0,-self.cameraZ),
                        np.dot(scaleMat(*[self.scaleAll]*3),
        np.dot(transMatReal(*self.translate),self.quatRot.toRotation4())))

        return modelView

    def fromTransformData(self,transformData):
        pass

    def toTransformData(self):
        return TransformData(self.quatRot)