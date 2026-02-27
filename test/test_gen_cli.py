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

import unittest
from unittest.mock import patch

from adbctool import gen


class TestGenCli(unittest.TestCase):

    def test_requires_sender_or_sender_list(self):
        with self.assertRaises(SystemExit):
            gen.main(["gen.py", "-f", "a.dbc", "-t", "testcar"])

    @patch("adbctool.gen.gen_vehicle_controller_and_manager")
    @patch("adbctool.gen.gen_protocols")
    @patch("adbctool.gen.gen_proto_file")
    @patch("adbctool.gen.extract_dbc_meta")
    def test_happy_path_invokes_all_generators(self, mock_extract,
                                               mock_gen_proto,
                                               mock_gen_protocols,
                                               mock_gen_vehicle):
        mock_extract.return_value = True

        gen.main([
            "gen.py", "-f", "a.dbc", "-t", "testcar", "--sender", "ADAS",
            "-o", "out/"
        ])

        mock_extract.assert_called_once_with(
            "a.dbc", "dbc.yml", "testcar", [], [], "ADAS"
        )
        mock_gen_proto.assert_called_once_with("dbc.yml", "out/proto/")
        mock_gen_protocols.assert_called_once_with(
            "dbc.yml", "out/vehicle/testcar/protocol/"
        )
        mock_gen_vehicle.assert_called_once_with(
            "dbc.yml", "out/vehicle/testcar/"
        )

    @patch("adbctool.gen.gen_vehicle_controller_and_manager")
    @patch("adbctool.gen.gen_protocols")
    @patch("adbctool.gen.gen_proto_file")
    @patch("adbctool.gen.extract_dbc_meta")
    def test_stops_when_extract_failed(self, mock_extract,
                                       mock_gen_proto,
                                       mock_gen_protocols,
                                       mock_gen_vehicle):
        mock_extract.return_value = False

        gen.main([
            "gen.py", "-f", "a.dbc", "-t", "testcar", "--sender", "ADAS"
        ])

        mock_gen_proto.assert_not_called()
        mock_gen_protocols.assert_not_called()
        mock_gen_vehicle.assert_not_called()


if __name__ == '__main__':
    unittest.main()
