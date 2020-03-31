#!/usr/bin/env python
#
# Copyright (c) 2016, PagerDuty, Inc. <info@pagerduty.com>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of PagerDuty Inc nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL PAGERDUTY INC BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from datetime import datetime
import json
import os
import requests
import logging

logger = logging.getLogger(__name__)


class PagerDutyREST():
    """Class to handle all calls to the PagerDuty API"""

    def __init__(self, access_token):
        self.base_url = 'https://api.pagerduty.com'
        self.headers = {
            'Accept': 'application/vnd.pagerduty+json;version=2',
            'Authorization': 'Token token={token}'.format(token=access_token)
        }

    def get(self, endpoint, payload={}, resource=None):
        """Handle all GET requests"""

        url = '{base_url}{endpoint}'.format(
            base_url=self.base_url,
            endpoint=endpoint
        )
        payload['limit'] = 100
        r = requests.get(url, params=payload, headers=self.headers)
        if r.status_code == 200:
            r = r.json()
            # Handle pagination if over 100 resources returned
            # Try/except for cases where getting a single resource
            try:
                if r['more']:
                    payload['offset'] = 100
                    output = r
                    while r['more']:
                        logger.info('GET pagination...')
                        r = requests.get(
                            url,
                            params=payload,
                            headers=self.headers
                        ).json()
                        for i in r[resource]:
                            output[resource].append(i)
                        payload['offset'] += 100
                    r = output
                return r
            except:
                return r
        else:
            raise Exception(
                'There was an issue with your GET request:\nStatus code: {code}\
                \nError: {error}'.format(code=r.status_code, error=r.text)
            )

    def put(self, endpoint, payload=None, from_header=None):
        """Handle all PUT requests"""

        url = '{base_url}{endpoint}'.format(
            base_url=self.base_url,
            endpoint=endpoint
        )
        headers = dict(self.headers)
        headers['Content-Type'] = 'application/json'
        if from_header:
            headers['From'] = from_header
        if payload:
            r = requests.put(
                url,
                data=json.dumps(payload),
                headers=headers
            )
        else:
            r = requests.put(url, headers=headers)
        if r.status_code == 200 or r.status_code == 204:
            return r.status_code
        else:
            raise Exception(
                'There was an issue with your PUT request:\nStatus code: {code}\
                \nError: {error}'.format(code=r.status_code, error=r.text)
            )

    def delete(self, endpoint):
        """Handle all DELETE requests"""

        url = '{base_url}{endpoint}'.format(
            base_url=self.base_url,
            endpoint=endpoint
        )
        r = requests.delete(url, headers=self.headers)
        if r.status_code == 204:
            return r.status_code
        else:
            raise Exception(
                'There was an issue with your DELETE request:\nStatus code: {code}\
                \nError: {error}'.format(code=r.status_code, error=r.text)
            )

    def post(self, endpoint, payload, from_header=None):
        """Handle all POST requests"""

        url = '{base_url}{endpoint}'.format(
            base_url=self.base_url,
            endpoint=endpoint
        )
        headers = dict(self.headers)
        headers['Content-Type'] = 'application/json'
        if from_header:
            headers['From'] = from_header
        r = requests.post(url, headers=headers, data=json.dumps(payload))
        if r.status_code == 201:
            return r.json()
        else:
            raise Exception(
                'There was an issue with your POST request:\nStatus code: {code}\
                \nError: {error}'.format(code=r.status_code, error=r.text)
            )
