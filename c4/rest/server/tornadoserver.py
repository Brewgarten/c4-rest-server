"""
Tornado based REST service implementation
"""
import logging
import multiprocessing

from concurrent.futures import ThreadPoolExecutor
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.web import Application, RequestHandler

import c4.rest.handlers
from c4.utils.logutil import ClassLogger
from c4.utils.util import getModuleClasses


log = logging.getLogger(__name__)

class BaseRequestHandler(RequestHandler):
    """
    Base request handler
    """
    @property
    def executor(self):
        """
        Executor for long-running/blocking tasks
        """
        return self.application.executor

    def initialize(self, node): # pylint: disable=arguments-differ
        """
        Information shared across request handlers

        :param node: node
        :type node: str
        """
        self.node = node

@ClassLogger
class RestServerProcess(multiprocessing.Process):
    """
    REST server process

    :param node: node
    :type node: str
    :param port: port number
    :type port: int
    """
    def __init__(self, node, port=8888):
        super(RestServerProcess, self).__init__(name="REST server")
        self.node = node
        self.port = int(port)

    def getHandlers(self):
        """
        Get a list of handlers with their route information

        :returns: list of route and handler tuples
        :rtype: (route, handler, <initialization dict>)
        """
        routeMap = getRouteMap()
        return [
            (actualRoute, handler, dict(node=self.node))
            for actualRoute, handler in sorted(routeMap.items())
        ]

    def run(self):
        """
        The implementation of the REST server process
        """
        application = Application(handlers=self.getHandlers())
        application.executor = ThreadPoolExecutor(10)
        restServer = HTTPServer(application)
        try:
            restServer.listen(self.port)
            IOLoop.current().start()
        except KeyboardInterrupt:
            self.log.info("Exiting..")
        except Exception as exception:
            self.log.info("Forced exiting..")
            self.log.exception(exception)

def getRouteMap():
    """
    Retrieve route to handler map by looking for request handlers
    extending the :class:`BaseRequestHandler` and decorated with ``route``

    :returns: route to handler map
    :rtype: dict
    """
    restHandlers = sorted(getModuleClasses(c4.rest.handlers, BaseRequestHandler))

    # remove base class
    if BaseRequestHandler in restHandlers:
        restHandlers.remove(BaseRequestHandler)

    routeMap = {}
    for handler in restHandlers:
        if hasattr(handler, "route"):
            if handler.route in routeMap:
                log.error("Route '%s' for REST handler '%s' conflicts with handler '%s'",
                          handler.route, handler, routeMap[handler.route])
            else:
                routeMap[handler.route] = handler
        else:
            log.error("REST handler '%s' is missing route", handler)

    return routeMap

def route(path):
    """
    Route decorator to be used on request handler classes that
    should be exposed externally through REST

    :param cls: a request handler class
    :returns: a request handler class decorated with additional route information
    """
    def routeDecorator(cls):
        """
        Route decorator implementation
        """
        cls.route = path
        return cls
    return routeDecorator
