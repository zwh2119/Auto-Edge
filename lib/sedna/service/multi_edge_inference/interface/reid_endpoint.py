# Copyright 2021 The KubeEdge Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pickle
from sedna.core.multi_edge_inference.data_classes import DetTrackResult
from sedna.service.client import http_request


class ReID_Endpoint:
    """Endpoint to trigger the ReID"""

    def __init__(self, service_name, version="",
                 ip="127.0.0.1", port="8080", protocol="http"):
        self.server_name = f"{service_name}{version}"
        self.endpoint = f"{protocol}://{ip}:{port}/{service_name}"

    def check_server_status(self):
        return http_request(url=self.endpoint, method="GET")

    def transmit(self, data: DetTrackResult, **kwargs):
        """Transfer feature vector to ReID worker"""
        _url = f"{self.endpoint}/reid"
        return http_request(url=_url, method="POST", data=pickle.dumps(data))
