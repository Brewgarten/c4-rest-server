"""
Copyright (c) IBM 2015-2017. All Rights Reserved.
Project name: c4-rest-server
This project is licensed under the MIT License, see LICENSE

REST API request handlers
"""
import json
from tornado import gen

from c4.rest.server import (BaseRequestHandler,
                            route)

@route("/api")
class API(BaseRequestHandler):
    """
    Handles REST requests for api information
    """
    @gen.coroutine
    def get(self):
        """
        Get API information

        @api {get} /api Get information
        @apiName GetAPI
        @apiGroup API

        @apiSuccess (JSON Result) {String} description Description
        """
        data = {
            "description": "information and management interface for C4 clusters"
        }
        response = json.dumps(data, indent=4, sort_keys=True, separators=(',', ': '))
        self.write(response)

@route("/api/")
class APIList(BaseRequestHandler):
    """
    Handles REST requests for api endpoint listings
    """
    @gen.coroutine
    def get(self):
        """
        Get API endpoints

        @api {get} /api/ Get endpoints
        @apiName GetAPIs
        @apiGroup API

        @apiSuccess (JSON Result) {String} description Description
        @apiSuccess (JSON Result) {String[]} names API endpoints
        """
        data = {
            "description": "list of api endpoints",
            "list": [
                "nodes"
            ]
        }
        response = json.dumps(data, indent=4, sort_keys=True, separators=(',', ': '))
        self.write(response)
