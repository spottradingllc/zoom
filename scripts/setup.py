from distutils.core import setup
import py2exe
import os

os.chdir('../server')
setup(console=['sentinel.py'])