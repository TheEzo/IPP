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

        self.labels = {}
        self.gf_vars = {}
        self.lf_vars = {}
        self.tf_vars = {}

        print(self.dict)
        self._run_code()


    def _parse_file(self):
        """
        convert check and convert file to dict
        """
        try:
            tree = et.parse(self.file)
        except:
            # asi??
            sys.exit(0)
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
                        regex = compile(r"^(\\0([0-2]\d|3[0-2]|35|92)|(?!(\\|#))[\x0000-\xFFFF])*$")
                    elif arg_type == 'int':
                        regex = compile(r"^((\-|\+)?[1-9]\d*|0)$")
                    elif arg_type == 'bool':
                        regex = (r"^(true|false)$")
                    elif arg_type == 'label':
                        regex = compile(r"^(\-|_|\$|\*|%|&|\w)[\w\d\-_\$\*%&]*$")
                    elif arg_type == 'type':
                        regex = compile(r"^(string|int|bool)$")
                    else:
                        sys.exit(31)

                    if match(regex, arg.text) is None:
                        sys.exit(32)
                    args.append({'type': arg_type, 'text': arg.text})
                instructions.append({'tag': child.tag, 'order': child.attrib['order'],
                                     'opcode': child.attrib['opcode'], 'args': args})
                if int(child.attrib['order']) > self.inst_count:
                    self.inst_count = int(child.attrib['order'])
        except KeyError:
            sys.exit(31)
        return {'root': {'tag': root.tag, 'attr': root.attrib}, 'instructions': instructions}

    def _define_labels(self):
        for i in self.dict['instructions']:
            if i['opcode'] == 'LABEL':
                self.labels.update({i['args'][0]['text']: int(i['order'])})

    def _run_code(self):
        self._define_labels()
        print(self.labels)
        jumps = ['JUMP', 'JUMPIFEQ', 'JUMPIFNEQ']
        i = 0
        while i < self.inst_count:
            # for i in range(self.inst_count):
            print(i)
            code = self.dict['instructions'][i]
            if code['opcode'] == 'LABEL':
                self.labels.update({code['args'][0]['text']: int(code['order'])})
            elif code['opcode'] in jumps:
                i = self.jump_instruction(i)
            else:
                self.complete_instruction(i)
                print(code['opcode'])
            i += 1

    def update(self, frame, varname, value):
        if frame == 'GF':
            self.gf_vars.update({varname: ''})
        elif frame == 'LF':
            self.lf_vars.update({varname: ''})
        elif frame == 'TF':
            self.tf_vars.update({varname: ''})
        else:
            pass

    def complete_instruction(self, i):

        types = ['int', 'bool', 'string']
        code = self.dict['instructions'][i]
        try:
            opcode = code['opcode']
            if opcode == 'DEFVAR':
                frame = code['args'][0]['text'][:2]
                varname = code['args'][0]['text'][3:]
                self.update(frame, varname, '')

            elif opcode == 'MOVE':
                frame = code['args'][0]['text'][:2]
                varname = code['args'][0]['text'][3:]

                value = ''

                if code['args'][1]['type'] == 'var':
                    pass
                elif code['args'][1]['type'] in types:
                    value = code['args'][1]['text']

                self.update(frame, varname, value)

            elif opcode == 'CONCAT':
                frame = code['args'][0]['text'][:2]
                varname = code['args'][0]['text'][3:]



        except KeyError:
            pass
        pass

    def jump_instruction(self, i):
        code = self.dict['instructions'][i]
        try:
            if code['opcode'] == 'JUMP':
                return self.labels[code['args'][0]['text']] - 1
            elif code['opcode'] == 'JUMPIFEQ':
                arg1 = code['args'][1]
                arg2 = code['args'][2]

                t1 = ''
                t2 = ''

                if arg1['type'] == 'var':
                    if arg1['text'][:2] == 'LF':
                        t1 = self.lf_vars[arg1['text'][3:]]
                    elif arg1['text'][:2] == 'GF':
                        t1 = self.gf_vars[arg1['text'][3:]]
                    elif arg1['text'][:2] == 'TF':
                        t1 = self.tf_vars[arg1['text'][3:]]
                    else:
                        pass
                        #sys.exit()
                else:
                    t1 = arg1['text']
                if arg2['type'] == 'var':
                    if arg2['text'][:2] == 'LF':
                        t2 = self.lf_vars[arg2['text'][3:]]
                    elif arg2['text'][:2] == 'GF':
                        t2 = self.gf_vars[arg2['text'][3:]]
                    elif arg2['text'][:2] == 'TF':
                        t2 = self.tf_vars[arg2['text'][3:]]
                    else:
                        pass
                        #sys.exit()
                else:
                    t2 = arg2['text']

                if t1 == t2:
                    return self.labels[code['args'][0]['text']] - 1
                else:
                    return i

            # JUMPIFNEQ
            else:
                pass
        except KeyError:
            # undefined label
            sys.exit(52)
        return 3


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--source', help='Path to input XML file', metavar='PATH', required=True)
    args = parser.parse_known_args()

    path = os.path.abspath(args[0].source)
    with open(path, 'r') as f:
        SomeClass(f)


