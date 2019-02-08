#!/usr/bin/env python3

import os
import sys
sys.path.append(f'{os.path.dirname(os.path.realpath(__file__))}/utils')
from utils import run, cli, check_files

scripts_root = os.path.dirname(os.path.realpath(__file__))

os.chdir(scripts_root)

run('git submodule update --init --recursive')

os.chdir(f'{scripts_root}/lib/data-translators')

if not os.path.isdir('build'): os.mkdir('build')

os.chdir('build')

run('FC=gfortran cmake ..', raise_error=True)
run('make')
