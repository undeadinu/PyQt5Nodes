 # -*- coding: utf-8 -*-
# !/usr/bin/env python3

from PyQt5.QtCore import QObject, QUuid, pyqtSignal

from PyQt5Nodes.Serializable import *
from PyQt5Nodes.PortType import *
from PyQt5Nodes.ConnectionGeometry import *
from PyQt5Nodes.ConnectionState import *
from PyQt5Nodes.NodeGraphicsObject import *
from PyQt5Nodes.ConnectionGraphicsObject import *

import PyQt5Nodes.Node
from PyQt5Nodes.Node import *


##----------------------------------------------------------------------------
class Connection(QObject, Serializable):
    def __init__(self, *args):
        QObject.__init__(self)

        self._id = None
        self._inNode = None
        self._outNode = None
        self._outPortIndex = INVALID
        self._inPortIndex = INVALID
        self._connectionState = ConnectionState()
        self._connectionGeometry = ConnectionGeometry()

        # method overload
        signature = tuple(arg.__class__ for arg in args)

        from PyQt5Nodes.Node import Node
        NodeCls = PyQt5Nodes.Node

        typemap = {(PortType, NodeCls, PortIndex) : self.connectionPorts,
                    (Node, PortIndex, NodeCls, PortIndex) : self.connectionNodes }

        if signature in typemap:
            return typemap[signature](*args)
        else:
            raise TypeError("Invalid type signature: {0}".format(signature))

    #-------------------------------------------------------------------------
    def connectionPorts(self, portType, node, portIndex):
        self._id = QUuid.createUuid()

        self._outPortIndex = INVALID
        self._inPortIndex = INVALID
        self._connectionState = ConnectionState()

        self.setNodeToPort(node, portType, portIndex)
        self.setRequiredPort(oppositePort(portType))

    #-------------------------------------------------------------------------
    def connectionNodes(self, nodeIn, portIndexIn, nodeOut, portIndexOut):
        self._id = QUuid.createUuid()

        self._outNode = (nodeOut)
        self._inNode = (nodeIn)
        self._outPortIndex = portIndexOut
        self._inPortIndex = portIndexIn
        self._connectionState = ConnectionState()

        self.setNodeToPort(nodeIn, PortType.In, portIndexIn)
        self.setNodeToPort(nodeOut, PortType.Out, portIndexOut)

    #-------------------------------------------------------------------------
    def __del__(self):
        self.propagateEmptyData()

        if(self._inNode):
            self._inNode.nodeGraphicsObject().update()

        if(self._outNode):
            self._outNode.nodeGraphicsObject().update()
            
    #-------------------------------------------------------------------------
    def save(self) -> dict:
        connectionJson = dict()

        if(self._inNode and self._outNode):

            connectionJson["in_id"] = self._inNode.id().toString()
            connectionJson["in_index"] = self._inPortIndex

            connectionJson["out_id"] = self._outNode.id().toString()
            connectionJson["out_index"] = self._outPortIndex

        return connectionJson

    #-------------------------------------------------------------------------
    def id(self) -> QUuid:
        return self._id

    #-------------------------------------------------------------------------
    def setRequiredPort(self, dragging):
        self._connectionState.setRequiredPort(dragging)

        if(dragging == PortType.Out):
            self._outNode = None
            self._outPortIndex = INVALID
        elif(dragging == PortType.In):
            self._inNode = None
            self._inPortIndex = INVALID
        else:
            Q_UNREACHABLE();

    #-------------------------------------------------------------------------
    def requiredPort(self):
        return self._connectionState.requiredPort()

    #-------------------------------------------------------------------------
    def setGraphicsObject(self, graphics: ConnectionGraphicsObject):
        self._connectionGraphicsObject = graphics

        # // This function is only called when the ConnectionGraphicsObject
        # // is newly created. At this moment both end coordinates are (0, 0)
        # // in Connection G.O. coordinates. The position of the whole
        # // Connection G. O. in scene coordinate system is also (0, 0).
        # // By moving the whole object to the Node Port position
        # // we position both connection ends correctly.

        if(self.requiredPort() != PortType.No_One):

            attachedPort = oppositePort(self.requiredPort())

            attachedPortIndex = self.getPortIndex(attachedPort)

            node = self.getNode(attachedPort)

            nodeSceneTransform =node.nodeGraphicsObject().sceneTransform()

            pos = node.nodeGeometry().portScenePosition(attachedPortIndex,
                                                        attachedPort,
                                                        nodeSceneTransform)

            self._connectionGraphicsObject.setPos(pos)

        self._connectionGraphicsObject.move()

    #-------------------------------------------------------------------------
    def getPortIndex(self, portType):
        if(portType == PortType.In):
            return self._inPortIndex
        elif(portType == PortType.Out):
            return self._outPortIndex
        else:
            return INVALID

    #-------------------------------------------------------------------------
    def setNodeToPort(self, node, portType, portIndex):
        if(portType == PortType.In):
            self._inNode = node
        elif(portType == PortType.Out):
            self._outNode = node
        else:
            Q_UNREACHABLE()

        if(portType == PortType.Out):
            self._outPortIndex = portIndex
        elif(portType == PortType.In):
            self._inPortIndex = portIndex
        else:
            Q_UNREACHABLE()

        self._connectionState.setNoRequiredPort()

        self.updated.emit(self)

    #-------------------------------------------------------------------------
    def removeFromNodes(self):
        if(self._inNode):
            self._inNode.nodeState().eraseConnection(PortType.In, self._inPortIndex, self.id())

        if(self._outNode):
            self._outNode.nodeState().eraseConnection(PortType.Out, self._outPortIndex, self.id())

    #-------------------------------------------------------------------------
    def getConnectionGraphicsObject(self):
        return self._connectionGraphicsObject

    #-------------------------------------------------------------------------
    def connectionState(self):
        return self._connectionState

    #-------------------------------------------------------------------------
    def connectionGeometry(self):
        return self._connectionGeometry

    #-------------------------------------------------------------------------
    def getNode(self, portType):
        if(portType == PortType.In):
            return self._inNode
        elif(portType == PortType.Out):
            return self._outNode
        else:
            return None

    #-------------------------------------------------------------------------
    def clearNode(self, portType):
        if(portType == PortType.In):
            self._inNode = None
            self._inPortIndex = INVALID
        elif(portType == PortType.Out):
            self._outNode = None
            self._outPortIndex = INVALID


    #-------------------------------------------------------------------------
    def dataType(self):
        if(self._inNode):
            index = self._inPortIndex
            portType = PortType.In
            validNode = self._inNode
        elif(self._outNode):
            index = self._outPortIndex
            portType = PortType.Out
            validNode = self._outNode

        if(validNode):
            model = validNode.nodeDataModel()

            return model.dataType(portType, index)

        Q_UNREACHABLE();

    #-------------------------------------------------------------------------
    def propagateData(self, nodeData):
        if(self._inNode):
            self._inNode.propagateData(nodeData, self._inPortIndex)

    #-------------------------------------------------------------------------
    def propagateEmptyData(self):
        emptyData = NodeData()
        self.propagateData(emptyData)

    #-------------------------------------------------------------------------
    #signals
    updated = pyqtSignal(object,  name="updatedConn")


##----------------------------------------------------------------------------



