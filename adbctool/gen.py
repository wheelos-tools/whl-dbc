#!/usr/bin/env python3

###############################################################################
# Copyright 2017 The Apollo Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
###############################################################################

# -*- coding:utf-8 -*-

import sys
import argparse

from adbctool.extract_dbc_meta import extract_dbc_meta
from adbctool.gen_proto_file import gen_proto_file
from adbctool.gen_protocols import gen_protocols
from adbctool.gen_vehicle_controller_and_manager import gen_vehicle_controller_and_manager


def main(args=sys.argv):
    """
        doc string:
    """
    parser = argparse.ArgumentParser(
        description="adbctool is a tool to generate vehicle protocol",
        prog="gen.py")

    parser.add_argument("-f",
                        "--dbc_file",
                        action="store",
                        type=str,
                        required=True,
                        help="")
    parser.add_argument("-t",
                        "--car_type",
                        action="store",
                        type=str,
                        required=True,
                        help="")
    parser.add_argument("-b",
                        "--black_list",
                        action="store",
                        type=list,
                        required=False,
                        default=[],
                        help="")
    parser.add_argument("-s",
                        "--sender_list",
                        action="store",
                        type=list,
                        required=False,
                        default=[],
                        help="")
    parser.add_argument("--sender",
                        action="store",
                        type=str,
                        required=False,
                        default="MAB",
                        help="")
    parser.add_argument("-o",
                        "--output_dir",
                        action="store",
                        type=str,
                        required=False,
                        default="output/",
                        help="")

    args = parser.parse_args(args[1:])

    # TODO(All): refact the parser or use the libraries such as `cantools`
    # extract dbc file meta to an internal config file
    protocol_conf_file = "dbc.yml"
    if not extract_dbc_meta(args.dbc_file, protocol_conf_file, args.car_type,
                            args.black_list, args.sender_list, args.sender):
        return

    # gen proto
    proto_dir = args.output_dir + "proto/"
    gen_proto_file(protocol_conf_file, proto_dir)

    # gen protocol
    protocol_dir = args.output_dir + "vehicle/" + \
        args.car_type.lower() + "/protocol/"
    gen_protocols(protocol_conf_file, protocol_dir)

    # gen vehicle controller and protocol_manager
    vehicle_dir = args.output_dir + "vehicle/" + args.car_type.lower() + "/"
    gen_vehicle_controller_and_manager(protocol_conf_file, vehicle_dir)
