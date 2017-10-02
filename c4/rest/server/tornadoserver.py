"""
Copyright (c) IBM 2015-2017. All Rights Reserved.
Project name: c4-rest-server
This project is licensed under the MIT License, see LICENSE

Tornado based REST service implementation
"""
import logging
import multiprocessing
import os
import pkg_resources
import ssl

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
    def __init__(self, node, port=8888, ssl_options=None, ssl_version=ssl.PROTOCOL_TLSv1_2):
        super(RestServerProcess, self).__init__(name="REST server")
        self.node = node
        self.port = int(port)
        self.ssl_options = ssl_options
        self.ssl_version = ssl_version

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
        try:
            handlers = self.getHandlers()
            self.log.info(handlers)
            application = Application(handlers=self.getHandlers())
            application.executor = ThreadPoolExecutor(10)
            ssl_options = None
            if self.ssl_options:
                ssl_enabled = True
                if self.ssl_options["package"]:
                    package = self.ssl_options["package"]
                
                directory = ""
                if self.ssl_options["directory"]:
                    directory = self.ssl_options["directory"]
                
                if self.ssl_options["certfile"]:
                    ssl_certificate_file = self.ssl_options["certfile"]
                    if os.path.dirname(ssl_certificate_file) == "" and package:
                        ssl_certificate_file = pkg_resources.resource_filename(package, directory + ssl_certificate_file)  # @UndefinedVariable
                
                if self.ssl_options["keyfile"]:
                    ssl_key_file = self.ssl_options["keyfile"]
                    if os.path.dirname(ssl_key_file) == "" and package:
                        ssl_key_file = pkg_resources.resource_filename(package, directory + ssl_key_file)  # @UndefinedVariable        
                
                if not os.path.exists(ssl_certificate_file):
                    self.log.error("SSL certificate file not found at location: %s", ssl_certificate_file)
                    ssl_enabled = False
                    
                if not os.path.exists(ssl_key_file):
                    self.log.error("SSL key file not found at location: %s", ssl_key_file)
                    ssl_enabled = False
                    
                if not self.ssl_version:    
                    self.log.error("SSL version not specified")
                    ssl_enabled = False
                
                if ssl_enabled:
                    ssl_options = {
                        "ssl_version": self.ssl_version,
                        "certfile": ssl_certificate_file,
                        "keyfile": ssl_key_file
                    }
                    self.log.info(ssl_options)
                else:
                    self.log.warning("SSL options specified but unable to enable SSL for REST server")    
    
            restServer = HTTPServer(application, ssl_options=ssl_options)
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
