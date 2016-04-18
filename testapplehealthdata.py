# -*- coding: utf-8 -*-
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

from collections import Counter


from applehealthdata import (HealthDataExtractor,
                             format_freqs, format_value,
                             abbreviate, encode)

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
        self.assertEqual((filename, expected), (filename, actual))

    def test_tiny_reference_extraction(self):
        path = copy_test_data()
        data = HealthDataExtractor(path, verbose=VERBOSE)
        data.extract()
        for kind in ('StepCount', 'DistanceWalkingRunning',
                     'Workout', 'ActivitySummary'):
            self.check_file('%s.csv' % kind)

    def test_format_freqs(self):
        counts = Counter()
        self.assertEqual(format_freqs(counts), '')
        counts['one'] += 1
        self.assertEqual(format_freqs(counts), 'one: 1')
        counts['one'] += 1
        self.assertEqual(format_freqs(counts), 'one: 2')
        counts['two'] += 1
        counts['three'] += 1
        self.assertEqual(format_freqs(counts),
                         '''one: 2
three: 1
two: 1''')

    def test_format_null_values(self):
        for dt in ('s', 'n', 'd', 'z'):
            # Note: even an illegal type, z, produces correct output for
            # null values.
            # Questionable, but we'll leave as a feature
            self.assertEqual(format_value(None, dt), '')

    def test_format_numeric_values(self):
        cases = {
            '0': '0',
            '3': '3',
            '-1': '-1',
            '2.5': '2.5',
        }
        for (k, v) in cases.items():
            self.assertEqual((k, format_value(k, 'n')), (k, v))

    def test_format_date_values(self):
        hearts = 'any string not need escaping or quoting; even this: ♥♥'
        cases = {
            '01/02/2000 12:34:56': '01/02/2000 12:34:56',
            hearts: hearts,
        }
        for (k, v) in cases.items():
            self.assertEqual((k, format_value(k, 'd')), (k, v))

    def test_format_string_values(self):
        cases = {
            'a': '"a"',
            '': '""',
            'one "2" three': r'"one \"2\" three"',
            r'1\2\3': r'"1\\2\\3"',
        }
        for (k, v) in cases.items():
            self.assertEqual((k, format_value(k, 's')), (k, v))

    def test_abbreviate(self):
        changed = {
            'HKQuantityTypeIdentifierHeight': 'Height',
            'HKQuantityTypeIdentifierStepCount': 'StepCount',
            'HK*TypeIdentifierStepCount': 'StepCount',
            'HKCharacteristicTypeIdentifierDateOfBirth': 'DateOfBirth',
            'HKCharacteristicTypeIdentifierBiologicalSex': 'BiologicalSex',
            'HKCharacteristicTypeIdentifierBloodType': 'BloodType',
            'HKCharacteristicTypeIdentifierFitzpatrickSkinType':
                                                    'FitzpatrickSkinType',
        }
        unchanged = [
            '',
            'a',
            'aHKQuantityTypeIdentifierHeight',
            'HKQuantityTypeIdentityHeight',
        ]
        for (k, v) in changed.items():
            self.assertEqual((k, abbreviate(k)), (k, v))
            self.assertEqual((k, abbreviate(k, False)), (k, k))
        for k in unchanged:
            self.assertEqual((k, abbreviate(k)), (k, k))

    def test_encode(self):
        # This test looks strange, but because of the import statments
        #     from __future__ import unicode_literals
        # in Python 2, type('a') is unicode, and the point of the encode
        # function is to ensure that it has been converted to a UTF-8 string
        # before writing to file.
        self.assertEqual(type(encode('a')), str)

    def test_extracted_reference_stats(self):
        path = copy_test_data()
        data = HealthDataExtractor(path, verbose=VERBOSE)

        self.assertEqual(data.n_nodes, 20)
        expectedRecordCounts = [
           ('DistanceWalkingRunning', 5),
           ('StepCount', 10),
        ]
        self.assertEqual(sorted(data.record_types.items()),
                         expectedRecordCounts)

        self.assertEqual(data.n_nodes, 20)
        expectedOtherCounts = [
           ('ActivitySummary', 2),
           ('Workout', 1),
        ]
        self.assertEqual(sorted(data.other_types.items()),
                         expectedOtherCounts)

        expectedTagCounts = [
           ('ActivitySummary', 2),
           ('ExportDate', 1),
           ('Me', 1),
           ('Record', 15),
           ('Workout', 1),
        ]
        self.assertEqual(sorted(data.tags.items()),
                         expectedTagCounts)

        expectedFieldCounts = [
            ('HKCharacteristicTypeIdentifierBiologicalSex', 1),
            ('HKCharacteristicTypeIdentifierBloodType', 1),
            ('HKCharacteristicTypeIdentifierDateOfBirth', 1),
            ('HKCharacteristicTypeIdentifierFitzpatrickSkinType', 1),
            ('activeEnergyBurned', 2),
            ('activeEnergyBurnedGoal', 2),
            ('activeEnergyBurnedUnit', 2),
            ('appleExerciseTime', 2),
            ('appleExerciseTimeGoal', 2),
            ('appleStandHours', 2),
            ('appleStandHoursGoal', 2),
            ('creationDate', 16),
            ('dateComponents', 2),
            ('duration', 1),
            ('durationUnit', 1),
            ('endDate', 16),
            ('sourceName', 16),
            ('sourceVersion', 1),
            ('startDate', 16),
            ('totalDistance', 1),
            ('totalDistanceUnit', 1),
            ('totalEnergyBurned', 1),
            ('totalEnergyBurnedUnit', 1),
            ('type', 15),
            ('unit', 15),
            ('value', 16),
            ('workoutActivityType', 1)
        ]
        self.assertEqual(sorted(data.fields.items()),
                         expectedFieldCounts)



if __name__ == '__main__':
    unittest.main()
