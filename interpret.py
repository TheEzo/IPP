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
        self.lf_vars = []
        self.tf_vars = None
        self.stack = []
        self.data_stack = []

        self._run_code()

    def _parse_file(self):
        """
        convert check and convert file to dict
        """
        try:
            tree = et.parse(self.file)
        except:
            # TODO asi??
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
                        regex = compile(r"^(\\0([0-2]\d|3[0-2]|35|92)|(?!(\\|#))[\u0000-\uFFFF])*$")
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
                pass
                # self.labels.update({code['args'][0]['text']: int(code['order'])})
            elif code['opcode'] in jumps:
                i = self.jump_instruction(i)
            elif code['opcode'] == 'CALL':
                self.stack.append(i+1)
                i = self.labels[code['args'][0]['text']] - 1
            elif code['opcode'] == 'RETURN':
                try:
                    i = self.stack.pop() - 1
                except IndexError:
                    pass
            else:
                self.complete_instruction(i)
            i += 1

    def get(self, frame, varname):
        try:
            if frame == 'GF':
                return self.gf_vars[varname]
            elif frame == 'LF':
                return self.lf_vars[-1][varname]
            elif frame == 'TF':
                return self.tf_vars[varname]
        except KeyError:
            pass #TODO

    def update(self, frame, varname, value, define=False):
        if define:
            vartype = 'uninitialized'
        else:
            if type(value) == str:
                vartype = 'string'
            elif type(value) == int:
                vartype = 'int'
            else:
                vartype = 'bool'

        if frame == 'GF':
            self.gf_vars.update({varname: {'val': value, 'type': vartype}})
        elif frame == 'LF': #TODO
            self.lf_vars[-1].update({varname: {'val': value, 'type': vartype}})
        elif frame == 'TF':
            self.tf_vars.update({varname: {'val': value, 'type': vartype}})
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

    def math(self, arg1, arg2, op):
        if arg1['type'] == 'var':
            frame = arg1['text'][:2]
            varname = arg1['text'][3:]
            var = self.get(frame, varname)
            if var['type'] == 'uninitialized':
                sys.exit(56)
            if not var['type'] == 'int':
                sys.exit(53)
            i1 = var['val']
        else:
            if not arg1['type'] == 'int':
                sys.exit(53)
            i1 = int(arg1['text'])

        if arg2['type'] == 'var':
            frame = arg2['text'][:2]
            varname = arg2['text'][3:]
            var = self.get(frame, varname)
            if var['type'] == 'uninitialized':
                sys.exit(56)
            if not var['type'] == 'int':
                sys.exit(53)
            i2 = var['val']
        else:
            if not arg2['type'] == 'int':
                sys.exit(53)
            i2 = int(arg2['text'])
        if i1 == "UNINITIALIZED" or i2 == 'UNINITIALIZED':
            sys.exit(56)
        if op == 'ADD':
            return i1 + i2
        elif op == 'SUB':
            return i1 - i2
        elif op == 'MUL':
            return i1 * i2
        elif op == 'IDIV':
            if i2 == 0:
                sys.exit(57)
            return int(i1 / i2)

    def complete_instruction(self, i):
        types = ['int', 'bool', 'string']
        code = self.dict['instructions'][i]

        frame = ''
        varname = ''
        arg1 = {}
        arg2 = {}
        arg3 = {}
        try:
            count = len(code['args'])
            if count > 0:
                if code['args'][0]['type'] == 'var':
                    frame = code['args'][0]['text'][:2]
                    varname = code['args'][0]['text'][3:]
                if count == 3:
                    arg3 = code['args'][2]
                if count >= 1:
                    arg1 = code['args'][0]
                if count >= 2:
                    arg2 = code['args'][1]
            #TODO zkontrolovat pocet args
        except KeyError:
            pass

        opcode = code['opcode']
        if opcode == 'DEFVAR':
            self.update(frame, varname, 'UNINITIALIZED', True)
        elif opcode == 'MOVE':
            if arg2['type'] == 'var':
                value = self.get(arg2['text'][:2], arg2['text'][3:])
            elif arg2['type'] in types:
                if arg2['type'] == 'int':
                    value = int(arg2['text'])
                elif arg2['type'] == 'string':
                    value = str(arg2['text'])
                else:
                    value = True if arg2['text'] == 'true' else False
                # if arg2['type'] == 'string':
                #     i = value.find('\\')
                #     if not i == -1:
                #         value = self.convert_string(value)
            else:
                # TODO kod?
                sys.exit()
            var = self.get(frame, varname)
            if var is None:
                sys.exit(54)
            self.update(frame, varname, value)

        elif opcode == 'CONCAT':
            symb1 = arg2['text']
            symb2 = arg3['text']
            if arg2['type'] == 'var':
                symb1 = self.get(symb1[:2], symb1[3:])
                if not symb1['type'] == 'string':
                    sys.exit(53)
                symb1 = symb1['val']
            elif not arg2['type'] == 'string':
                sys.exit(53)
            if arg3['type'] == 'var':
                symb2 = self.get(symb2[:2], symb2[3:])
                if not symb2['type'] == 'string':
                    sys.exit(53)
                symb2 = symb2['val']
            elif not arg3['type'] == 'string':
                sys.exit(53)
            self.update(frame, varname, str(symb1) + str(symb2))
        elif opcode == 'WRITE':
            if not arg1['type'] == 'var':
                print(str(self.convert_string(arg1['text'])))
            else:
                v = arg1['text']
                val = self.get(v[:2], v[3:])['val']
                if val == 'UNINITIALIZED':
                    sys.exit(56)
                if type(val) is bool:
                    print(str(val).lower())
                else:
                    print(str(val))
        elif opcode == 'CREATEFRAME':
            self.tf_vars = {}
        elif opcode == 'PUSHFRAME':
            self.lf_vars.append(self.tf_vars)
        elif opcode == 'POPFRAME':
            if not self.lf_vars:
                sys.exit(55)
            self.tf_vars = self.lf_vars[-1]
        elif opcode == 'PUSHS':
            if arg1['type'] == 'var':
                val = self.get(frame, varname)['val']
                self.data_stack.append(val)
            else:
                if arg1['type'] == 'int':
                    self.data_stack.append(int(arg1['text']))
                elif arg1['type'] == 'string':
                    self.data_stack.append(str(arg1['text']))
                else:
                    self.data_stack.append(str(arg1['text']))
        elif opcode == 'POPS':
            if not self.data_stack:
                sys.exit(56)
            self.update(frame, varname, self.data_stack.pop())
        elif opcode == 'ADD':
            self.update(frame, varname, self.math(arg2, arg3, 'ADD'))
        elif opcode == 'SUB':
            self.update(frame, varname, self.math(arg2, arg3, 'SUB'))
        elif opcode == 'MUL':
            self.update(frame, varname, self.math(arg2, arg3, 'MUL'))
        elif opcode == 'IDIV':
            self.update(frame, varname, self.math(arg2, arg3, 'IDIV'))
        elif opcode == 'LT' or opcode == 'GT' or opcode == 'EQ':
            if arg2['type'] == 'var':
                val1 = self.get_var(arg2)
            else:
                if arg2['type'] == 'string':
                    val1 = str(arg2['text'])
                elif arg2['type'] == 'int':
                    val1 = int(arg2['text'])
                else:
                    val1 = True if arg2['text'] == 'true' else False

            if arg3['type'] == 'var':
                val2 = self.get_var(arg3)
            else:
                if arg3['type'] == 'string':
                    val2 = str(arg3['text'])
                elif arg2['type'] == 'int':
                    val2 = int(arg3['text'])
                else:
                    val2 = True if arg3['text'] == 'true' else False

            if type(val1) is not type(val2):
                sys.exit(53)

            if opcode == 'LT':
                val = val1['val'] < val2['val']
            elif opcode == 'GT':
                val = val1['val'] > val2['val']
            else:
                val = val1['val'] == val2['val']
            self.update(frame, varname, val)
        elif opcode == 'AND' or opcode == 'or':
            if arg2['type'] == 'var':
                val1 = self.get_var(arg2)
            else:
                if not arg2['type'] == 'bool':
                    sys.exit(53)
                val1 = True if arg2['text'] == 'true' else False

            if arg3['type'] == 'var':
                val2 = self.get_var(arg3)
            else:
                if not arg3['type'] == 'bool':
                    sys.exit(53)
                val2 = True if arg3['text'] == 'true' else False

            if type(val1) is not bool or type(val2) is not bool:
                sys.exit(53)

            if opcode == 'AND':
                self.update(frame, varname, val1 & val2)
            else:
                self.update(frame, varname, val1 | val2)
        elif opcode == 'NOT':
            if arg2['type'] == 'var':
                val1 = self.get_var(arg2)
            else:
                if not arg2['type'] == 'bool':
                    sys.exit(53)
                val1 = True if arg2['text'] == 'true' else False
            self.update(frame, varname, not val1)
        elif opcode == 'INT2CHAR':
            if arg2['type'] == 'var':
                val = self.get_var(arg2)['val']
                if not val['type'] == 'int':
                    sys.exit(53)
            else:
                if not arg2['type'] == 'int':
                    sys.exit(53)
                val = int(arg2['text'])
            if val < 0:
                sys.exit(58)
            self.update(frame, varname, chr(val))
        elif opcode == 'STRI2INT':
            if arg2['type'] == 'var':
                val1 = self.get_var(arg2)
                if not val1['type'] == 'string':
                    sys.exit(53)
                val1 = val1['val']
            else:
                if not arg2['type'] == 'string':
                    sys.exit(53)
                val1 = str(arg2['text'])

            if arg3['type'] == 'var':
                val2 = self.get_var(arg3)['val']
                if not val2['type'] == 'int':
                    sys.exit(53)
            else:
                if not arg3['type'] == 'int':
                    sys.exit(53)
                val2 = int(arg3['text'])
            try:
                val1[val2]
            except IndexError:
                sys.exit(58)
            if val2 < 0:
                sys.exit(58)
            self.update(frame, varname, ord(val1[val2]))
        elif opcode == 'READ':
            text = input()
            if arg2['text'] == 'string':
                self.update(frame, varname, str(text))
            elif arg2['text'] == 'int':
                self.update(frame, varname, int(text))
            else:
                if text == 'true' or text == 'false':
                    self.update(frame, varname, True if text == 'true' else False)
                else:
                    sys.exit() #todo kod
        elif opcode == 'STRLEN':
            if arg2['type'] == 'var':
                f = arg2['text'][:2]
                n = arg2['text'][3:]
                self.update(frame, varname, len(self.get(f, n)['val']))
            else:
                self.update(frame, varname, len(arg2['text']))
        elif opcode == 'GETCHAR':
            if arg2['type'] == 'var':
                val1 = self.get_var(arg2)
                if not val1['type'] == 'string':
                    sys.exit(53)
            else:
                if not arg2['type'] == 'string':
                    sys.exit(53)
                val1 = str(arg2['text'])

            if arg3['type'] == 'var':
                val2 = self.get_var(arg3)
                if not val2['type'] == 'string':
                    sys.exit(53)
            else:
                if not arg3['type'] == 'int':
                    sys.exit(53)
                val2 = int(arg3['text'])
            # TODO index exception 58
            self.update(frame, varname, str(val1['val'][val2]))
        elif opcode == 'SETCHAR':
            if arg2['type'] == 'var':
                val1 = self.get_var(arg2)
                if not val1['type'] == 'int':
                    sys.exit(53)
            else:
                if not arg2['type'] == 'int':
                    sys.exit(53)
                val1 = int(arg2['text'])

            if arg3['type'] == 'var':
                val2 = self.get_var(arg3)
                if not val2['type'] == 'string':
                    sys.exit(53)
            else:
                if not arg3['type'] == 'string':
                    sys.exit(53)
                val2 = str(arg3['text'])
            if len(val2) == 0:
                sys.exit(58)

            var = self.get(frame, varname)['val']
            var = var[:1] + val2['val'] + var[2:]
            self.update(frame, varname, var)
        elif opcode == 'TYPE':
            if arg2['type'] == 'var':
                val = arg2['text']
                val = self.get(val[:2], val[3:])
                if val['type'] == 'string':
                    typ = 'string'
                elif val['type'] == 'int':
                    typ = 'int'
                elif val['type'] == 'bool':
                    typ = 'bool'
                else:
                    typ = ''
                self.update(frame, varname, typ)
            else:
                self.update(frame, varname, arg2['type'])
        elif opcode == 'DPRINT':
            pass
        elif opcode == 'BREAK':
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
                        t1 = self.lf_vars[arg1['text'][3:]]['val']
                    elif arg1['text'][:2] == 'GF':
                        t1 = self.gf_vars[arg1['text'][3:]]['val']
                    elif arg1['text'][:2] == 'TF':
                        t1 = self.tf_vars[arg1['text'][3:]]['val']
                    else:
                        pass
                        #sys.exit() TODO
                else:
                    t1 = arg1['text']
                if arg2['type'] == 'var':
                    if arg2['text'][:2] == 'LF':
                        t2 = self.lf_vars[arg2['text'][3:]]['val']
                    elif arg2['text'][:2] == 'GF':
                        t2 = self.gf_vars[arg2['text'][3:]]['val']
                    elif arg2['text'][:2] == 'TF':
                        t2 = self.tf_vars[arg2['text'][3:]]['val']
                    else:
                        pass
                        #sys.exit() TODO
                else:
                    t2 = arg2['text']

                if t1 == t2:
                    return self.labels[code['args'][0]['text']] - 1
                else:
                    return i

            # JUMPIFNEQ
            else:
                arg1 = code['args'][1]
                arg2 = code['args'][2]

                t1 = ''
                t2 = ''

                if arg1['type'] == 'var':
                    if arg1['text'][:2] == 'LF':
                        t1 = self.lf_vars[-1][arg1['text'][3:]]['val']
                    elif arg1['text'][:2] == 'GF':
                        t1 = self.gf_vars[arg1['text'][3:]]['val']
                    elif arg1['text'][:2] == 'TF':
                        t1 = self.tf_vars[arg1['text'][3:]]['val']
                else:
                    t1 = arg1['text']
                if arg2['type'] == 'var':
                    if arg2['text'][:2] == 'LF':
                        t2 = self.lf_vars[arg2['text'][3:]]['val']
                    elif arg2['text'][:2] == 'GF':
                        t2 = self.gf_vars[arg2['text'][3:]]['val']
                    elif arg2['text'][:2] == 'TF':
                        t2 = self.tf_vars[arg2['text'][3:]]['val']
                else:
                    t2 = arg2['text']

                if not t1 == t2:
                    return self.labels[code['args'][0]['text']] - 1
                else:
                    return i
        except KeyError:
            # undefined label
            sys.exit(52)
        return 3

    def get_var(self, arg):
        frame = arg['text'][:2]
        varname = arg['text'][3:]
        return self.get(frame, varname)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--source', help='Path to input XML file', metavar='PATH', required=True)
    args = parser.parse_known_args()

    path = os.path.abspath(args[0].source)
    with open(path, 'r') as f:
        SomeClass(f)
