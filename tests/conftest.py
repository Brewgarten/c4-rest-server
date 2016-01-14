import json
import logging
import shutil
import tempfile

import pytest
from tornado.httpclient import HTTPClient

from c4.backends.sharedSQLite import SharedSqliteDBBackend
from c4.system.backend import Backend, BackendInfo
from c4.system.configuration import (DeviceInfo,
                                     NodeInfo,
                                     PlatformInfo,
                                     Roles,
                                     States)
from c4.system.manager import SystemManager


logging.basicConfig(format='%(asctime)s [%(levelname)s] <%(processName)s> [%(name)s(%(filename)s:%(lineno)d)] - %(message)s', level=logging.INFO)
log = logging.getLogger(__name__)

@pytest.fixture(scope="session")
def temporaryBackend(request):
    """
    Set backend to something temporary for testing
    """
    # save old backend
    try:
        oldBackend = Backend()
    except ValueError:
        newpath = tempfile.mkdtemp(dir="/dev/shm")
        log.info("setting default temp backend to use '%s' as part of testing", newpath)
        infoProperties = {
            "path.database": newpath,
            "path.backup": newpath
        }
        info = BackendInfo("c4.backends.sharedSQLite.SharedSqliteDBBackend", properties=infoProperties)
        oldBackend = SharedSqliteDBBackend(info)

    newpath = tempfile.mkdtemp(dir="/dev/shm")
#     newpath = tempfile.mkdtemp(dir="/tmp")
    infoProperties = {
        "path.database": newpath,
        "path.backup": newpath
    }
    info = BackendInfo("c4.backends.sharedSQLite.SharedSqliteDBBackend", properties=infoProperties)
    testBackendImplementation = SharedSqliteDBBackend(info)

    # change backend
    newBackend = Backend(implementation=testBackendImplementation)

    def removeTemporaryDirectory():
        # change backend back
        Backend(implementation=oldBackend)
        shutil.rmtree(newpath)
    request.addfinalizer(removeTemporaryDirectory)
    return newBackend

@pytest.fixture
def temporaryIPCPath(request, monkeypatch):
    """
    Create a new temporary directory and set c4.messaging.zeromqMessaging.DEFAULT_IPC_PATH to it
    """
    newpath = tempfile.mkdtemp(dir="/dev/shm")
#     newpath = tempfile.mkdtemp(dir="/tmp")
    monkeypatch.setattr("c4.messaging.zeromqMessaging.DEFAULT_IPC_PATH", newpath)

    def removeTemporaryDirectory():
        shutil.rmtree(newpath)
    request.addfinalizer(removeTemporaryDirectory)
    return newpath

@pytest.fixture(scope="session")
def rest():
    """
    Basic REST client connected to localhost
    """
    class LocalhostClient(HTTPClient):

        def get(self, url):
            response = self.fetch("http://localhost:8888/{0}".format(url.lstrip("/")))
            return json.loads(response.body)

    return LocalhostClient()

@pytest.fixture(scope="session")
def system(request, temporaryBackend):
    """
    Set up a basic system configuration
    """
    configuration = Backend().configuration
    platform = PlatformInfo("im-devops", "c4.system.platforms.devops.IMDevOps")
    configuration.addPlatform(platform)

    node1Info = NodeInfo("node1", "tcp://127.0.0.1:5000", role=Roles.ACTIVE)
    node1Info.addDevice(DeviceInfo("info", "c4.devices.cluster.info.Info"))
    node1Info.addDevice(DeviceInfo("rest-server", "c4.devices.rest.RESTServer"))
    node1Info.addDevice(DeviceInfo("cpu", "c4.devices.cpu.Cpu"))
    node1Info.addDevice(DeviceInfo("unknown", "c4.devices.Unknown"))
    node1Info.addDevice(DeviceInfo("disk", "c4.devices.disk.Disk"))
    node1Info.addDevice(DeviceInfo("memory", "c4.devices.mem.Memory"))

    configuration.addNode(node1Info)
    # TODO: this should automatically set role of the node to active
    configuration.addAlias("system-manager", "node1")

    node2Info = NodeInfo("node2", "tcp://127.0.0.1:6000", role=Roles.PASSIVE)
    node2Info.addDevice(DeviceInfo("cpu", "c4.devices.cpu.Cpu"))
    node2Info.addDevice(DeviceInfo("memory", "c4.devices.mem.Memory"))
    configuration.addNode(node2Info)
    node3Info = NodeInfo("node3", "tcp://127.0.0.1:7000")
    node3Info.addDevice(DeviceInfo("cpu", "c4.devices.cpu.Cpu"))
    node3Info.addDevice(DeviceInfo("memory", "c4.devices.mem.Memory"))
    configuration.addNode(node3Info)
    log.debug(configuration.toInfo().toJSON(pretty=True))

    node1ClusterInfo = temporaryBackend.ClusterInfo("node1", "ipc://node1.ipc", "ipc://node1.ipc", role=Roles.ACTIVE, state=States.DEPLOYED)
    node1 = SystemManager(node1ClusterInfo, name="node1")
    node2ClusterInfo = temporaryBackend.ClusterInfo("node2", "ipc://node2.ipc", "ipc://node1.ipc", role=Roles.PASSIVE, state=States.DEPLOYED)
    node2 = SystemManager(node2ClusterInfo, name="node2")
    node3ClusterInfo = temporaryBackend.ClusterInfo("node3", "ipc://node3.ipc", "ipc://node1.ipc", role=Roles.THIN, state=States.DEPLOYED)
    node3 = SystemManager(node3ClusterInfo, name="node3")

    node1.start()
    node2.start()
    node3.start()

    def systemTeardown():
        node3.stop()
        node2.stop()
        node1.stop()
    request.addfinalizer(systemTeardown)
