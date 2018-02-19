__author__ = "Tomáš Willaschek"
__login__ = "xwilla00"
__email__ = "xwilla00@stud.fit.vutbr.cz"
__project__ = "IPP 2018"


import sys
import os
from xml import etree
from argparse import ArgumentParser


class SomeClass:
    pass


def get_help():
    print('Some help...')


if __name__ == '__main__':

    parser = ArgumentParser()
    parser.add_argument('-s', '--source', help='Path to input XML file', metavar='PATH', required=True)
    args = parser.parse_known_args()
    print(args)
    # if args.help:
    #     get_help()
    #     sys.exit(0)
    SomeClass()

