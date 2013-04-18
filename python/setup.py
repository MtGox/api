import os

from mtgox import __version__

try:
	from setuptools import setup
except ImportError:
	from distutils.core import setup

# read description from README.md file
f = open(os.path.join(os.path.dirname(__file__), 'README.md'))
long_description = f.read()
f.close()

setup(
	name='mtgox',
	version=__version__,
	description='Python3 client for accessing the MtGox API',
	long_description=long_description,
	url='https://github.com/MtGox/api/python',
	author='Christophe Robin',
	author_email='crobin@nekoo.com',
	maintainer='Christophe Robin',
	maintainer_email='crobin@nekoo.com',
	keywords=['mtgox', 'api'],
	license='MIT',
	packages=['mtgox'],
	classifiers=[
		'Development Status :: 4 - Beta',
		'Environment :: Console',
		'Intended Audience :: Developers',
		'License :: OSI Approved :: MIT License',
		'Operating System :: OS Independent',
		'Programming Language :: Python :: 3',
		'Programming Language :: Python :: 3.0',
		'Programming Language :: Python :: 3.1',
		'Programming Language :: Python :: 3.2',
		'Programming Language :: Python :: 3.3',
		'Topic :: Internet'

	]
)