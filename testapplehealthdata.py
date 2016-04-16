"""
testapplehealthdata.py: tests for the applehealthdata.py

Copyright (c) 2016 Nicholas J. Radcliffe
Licence: MIT
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import re
import shutil
import sys
import unittest

from applehealthdata import HealthDataExtractor

CLEAN_UP = True
VERBOSE = False


def get_base_dir():
    """
    Return the directory containing this test file,
    which will (normally) be the applyhealthdata directory
    also containing the testdata dir.
    """
    return os.path.split(os.path.abspath(__file__))[0]


def get_testdata_dir():
    """Return the full path to the testdata directory"""
    return os.path.join(get_base_dir(), 'testdata')


def get_tmp_dir():
    """Return the full path to the tmp directory"""
    return os.path.join(get_base_dir(), 'tmp')


def remove_any_tmp_dir():
    """
    Remove the temporary directory if it exists.
    Returns its location either way.
    """
    tmp_dir = get_tmp_dir()
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)
    return tmp_dir


def make_tmp_dir():
    """
    Remove any existing tmp directory.
    Create empty tmp direcory.
    Return the location of the tmp dir.
    """
    tmp_dir = remove_any_tmp_dir()
    os.mkdir(tmp_dir)
    return tmp_dir


def copy_test_data():
    """
    Copy the test data export6s3sample.xml from testdata directory
    to tmp directory.
    """
    tmp_dir = make_tmp_dir()
    name = 'export6s3sample.xml'
    in_xml_file = os.path.join(get_testdata_dir(), name)
    out_xml_file = os.path.join(get_tmp_dir(), name)
    shutil.copyfile(in_xml_file, out_xml_file)
    return out_xml_file


class TestAppleHealthDataExtractor(unittest.TestCase):
    @classmethod
    def tearDownClass(cls):
        """Clean up by removing the tmp directory, if it exists."""
        if CLEAN_UP:
            remove_any_tmp_dir()

    def check_file(self, filename):
        expected_output = os.path.join(get_testdata_dir(), filename)
        actual_output = os.path.join(get_tmp_dir(), filename)
        with open(expected_output) as f:
            expected = f.read()
        with open(actual_output) as f:
            actual = f.read()
        self.assertEqual(expected, actual)

    def test_tiny_fixed_extraction(self):
        path = copy_test_data()
        data = HealthDataExtractor(path, verbose=VERBOSE)
        data.extract()
        self.check_file('StepCount.csv')
        self.check_file('DistanceWalkingRunning.csv')


if __name__ == '__main__':
    unittest.main()

