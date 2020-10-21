from setuptools import setup
import re

PACKAGE_NAME = 'domino'


def get_version():
    try:
        f = open(f"{PACKAGE_NAME}/_version.py")
    except EnvironmentError:
        return None
    for line in f.readlines():
        mo = re.match("__version__ = '([^']+)'", line)
        if mo:
            ver = mo.group(1)
            return ver
    return None


setup(
    name='python-domino',
    version=get_version(),
    author='Domino Data Lab',
    author_email='support@dominodatalab.com',
    packages=[PACKAGE_NAME],
    scripts=[],
    url='http://www.dominodatalab.com',
    license='LICENSE.txt',
    description='Python bindings for the Domino API',
    long_description='',
    install_requires=[
        'requests>=2.4.2',
        'bs4==0.*,>=0.0.1',
        'polling2'
    ],
    extras_require={
        "airflow":  ['apache-airflow==1.*,>=1.10'],
    }
)
