#! /bin/bash

if ! -f [.venv]
    python3 -m venv .venv
    pip install -U pip whell
    pip install -r requiremnts.txt

./.venv/bin/python name_do_script $0 $1





~~~~~~~~~~~~~~~~~~~~~~~~


import sys

def main(input1, input2):
    pass

if __name__ == '__main__':
    main(sys.argv[0], sys.argv[1])