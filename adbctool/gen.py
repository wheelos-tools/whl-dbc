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
import ast

from adbctool.extract_dbc_meta import extract_dbc_meta
from adbctool.gen_proto_file import gen_proto_file
from adbctool.gen_protocols import gen_protocols
from adbctool.gen_vehicle_controller_and_manager import gen_vehicle_controller_and_manager


def main(args=sys.argv):
    """
    Main function to generate vehicle protocol files from a DBC file.
    It parses arguments, validates them, and then orchestrates the generation process.
    """
    parser = argparse.ArgumentParser(
        description="A tool to generate Apollo vehicle protocol from a DBC file.",
        prog="gen.py",
        formatter_class=argparse.RawTextHelpFormatter
    )

    # --- Required Arguments ---
    parser.add_argument("-f", "--dbc_file",
                        action="store",
                        type=str,
                        required=True,
                        help="Specify the path to the input DBC file.")
    parser.add_argument("-t", "--car_type",
                        action="store",
                        type=str,
                        required=True,
                        help="Specify the car type or name (e.g., LINCOLN_MKZ_2017).")

    # --- Control Message Definition (User must choose one of the following) ---
    control_group = parser.add_argument_group(
        'Control Message Definition (Choose ONE method)',
        'Define which CAN messages are control commands.'
    )
    control_group.add_argument("--sender",
                               action="store",
                               type=str,
                               default=None,  # Default to None to check if it was provided
                               help="""The name of the node (ECU) that sends control messages.
All messages from this sender will be marked as control messages.
(e.g., --sender MAB)""")
    control_group.add_argument("--sender_list",
                               action="store",
                               type=str,      # Receive as string, parse to list later
                               default=None,  # Default to None
                               help="""A Python-style list of CAN message IDs (as strings) for control.
Use this for fine-grained control or when commands come from multiple ECUs.
(e.g., --sender_list "['0x180', '0x25A']")""")

    # --- Optional Arguments ---
    parser.add_argument("-b", "--black_list",
                        action="store",
                        type=str,      # Receive as string
                        default='[]',  # Default to a string representation of an empty list
                        help="A Python-style list of message names to exclude from processing.")
    parser.add_argument("-o", "--output_dir",
                        action="store",
                        type=str,
                        default="output/",
                        help="Specify the directory to save the generated files (default: ./output/).")

    parsed_args = parser.parse_args(args[1:])

    # --- Argument Validation ---
    if parsed_args.sender is None and parsed_args.sender_list is None:
        parser.error(
            "You must define the source of control messages. Please provide either --sender or --sender_list.")

    # Safely parse string arguments into Python lists
    try:
        black_list = ast.literal_eval(parsed_args.black_list)
        sender_list = ast.literal_eval(
            parsed_args.sender_list) if parsed_args.sender_list else []
    except (ValueError, SyntaxError) as e:
        print(f"Error: Invalid list format for --black_list or --sender_list. Please use Python list syntax.", file=sys.stderr)
        print(f"Details: {e}", file=sys.stderr)
        sys.exit(1)

    # --- Generation Logic ---
    print("🚀 Starting vehicle protocol generation...")
    protocol_conf_file = "dbc.yml"
    if not extract_dbc_meta(parsed_args.dbc_file, protocol_conf_file, parsed_args.car_type,
                            black_list, sender_list, parsed_args.sender):
        print("❌ Failed to extract DBC meta information.", file=sys.stderr)
        return

    # Generate proto file
    proto_dir = parsed_args.output_dir + "proto/"
    gen_proto_file(protocol_conf_file, proto_dir)

    # Generate protocol files
    protocol_dir = parsed_args.output_dir + "vehicle/" + \
        parsed_args.car_type.lower() + "/protocol/"
    gen_protocols(protocol_conf_file, protocol_dir)

    # Generate vehicle controller and protocol_manager
    vehicle_dir = parsed_args.output_dir + \
        "vehicle/" + parsed_args.car_type.lower() + "/"
    gen_vehicle_controller_and_manager(protocol_conf_file, vehicle_dir)

    print(f"\n✅ Vehicle protocol generation complete!")
    print(f"Files saved in: {parsed_args.output_dir}")


if __name__ == '__main__':
    main()
