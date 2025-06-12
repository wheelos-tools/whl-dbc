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

import re
import shlex
import sys
import yaml
import chardet
import codecs

MAX_CAN_ID = 4096000000  # include can extended ID
STANDARD_CAN_ID = 2048


def extract_var_info(items):
    """
       Desp: extract var info from line split items.
    """
    car_var = {}
    car_var["name"] = items[1]
    car_var["bit"] = int(items[3].split('|')[0])
    car_var["len"] = int(items[3].split('|')[1].split('@')[0])
    order_sign = items[3].split('|')[1].split('@')[1]
    if order_sign == "0+":
        car_var["order"] = "motorola"
        car_var["is_signed_var"] = False
    elif order_sign == "0-":
        car_var["order"] = "motorola"
        car_var["is_signed_var"] = True
    elif order_sign == "1+":
        car_var["order"] = "intel"
        car_var["is_signed_var"] = False
    elif order_sign == "1-":
        car_var["order"] = "intel"
        car_var["is_signed_var"] = True
    car_var["offset"] = float(items[4].split(',')[1].split(')')[0])
    car_var["precision"] = float(items[4].split(',')[0].split('(')[1])
    car_var["physical_range"] = items[5]
    car_var["physical_unit"] = items[6].replace('_', ' ')
    if car_var["len"] == 1:
        car_var["type"] = "bool"
    elif car_var["physical_range"].find(
            ".") != -1 or car_var["precision"] != 1.0:
        car_var["type"] = "double"
    else:
        car_var["type"] = "int"

    return car_var


def detect_file_encoding(file_path,
                         default_encoding='utf-8',
                         confidence_threshold=0.5):
    """Detect file encoding

    Args:
        file_path (_type_): _description_
        default_encoding (str, optional): _description_. Defaults to 'utf-8'.
        confidence_threshold (float, optional): _description_. Defaults to 0.5.

    Returns:
        _type_: _description_
    """
    with open(file_path, 'rb') as f:
        raw_data = f.read()
        result = chardet.detect(raw_data)

        encoding = result['encoding']
        confidence = result['confidence']

        if confidence < confidence_threshold or encoding is None:
            return default_encoding, confidence
        else:
            return encoding, confidence


def parse_signal_comment(items, protocols):
    """
    Parse a signal comment line from the DBC file.
    """
    protocol_id = "%x" % int(items[2])
    if int(items[2]) > MAX_CAN_ID:
        return
    if int(items[2]) > STANDARD_CAN_ID:
        protocol_id = gen_can_id_extended(protocol_id)
    for var in protocols[protocol_id]["vars"]:
        if var["name"] == items[3]:
            var["description"] = items[4][:-1]


def parse_enum_values(items, protocols):
    """
    Parse enumeration values from the DBC file.
    """
    protocol_id = "%x" % int(items[1])
    if int(items[1]) > MAX_CAN_ID:
        return
    if int(items[1]) > STANDARD_CAN_ID:
        protocol_id = gen_can_id_extended(protocol_id)
    for var in protocols[protocol_id]["vars"]:
        if var["name"] == items[2]:
            var["type"] = "enum"
            var["enum"] = {}
            for idx in range(3, len(items) - 1, 2):
                enumtype = re.sub('\W+', ' ',
                                  items[idx + 1]).strip().replace(" ",
                                                                  "_").upper()
                enumtype = f"{items[2].upper()}_{enumtype}"
                var["enum"][int(items[idx])] = enumtype


def parse_message_cycle_time(items, protocols):
    """Parse message cycle time from the DBC file.
    """
    protocol_id = '%x' % int(items[3])
    if int(items[3]) > MAX_CAN_ID:
        return
    if int(items[3]) > STANDARD_CAN_ID:
        protocol_id = gen_can_id_extended(protocol_id)
    period = items[4].rstrip(' ;')
    protocols[protocol_id]['period'] = period


def adjust_reserved_keywords(protocols):
    """
    Adjust variable names that are reserved C++ keywords.
    """
    CPP_RESERVED_KEYWORDS = ['minor', 'major', 'long', 'int']
    for protocol in protocols.values():
        for var in protocol["vars"]:
            if var["name"].lower() in CPP_RESERVED_KEYWORDS:
                var["name"] = f"MY_{var['name']}"


def log_summary(car_type, out_file, protocols):
    """
    Log a summary of the parsed protocols.
    """
    control_protocol_num = sum(1 for p in protocols.values()
                               if p["protocol_type"] == "control")
    report_protocol_num = sum(1 for p in protocols.values()
                              if p["protocol_type"] == "report")

    print(
        f"Extracted car_type: {car_type.upper()}'s protocol meta info to file: {out_file}"
    )
    print(f"Total parsed protocols: {len(protocols)}")
    print(f"Control protocols: {control_protocol_num}")
    print(f"Report protocols: {report_protocol_num}")


def extract_dbc_meta(dbc_file, out_file, car_type, black_list, sender_list,
                     sender):
    """
        the main gen_config func, use dbc file to gen a yaml file
        parse every line, if the line is:
        eg:BO_ 1104 BMS_0x450: 8 VCU
        5 segments, and segments[0] is "BO_", then begin parse every signal in the following line

    """
    sender_list = set(map(str, sender_list))

    # Get the file character encoding
    encoding, _ = detect_file_encoding(dbc_file)

    with codecs.open(dbc_file, encoding=encoding) as f:
        in_protocol = False
        protocols = {}
        protocol = {}
        p_name = ""

        try:
            for line_num, line in enumerate(f, start=1):
                items = shlex.split(line)

                if len(items) == 5 and items[0] == "BO_":
                    p_name = items[2][:-1].lower()
                    protocol = {}
                    if int(items[1]) > MAX_CAN_ID:
                        continue
                    protocol["id"] = "%x" % int(items[1])
                    if int(items[1]) > STANDARD_CAN_ID:
                        protocol["id"] = gen_can_id_extended(protocol["id"])
                    protocol["name"] = "%s_%s" % (p_name, protocol["id"])
                    protocol["sender"] = items[4]
                    if protocol["id"] in black_list:
                        continue
                    protocol["protocol_type"] = "report"
                    if protocol["id"] in sender_list or protocol[
                            "sender"] == sender:
                        protocol["protocol_type"] = "control"
                    protocol["vars"] = []
                    in_protocol = True
                elif in_protocol:
                    if len(items) > 3 and items[0] == "SG_":
                        if items[2] == ":":
                            var_info = extract_var_info(items)
                            # current we can't process than 4 byte value
                            if var_info["len"] <= 32:
                                protocol["vars"].append(var_info)
                    else:
                        in_protocol = False
                        if len(protocol) != 0 and len(
                                protocol["vars"]) != 0 and len(
                                    protocol["vars"]) < 65:
                            protocols[protocol["id"]] = protocol
                            # print protocol
                            protocol = {}

                if len(items) == 5 and items[0] == "CM_" and items[1] == "SG_":
                    parse_signal_comment(items, protocols)

                if len(items) > 2 and items[0] == "VAL_":
                    parse_enum_values(items, protocols)

                if len(items) == 5 and items[0] == 'BA_' and items[
                        1] == 'GenMsgCycleTime' and items[2] == 'BO_':
                    parse_message_cycle_time(items, protocols)

        except (ValueError, UnicodeDecodeError) as e:
            print(f"Error occurred on line {line_num}: {e}")
            return False

        adjust_reserved_keywords(protocols)

        # save protocols
        config = {"car_type": car_type, "protocols": protocols}
        with open(out_file, 'w') as fp:
            yaml.dump(config, fp)

        # summary
        log_summary(car_type, out_file, protocols)
        return True


def gen_can_id_extended(str):
    """
        id string:
    """
    int_id = int(str, 16)
    int_id &= 0x1FFFFFFF
    str = hex(int_id).replace('0x', '')
    return str


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage:\npython %s your_car_parse_config_file.yml" % sys.argv[0])
        sys.exit(0)
    with open(sys.argv[1], 'r') as fp:
        conf = yaml.safe_load(fp)
    dbc_file = conf["dbc_file"]
    protocol_conf_file = conf["protocol_conf"]
    car_type = conf["car_type"]
    black_list = conf["black_list"]
    sender_list = conf["sender_list"]
    sender = conf["sender"]
    extract_dbc_meta(dbc_file, protocol_conf_file, car_type, black_list,
                     sender_list, sender)
