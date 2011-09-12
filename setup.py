#!/usr/bin/env python

from distutils.core import setup

VERSION = '0.1'

setup(name ='ejudgeparse',
      version = VERSION,
      description = 'Accessing and Modifying CFG files',
      author = 'German Ilyin',
      author_email = 'germanilyin@gmail.com',
      url = 'http://github.com/yunmanger1/ejudgeparse/',
      license = 'MIT',
      long_description = '''Python lib for parsing ejudge .cfg files''',
      classifiers = [
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'License :: OSI Approved :: Python Software Foundation License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.5',
        'Programming Language :: Python :: 2.6',
        'Topic :: Software Development :: Libraries :: Python Modules',
      ],
      packages = ['iniparse'],
      data_files = [
        ('share/doc/iniparse-%s' % VERSION, ['README', ]),
      ],
)

