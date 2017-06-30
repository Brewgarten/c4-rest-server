"""
REST API nodes request handlers

"""
import json
from tornado import gen

from c4.rest.server import (BaseRequestHandler,
                            route)
from c4.system.backend import Backend
from c4.utils.jsonutil import JSONSerializable
from c4.utils.logutil import ClassLogger


class NodeMap(JSONSerializable):
    """
    Node map information
    """

    def add(self, nodeInfo):
        """
        Add node info

        :param nodeInfo: node info
        :type nodeInfo: :class:`~c4.system.configuration.NodeInfo`
        """
        setattr(self, nodeInfo.name, nodeInfo)

@ClassLogger
@route("/api/nodes")
class Nodes(BaseRequestHandler):
    """
    Handles REST requests for node information
    """
    @gen.coroutine
    def get(self):
        """
        Get information on all nodes in the cluster

        ..
            @api {get} /api/nodes Get information on all nodes
            @apiName GetNodes
            @apiGroup Nodes
        """
        includeClassInfo = self.get_query_argument("includeClassInfo", "", strip=True).lower() in ["true"]

        nodeMap = NodeMap()

        def getNodeNames():
            """
            Get node names
            """
            configuration = Backend().configuration
            return configuration.getNodeNames()
        nodeNames = yield self.executor.submit(getNodeNames)

        def getNode(node, includeDevices=True, flatDeviceHierarchy=False):
            """
            Get node information
            """
            configuration = Backend().configuration
            return configuration.getNode(node, includeDevices=includeDevices, flatDeviceHierarchy=flatDeviceHierarchy)
        for node in nodeNames:
            nodeInfo = yield self.executor.submit(getNode, node, includeDevices=False)
            if nodeInfo:
                nodeMap.add(nodeInfo)
            else:
                self.log.error("could not retrieve node information for '%s'", node)

        self.write(nodeMap.toJSON(includeClassInfo=includeClassInfo, pretty=True))
        self.set_header("Content-Type", "application/json; charset=UTF-8")

@ClassLogger
@route("/api/nodes/")
class NodeList(BaseRequestHandler):
    """
    Handles REST requests for listing nodes
    """
    @gen.coroutine
    def get(self):
        """
        Outputs a dictionary that has a key called "nodes"
        and a value that is a list of nodes.

        ..
            @api {get} /nodes Get nodes
            @apiName GetNodes
            @apiGroup Nodes

            @apiSuccess {String[]} nodes       List of nodes
            @apiSuccessExample {json} Success-Response:
                HTTP/1.1 200 OK
                {
                    "nodes": ["node1", "node2"]
                }
        """
        def getNodeNames():
            """
            Get node names
            """
            configuration = Backend().configuration
            return configuration.getNodeNames()
        nodeNames = yield self.executor.submit(getNodeNames)

        data = {
            "description": "list of nodes",
            "list": nodeNames
        }
        response = json.dumps(data, indent=4, sort_keys=True, separators=(',', ': '))
        self.write(response)
