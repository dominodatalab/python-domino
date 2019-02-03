from distutils.core import setup

## begin borrowed from https://github.com/pypa/pip/blob/master/setup.py#L11-L28
import codecs
import os
import re

here = os.path.abspath(os.path.dirname(__file__))

def read(*parts):
    with codecs.open(os.path.join(here, *parts), 'r') as fp:
        return fp.read()

def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")
## end

setup(
    name='python-domino',
    version=find_version("domino", "__init__.py"),
    author='Domino Data Lab',
    author_email='support@dominodatalab.com',
    packages=['domino'],
    scripts=[],
    url='http://www.dominodatalab.com',
    license='LICENSE.txt',
    description='Python bindings for the Domino API',
    long_description='',
    install_requires=[
        'requests>=2.4.2'
    ]
)
