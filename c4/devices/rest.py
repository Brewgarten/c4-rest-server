"""
REST service device manager
"""
from c4.rest.server import RestServerProcess
from c4.system.deviceManager import (DeviceManagerImplementation, DeviceManagerStatus,
                                     operation)
from c4.utils.logutil import ClassLogger


@ClassLogger
class RESTServer(DeviceManagerImplementation):
    """
    REST server
    """
    def __init__(self, host, name, properties=None):
        super(RESTServer, self).__init__(host, name, properties=properties)
        self.restServerProcess = None

    def handleLocalStartDeviceManager(self, message, envelope):
        """
        Handle :class:`~c4.system.messages.LocalStartDeviceManager` messages

        :param message: message
        :type message: dict
        :param envelope: envelope
        :type envelope: :class:`~c4.system.messages.Envelope`
        """
        self.start()
        return super(RESTServer, self).handleLocalStartDeviceManager(message, envelope)

    def handleLocalStopDeviceManager(self, message, envelope):
        """
        Handle :class:`~c4.system.messages.LocalStopDeviceManager` messages

        :param message: message
        :type message: dict
        :param envelope: envelope
        :type envelope: :class:`~c4.system.messages.Envelope`
        """
        self.stop()
        return super(RESTServer, self).handleLocalStopDeviceManager(message, envelope)

    @operation
    def start(self):
        """
        Start REST server
        """
        if self.restServerProcess and self.restServerProcess.is_alive():
            self.log.error("REST server already started")
        else:
            if self.restServerProcess:
                self.log.info("Start requested after restServerProcess died, cleaning up old process")
                self.stop()
                
            arguments = {
                "node": self.node
            }
            if "port" in self.properties:
                arguments["port"] = self.properties["port"]
            if "ssl_options" in self.properties:
                arguments["ssl_options"] = self.properties["ssl_options"]
            self.restServerProcess = RestServerProcess(**arguments)
            self.restServerProcess.start()

    @operation
    def stop(self):
        """
        Stop REST server
        """
        if self.restServerProcess and self.restServerProcess.is_alive():
            self.restServerProcess.terminate()
            self.restServerProcess.join()
            self.restServerProcess = None

    def handleStatus(self):
        """
        The handler for an incoming Status message.
        """
        isAlive = False
        if self.restServerProcess:
            isAlive = self.restServerProcess.is_alive()
            if not isAlive:
                # Handle case where is_alive() returns None (which is not boolean)
                isAlive = False
        return RESTServerStatus(self.state, isAlive=isAlive)

class RESTServerStatus(DeviceManagerStatus):
    """
    REST server device manager status

    :param state: state
    :type state: :class:`~c4.system.configuration.States`
    :param isAlive: tornado server isAlive
    :type isAlive: boolean
    """
    def __init__(self, state, isAlive=True):
        super(RESTServerStatus, self).__init__()
        self.state = state
        self.isAlive = isAlive
