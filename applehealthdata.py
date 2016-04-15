"""
applehealthdata.py: Extract data from Apple Health App's export.xml.

Copyright (c) 2016 Nicholas J. Radcliffe
Licence: MIT
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import re
import sys

from xml.etree import ElementTree
from collections import Counter, OrderedDict

__version__ = '1.0'

FIELDS = OrderedDict((
    ('sourceName', 's'),
    ('sourceVersion', 's'),
    ('device', 's'),
    ('type', 's'),
    ('unit', 's'),
    ('creationDate', 'd'),
    ('startDate', 'd'),
    ('endDate', 'd'),
    ('value', 'n'),
))

PREFIX_RE = re.compile('^HK.*TypeIdentifier(.+)$')
ABBREVIATE = True
VERBOSE = True

def format_freqs(counter):
    """
    Format a counter object for display.
    """
    return '\n'.join('%s: %d' % (tag, counter[tag])
                     for tag in sorted(counter.keys()))


def format_value(value, datatype):
    """
    Format a value for a CSV file, escaping double quotes and backslashes.

    None maps to empty.

    datatype should be
        's' for string (escaped)
        'n' for number
        'd' for datetime
    """
    if value is None:
        return ''
    elif datatype == 's':  # string
        return '"%s"' % value.replace('\\', '\\\\').replace('"', '\\"')
    elif datatype in ('n', 'd'):  # number or date
        return value
    else:
        raise KeyError('Unexpected format value: %s' % datatype)


def abbreviate(s):
    """
    Abbreviate particularly verbose strings based on a regular expression
    """
    m = re.match(PREFIX_RE, s)
    return m.group(1) if ABBREVIATE and m else s


def encode(s):
    """
    Encode string for writing to file.
    In Python 2, this encodes as UTF-8, whereas in Python 3,
    it does nothing
    """
    return s.encode('UTF-8') if sys.version_info.major < 3 else s



class HealthDataExtractor(object):
    """
    Extract health data from Apple Health App's XML export, export.xml.

    Inputs:
        path:      Relative or absolute path to export.xml
        verbose:   Set to False for less verbose output

    Outputs:
        Writes a CSV file for each record type found, in the same
        directory as the input export.xml. Reports each file written
        unless verbose has been set to False.
    """
    def __init__(self, path, verbose=VERBOSE):
        self.in_path = path
        self.verbose = verbose
        self.directory = os.path.abspath(os.path.split(path)[0])
        with open(path) as f:
            self.report('Reading data from %s . . . ' % path, end='')
            self.data = ElementTree.parse(f)
            self.report('done')
        self.root = self.data._root
        self.nodes = self.root.getchildren()
        self.n_nodes = len(self.nodes)
        self.abbreviate_types()
        self.collect_stats()

    def report(self, msg, end='\n'):
        if self.verbose:
            print(msg, end=end)
            sys.stdout.flush()

    def count_tags_and_fields(self):
        self.tags = Counter()
        self.fields = Counter()
        for record in self.nodes:
            self.tags[record.tag] += 1
            for k in record.keys():
                self.fields[k] += 1

    def count_record_types(self):
        self.record_types = Counter()
        for record in self.nodes:
            if record.tag == 'Record':
                self.record_types[record.attrib['type']] += 1

    def collect_stats(self):
        self.count_record_types()
        self.count_tags_and_fields()

    def open_for_writing(self):
        self.handles = {}
        self.paths = []
        for kind in self.record_types:
            path = os.path.join(self.directory, '%s.csv' % abbreviate(kind))
            f = open(path, 'w')
            f.write(','.join(FIELDS) + '\n')
            self.handles[kind] = f
            self.report('Opening %s for writing' % path)

    def abbreviate_types(self):
        """
        Shorten types by removing common boilerplate text.
        """
        for node in self.nodes:
            if node.tag == 'Record':
                if 'type' in node.attrib:
                    node.attrib['type'] = abbreviate(node.attrib['type'])


    def write_records(self):
        for node in self.nodes:
            if node.tag == 'Record':
                attributes = node.attrib
                kind = attributes['type']
                values = [format_value(attributes.get(field), datatype)
                          for (field, datatype) in FIELDS.items()]
                line = encode(','.join(values) + '\n')
                self.handles[kind].write(line)

    def close_files(self):
        for (kind, f) in self.handles.items():
            f.close()
            self.report('Written %s data.' % abbreviate(kind))

    def extract(self):
        self.open_for_writing()
        self.write_records()
        self.close_files()

    def report_stats(self):
        print('\nTags:\n%s\n' % format_freqs(self.tags))
        print('Fields:\n%s\n' % format_freqs(self.fields))
        print('Record types:\n%s\n' % format_freqs(self.record_types))


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('USAGE: python applehealthdata.py /path/to/export.xml',
              file=sys.stderr)
        sys.exit(1)
    data = HealthDataExtractor(sys.argv[1])
    data.report_stats()
    data.extract()
