#!/usr/bin/env python3


"""
Histórico:
2022-01-16 - Criar a versão 0.2.3
2021-12-12 - Alterar o nome de commandlib para cmdlib.
2021-11-07 - Inserir a função is_admin().

"""

from setuptools import setup
import os
import sys

file_setup = os.path.abspath(os.path.realpath(__file__))
dir_of_project = os.path.dirname(file_setup)

sys.path.insert(0, dir_of_project)

from cmdlib.__main__ import (
	__version__, 
	__author__,
	__repo__,
	__download_file__,
)

DESCRIPTION = 'Trabalha com a linha de comando em sistemas Linux e Windows.'
LONG_DESCRIPTION = 'Trabalha com a linha de comando em sistemas Linux e Windows.'

setup(
	name='cmdlib',
	version=__version__,
	description=DESCRIPTION,
	long_description=LONG_DESCRIPTION,
	author=__author__,
	author_email='brunodasill@gmail.com',
	license='MIT',
	packages=['cmdlib'],
	zip_safe=False,
	url='https://gitlab.com/bschaves/cmd-lib',
	project_urls = {
		'Código fonte': __repo__,
		'Download': __download_file__,
	},
)


