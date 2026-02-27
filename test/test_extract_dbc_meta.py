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

from adbctool.extract_dbc_meta import extract_dbc_meta

_TEST_DIR = os.path.dirname(os.path.abspath(__file__))


def _write_dbc(content):
    """Write DBC content to a temporary file and return the path."""
    f = tempfile.NamedTemporaryFile(mode='w', suffix='.dbc', delete=False)
    f.write(content)
    f.close()
    return f.name


class TestExtractDbcMeta(unittest.TestCase):

    def setUp(self):
        fd, self.out_file = tempfile.mkstemp(suffix='.yaml')
        os.close(fd)
        os.unlink(self.out_file)

    def tearDown(self):
        if os.path.exists(self.out_file):
            os.unlink(self.out_file)

    def test_parse_acura_ilx_2016_nidec(self):
        """Parsing the provided acura_ilx_2016_nidec.dbc should succeed."""
        dbc_file = os.path.join(_TEST_DIR, 'acura_ilx_2016_nidec.dbc')
        result = extract_dbc_meta(dbc_file, self.out_file, 'acura', [], [],
                                  'ADAS')
        self.assertTrue(result)
        self.assertTrue(os.path.exists(self.out_file))
        with open(self.out_file, 'r') as fp:
            parsed = yaml.safe_load(fp)
        self.assertGreater(len(parsed.get("protocols", {})), 0)

    def test_parse_multiline_comment(self):
        """A DBC with a multi-line CM_ comment should parse successfully."""
        dbc = _write_dbc('''VERSION ""

NS_ :

BS_:

BU_: ADAS RADAR

BO_ 768 VEHICLE_STATE: 8 ADAS
 SG_ VEHICLE_SPEED : 15|8@0+ (1,0) [0|255] "kph" Vector__XXX

BO_ 1024 RADAR_DIAGNOSTIC: 8 RADAR
 SG_ RADAR_STATE : 7|8@0+ (1,0) [0|255] "" NEO

CM_ SG_ 1024 RADAR_STATE "This is
a multi-line comment";
''')
        try:
            result = extract_dbc_meta(dbc, self.out_file, 'test', [], [],
                                      'ADAS')
            self.assertTrue(result)
            self.assertTrue(os.path.exists(self.out_file))
        finally:
            os.unlink(dbc)

    def test_parse_comment_for_unknown_message(self):
        """A CM_ entry referencing a message not in protocols should not crash."""
        dbc = _write_dbc('''VERSION ""

NS_ :

BS_:

BU_: ADAS RADAR

BO_ 768 VEHICLE_STATE: 8 ADAS
 SG_ VEHICLE_SPEED : 15|8@0+ (1,0) [0|255] "kph" Vector__XXX

BO_ 1040 XXX_EMPTY: 8 RADAR

CM_ SG_ 1040 SOME_SIG "comment for empty message";
''')
        try:
            result = extract_dbc_meta(dbc, self.out_file, 'test', [], [],
                                      'ADAS')
            self.assertTrue(result)
        finally:
            os.unlink(dbc)

    def test_parse_val_for_unknown_message(self):
        """A VAL_ entry referencing a message not in protocols should not crash."""
        dbc = _write_dbc('''VERSION ""

NS_ :

BS_:

BU_: ADAS RADAR

BO_ 768 VEHICLE_STATE: 8 ADAS
 SG_ VEHICLE_SPEED : 15|8@0+ (1,0) [0|255] "kph" Vector__XXX

BO_ 1040 XXX_EMPTY: 8 RADAR

VAL_ 1040 SOME_SIG 1 "on" 0 "off";
''')
        try:
            result = extract_dbc_meta(dbc, self.out_file, 'test', [], [],
                                      'ADAS')
            self.assertTrue(result)
        finally:
            os.unlink(dbc)

    def test_hash_comment_lines_fail_in_strict_mode(self):
        """Non-DBC '#' comment lines should fail in strict mode."""
        dbc = _write_dbc('''VERSION ""

NS_ :

BS_:

BU_: ADAS RADAR

# this is not a standard DBC comment line and should be ignored
BO_ 768 VEHICLE_STATE: 8 ADAS
 SG_ VEHICLE_SPEED : 15|8@0+ (1,0) [0|255] "kph" Vector__XXX

CM_ SG_ 768 VEHICLE_SPEED "vehicle speed";
''')
        try:
            result = extract_dbc_meta(dbc, self.out_file, 'test', [], [],
                                      'ADAS')
            self.assertFalse(result)
        finally:
            os.unlink(dbc)

    def test_inline_hash_tail_does_not_break_signal_parsing(self):
        """A trailing '#' token on a signal line should not crash parser."""
        dbc = _write_dbc('''VERSION ""

NS_ :

BS_:

BU_: ADAS

BO_ 768 VEHICLE_STATE: 8 ADAS
 SG_ VEHICLE_SPEED : 15|8@0+ (1,0) [0|255] "kph" Vector__XXX # trailing tokens

CM_ SG_ 768 VEHICLE_SPEED "vehicle speed";
''')
        try:
            result = extract_dbc_meta(dbc, self.out_file, 'test', [], [],
                                      'ADAS')
            self.assertTrue(result)
            with open(self.out_file, 'r') as fp:
                parsed = yaml.safe_load(fp)
            protocol = parsed["protocols"]["300"]
            self.assertEqual(len(protocol["vars"]), 1)
            self.assertEqual(protocol["vars"][0]["name"], "VEHICLE_SPEED")
        finally:
            os.unlink(dbc)

    def test_slash_comment_lines_fail_in_strict_mode(self):
        """Non-DBC '//' comment lines should fail in strict mode."""
        dbc = _write_dbc('''VERSION ""

NS_ :

BS_:

BU_: ADAS RADAR

// this line should be ignored
BO_ 768 VEHICLE_STATE: 8 ADAS
 SG_ VEHICLE_SPEED : 15|8@0+ (1,0) [0|255] "kph" Vector__XXX

CM_ SG_ 768 VEHICLE_SPEED "vehicle speed";
''')
        try:
            result = extract_dbc_meta(dbc, self.out_file, 'test', [], [],
                                      'ADAS')
            self.assertFalse(result)
        finally:
            os.unlink(dbc)

    def test_hash_comment_ignored_in_lenient_mode(self):
        """Non-DBC comment line can be ignored in lenient mode for compatibility."""
        dbc = _write_dbc('''VERSION ""

NS_ :

BS_:

BU_: ADAS RADAR

# this line should be ignored in lenient mode
BO_ 768 VEHICLE_STATE: 8 ADAS
 SG_ VEHICLE_SPEED : 15|8@0+ (1,0) [0|255] "kph" Vector__XXX

CM_ SG_ 768 VEHICLE_SPEED "vehicle speed";
''')
        try:
            result = extract_dbc_meta(dbc, self.out_file, 'test', [], [],
                                      'ADAS', strict_dbc=False)
            self.assertTrue(result)
            with open(self.out_file, 'r') as fp:
                parsed = yaml.safe_load(fp)
            protocol = parsed["protocols"]["300"]
            self.assertEqual(len(protocol["vars"]), 1)
        finally:
            os.unlink(dbc)

    def test_comments_inside_signal_block_fail_in_strict_mode(self):
        """'#' and '//' between SG_ lines should fail in strict mode."""
        dbc = _write_dbc('''VERSION ""

NS_ :

BS_:

BU_: ADAS RADAR

BO_ 768 VEHICLE_STATE: 8 ADAS
 SG_ VEHICLE_SPEED : 15|8@0+ (1,0) [0|255] "kph" Vector__XXX
 # hash comment inside signal block
 // slash comment inside signal block
 SG_ VEHICLE_ACC : 23|8@0+ (1,0) [0|255] "m/s2" Vector__XXX

CM_ SG_ 768 VEHICLE_SPEED "vehicle speed";
''')
        try:
            result = extract_dbc_meta(dbc, self.out_file, 'test', [], [],
                                      'ADAS')
            self.assertFalse(result)
        finally:
            os.unlink(dbc)

    def test_malformed_quote_fails_in_strict_mode(self):
        """Malformed quoted string should fail in strict mode."""
        dbc = _write_dbc('''VERSION ""

NS_ :

BS_:

BU_: ADAS

BO_ 768 VEHICLE_STATE: 8 ADAS
 SG_ VEHICLE_SPEED : 15|8@0+ (1,0) [0|255] "kph" Vector__XXX

CM_ SG_ 768 VEHICLE_SPEED "unterminated comment;
''')
        try:
            result = extract_dbc_meta(dbc, self.out_file, 'test', [], [],
                                      'ADAS')
            self.assertFalse(result)
        finally:
            os.unlink(dbc)


if __name__ == '__main__':
    unittest.main()
