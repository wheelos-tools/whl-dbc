#!/usr/bin/env python3

# Copyright 2026 The WheelOS Team. All Rights Reserved.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Created Date: 2026-02-27
# Author: daohu527

import os
import tempfile
import unittest

import yaml

from adbctool.gen_proto_file import gen_proto_file
from adbctool.gen_protocols import gen_protocols
from adbctool.gen_vehicle_controller_and_manager import gen_vehicle_controller_and_manager


def _sample_protocol_config():
    return {
        "car_type": "testcar",
        "can_interface": "socketcan",
        "protocols": {
            "100": {
                "id": "100",
                "name": "steer_cmd_100",
                "sender": "ADAS",
                "protocol_type": "control",
                "vars": [
                    {
                        "name": "STEER_EN",
                        "bit": 0,
                        "len": 1,
                        "order": "intel",
                        "is_signed_var": False,
                        "offset": 0.0,
                        "precision": 1.0,
                        "physical_range": "[0|1]",
                        "physical_unit": "",
                        "type": "bool",
                    }
                ],
            },
            "101": {
                "id": "101",
                "name": "steer_status_101",
                "sender": "EPS",
                "protocol_type": "report",
                "vars": [
                    {
                        "name": "STEER_ANGLE",
                        "bit": 0,
                        "len": 8,
                        "order": "intel",
                        "is_signed_var": False,
                        "offset": 0.0,
                        "precision": 1.0,
                        "physical_range": "[0|255]",
                        "physical_unit": "deg",
                        "type": "int",
                    }
                ],
            },
        },
    }


class TestGenerationPipeline(unittest.TestCase):

    def test_generate_proto_file_from_config(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_file = os.path.join(tmp_dir, "dbc.yml")
            with open(config_file, "w") as fp:
                yaml.safe_dump(_sample_protocol_config(), fp)

            proto_dir = os.path.join(tmp_dir, "proto")
            gen_proto_file(config_file, proto_dir)

            proto_file = os.path.join(proto_dir, "testcar.proto")
            self.assertTrue(os.path.exists(proto_file))
            with open(proto_file, "r") as fp:
                content = fp.read()

            self.assertIn("message Steer_cmd_100", content)
            self.assertIn("message Steer_status_101", content)
            self.assertIn("// control message", content)
            self.assertIn("// report message", content)

    def test_generate_protocols_and_vehicle_manager_files(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_file = os.path.join(tmp_dir, "dbc.yml")
            with open(config_file, "w") as fp:
                yaml.safe_dump(_sample_protocol_config(), fp)

            protocol_dir = os.path.join(
                tmp_dir, "vehicle", "testcar", "protocol") + "/"
            gen_protocols(config_file, protocol_dir)

            self.assertTrue(os.path.exists(
                os.path.join(protocol_dir, "steer_cmd_100.h")))
            self.assertTrue(os.path.exists(
                os.path.join(protocol_dir, "steer_cmd_100.cc")))
            self.assertTrue(os.path.exists(
                os.path.join(protocol_dir, "steer_status_101.h")))
            self.assertTrue(os.path.exists(os.path.join(
                protocol_dir, "steer_status_101.cc")))
            self.assertTrue(os.path.exists(
                os.path.join(protocol_dir, "BUILD")))

            vehicle_dir = os.path.join(tmp_dir, "vehicle", "testcar") + "/"
            gen_vehicle_controller_and_manager(config_file, vehicle_dir)

            self.assertTrue(os.path.exists(os.path.join(
                vehicle_dir, "testcar_controller.h")))
            self.assertTrue(os.path.exists(os.path.join(
                vehicle_dir, "testcar_controller.cc")))
            self.assertTrue(os.path.exists(os.path.join(
                vehicle_dir, "testcar_message_manager.h")))
            self.assertTrue(os.path.exists(os.path.join(
                vehicle_dir, "testcar_message_manager.cc")))
            self.assertTrue(os.path.exists(os.path.join(
                vehicle_dir, "testcar_vehicle_factory.h")))
            self.assertTrue(os.path.exists(os.path.join(
                vehicle_dir, "testcar_vehicle_factory.cc")))
            self.assertTrue(os.path.exists(os.path.join(vehicle_dir, "BUILD")))


if __name__ == '__main__':
    unittest.main()
