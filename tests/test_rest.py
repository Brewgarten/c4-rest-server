import logging

import pytest

from c4.system.configuration import (Roles,
                                     States)


log = logging.getLogger(__name__)

pytestmark = pytest.mark.usefixtures("temporaryIPCPath")

@pytest.mark.usefixtures("system")
class TestAPI(object):

    def test_getAPI(self, rest):

        response = rest.get("/api")

        assert "description" in response

    def test_getAPIList(self, rest):

        response = rest.get("/api/")

        assert "description" in response
        assert response["list"] == ["nodes"]

@pytest.mark.usefixtures("system")
class TestNodes(object):

    def test_getNodeList(self, rest):

        response = rest.get("/api/nodes/")

        assert response["list"] == ["node1", "node2", "node3"]

    def test_getNodes(self, rest):

        response = rest.get("/api/nodes")

        assert response["node1"]["name"] == "node1"
        assert Roles.valueOf(response["node1"]["role"]) == Roles.ACTIVE
        assert States.valueOf(response["node1"]["state"]) == States.RUNNING

        assert response["node2"]["name"] == "node2"
        assert Roles.valueOf(response["node2"]["role"]) == Roles.PASSIVE
        assert States.valueOf(response["node2"]["state"]) == States.RUNNING

        assert response["node3"]["name"] == "node3"
        assert Roles.valueOf(response["node3"]["role"]) == Roles.THIN
        assert States.valueOf(response["node3"]["state"]) == States.RUNNING
