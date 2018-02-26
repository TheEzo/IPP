__author__ = "Tomas Willaschek"
__login__ = "xwilla00"
__email__ = "xwilla00@stud.fit.vutbr.cz"
__project__ = "IPP 2018"


import sys
import os

from re import match, compile
from xml.etree import ElementTree as et
import argparse


class SomeClass:

    def __init__(self, file):
        self.file = file
        self.inst_count = 0
        self.dict = self._parse_file()
        print(self.dict)
        self._run_code()

    def _parse_file(self):
        """
        convert check and convert file to dict
        """
        tree = et.parse(self.file)
        root = tree.getroot()
        instructions = []
        try:
            for child in root:
                args = []
                for arg in child:
                    arg_type = arg.attrib['type']
                    if arg_type == 'var':
                        regex = compile(r"^(GF|LF|TF)@(-|_|\$|\*|%|&|\w)[\w\d\-_\$\*%&]*$")
                    elif arg_type == 'string':
                        if arg.text is None:
                            arg.text = ''
                        regex = compile(r".*")
                    elif arg_type == 'int':
                        regex = compile(r".*")
                    elif arg_type == 'bool':
                        regex = (r"^(true|false)$")
                    elif arg_type == 'label':
                        regex = compile(r".*")
                    elif arg_type == 'type':
                        regex = compile(r"^(string|int|bool)$")
                    else:
                        sys.exit(31)

                    if match(regex, arg.text) is None:
                        sys.exit(32)
                    args.append({'tag': arg.tag, 'type': arg_type, 'text': arg.text})
                instructions.append({'tag': child.tag, 'order': child.attrib['order'],
                                     'opcode': child.attrib['opcode'], 'args': args})
                if int(child.attrib['order']) > self.inst_count:
                    self.inst_count = int(child.attrib['order'])
        except KeyError:
            sys.exit(31)
        return {'root': {'tag': root.tag, 'attr': root.attrib, 'instructions': instructions}}

    def _run_code(self):
        for i in range(self.inst_count):

        pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--source', help='Path to input XML file', metavar='PATH', required=True)
    args = parser.parse_known_args()

    path = os.path.abspath(args[0].source)
    with open(path, 'r') as f:
        SomeClass(f)


