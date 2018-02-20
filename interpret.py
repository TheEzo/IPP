__author__ = "Tomas Willaschek"
__login__ = "xwilla00"
__email__ = "xwilla00@stud.fit.vutbr.cz"
__project__ = "IPP 2018"


import sys
import os
from xml.etree import ElementTree as et
import argparse


class SomeClass:

    def __init__(self, file):
        self.file = file
        self.dict = self._parse_file()
        print(self.dict)

    def _parse_file(self):
        tree = et.parse(self.file)
        root = tree.getroot()
        instructions = []
        for child in root:
            args = []
            for arg in child:
                args.append({'tag': arg.tag, 'type': arg.attrib['type'], 'text': arg.text})
            instructions.append({'tag': child.tag, 'order': child.attrib['order'],
                                 'opcode': child.attrib['opcode'], 'args': args})
        return {'root': {'tag': root.tag, 'attr': root.attrib, 'instructions': instructions}}


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--source', help='Path to input XML file', metavar='PATH', required=True)
    args = parser.parse_known_args()

    path = os.path.abspath(args[0].source)
    with open(path, 'r') as f:
        SomeClass(f)


