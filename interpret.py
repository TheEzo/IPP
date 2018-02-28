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
        jumps = ['JUMP', 'JUMPIFEQ', 'JUMPIFNEQ']
        i = 0
        while i < self.inst_count:
            code = self.dict['instructions'][i]
            if code['opcode'] == 'LABEL':
                self.labels.update({code['args'][0]['text']: int(code['order'])})
            elif code['opcode'] in jumps:
                i = self.jump_instruction(i)
            else:
                self.complete_instruction(i)
                # print(code['opcode'])
            i += 1

    def get(self, frame, varname):
        if frame == 'GF':
            return self.gf_vars[varname]
        elif frame == 'LF':
            return self.lf_vars[varname]
        elif frame == 'TF':
            return self.tf_vars[varname]

    def update(self, frame, varname, value=''):
        if frame == 'GF':
            self.gf_vars.update({varname: value})
        elif frame == 'LF':
            self.lf_vars.update({varname: value})
        elif frame == 'TF':
            self.tf_vars.update({varname: value})
        else:
            pass

    def convert_string(self, s):
        while True:
            i = s.find('\\')
            if i == -1:
                return s
            else:
                n = int(s[i + 1:i + 4])
                if s[i+5:]:
                    s = s[:i] + chr(n) + s[i + 4:]
                else:
                    s = s[:i] + chr(n)

    def math(self, arg1, arg2):
        i1 = 0
        i2 = 0
        if arg1['type'] == 'var':
            pass
        else:
            if not arg1['type'] == 'int':
                sys.exit(53)
            i1 = int(arg1['text'])
        if arg2['type'] == 'var':
            pass
        else:
            if not arg2['type'] == 'int':
                sys.exit(53)
            i2 = int(arg2['text'])
        value = 0
        return value

    def complete_instruction(self, i):
        types = ['int', 'bool', 'string']
        code = self.dict['instructions'][i]
        try:
            frame = ''
            varname = ''
            arg1 = {}
            arg2 = {}
            arg3 = {}
            count = len(code['args'])
            if count >= 1:
                arg1 = code['args'][0]
            if count >= 2:
                arg2 = code['args'][1]
            if count == 3:
                arg3 = code['args'][2]
            if code['args'][0]['type'] == 'var':
                    frame = code['args'][0]['text'][:2]
                    varname = code['args'][0]['text'][3:]
            opcode = code['opcode']
            if opcode == 'DEFVAR':
                self.update(frame, varname, '')

            elif opcode == 'MOVE':
                value = ''

                if code['args'][1]['type'] == 'var':
                    pass
                # TODO
                elif arg2['type'] in types:
                    value = arg2['text']
                    if arg2['type'] == 'string':
                        i = value.find('\\')
                        if not i == -1:
                            value = self.convert_string(value)
                self.update(frame, varname, value)

            elif opcode == 'CONCAT':
                symb1 = arg2['text']
                symb2 = arg3['text']
                if arg2['type'] == 'var':
                    symb1 = self.get(symb1[:2], symb1[3:])
                elif not arg2['type'] == 'string':
                    sys.exit(58)
                if arg3['type'] == 'var':
                    symb2 = self.get(symb2[:2], symb2[3:])
                elif not arg3['type'] == 'string':
                    sys.exit(58)
                self.update(frame, varname, str(symb1) + str(symb2))
            elif opcode == 'WRITE':
                if not arg1['type'] == 'var':
                    sys.stdout.write(str(self.convert_string(arg1['text'])))
                else:
                    v = arg1['text']
                    sys.stdout.write(str(self.get(v[:2], v[3:])))
            elif opcode == 'CREATEFRAME':
                pass
            elif opcode == 'PUSHFRAME':
                pass
            elif opcode == 'POPFRAME':
                pass
            elif opcode == 'CALL':
                pass
            elif opcode == 'RETURN':
                pass
            elif opcode == 'PUSHS':
                pass
            elif opcode == 'POPS':
                pass
            elif opcode == 'ADD':
                self.update(frame, varname, self.math(arg2, arg3))
            elif opcode == 'SUB':
                pass
            elif opcode == 'MUL':
                pass
            elif opcode == 'IDIV':
                pass
            elif opcode == 'LT':
                pass
            elif opcode == 'GT':
                pass
            elif opcode == 'EQ':
                pass
            elif opcode == 'AND':
                pass
            elif opcode == 'OR':
                pass
            elif opcode == 'NOT':
                pass
            elif opcode == 'INT2CHAR':
                pass
            elif opcode == 'STR2INT':
                pass
            elif opcode == 'READ':
                pass
            elif opcode == 'STRLEN':
                if arg2['type'] == 'var':
                    pass
                else:
                    self.update(frame, varname, len(arg2['text']))
            elif opcode == 'GETCHAR':
                pass
            elif opcode == 'SETCHAR':
                pass
            elif opcode == 'TYPE':
                pass
            elif opcode == 'DPRINT':
                pass
            elif opcode == 'BREAK':
                pass

        except KeyError:
            pass
        except Exception as e:
            print(e)
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


