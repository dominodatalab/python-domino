import pathlib
from setuptools import setup, find_packages
import re

PACKAGE_NAME = "domino"

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()


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
    name="dominodatalab",
    version=get_version(),
    author="Domino Data Lab",
    author_email="support@dominodatalab.com",
    packages=find_packages(),
    scripts=[],
    url="https://github.com/dominodatalab/python-domino",
    download_url='https://github.com/dominodatalab/python-domino/archive/' + get_version() + '.zip',
    license="Apache Software License (Apache 2.0)",
    description="Python bindings for the Domino API",
    long_description=README,
    long_description_content_type="text/markdown",
    keywords=["Domino Data Lab", "API"],
    install_requires=["requests>=2.4.2", "bs4==0.*,>=0.0.1", "polling2"],
    tests_require=[
        "pytest==6.2.2",
        "requests_mock>=1.9.*",
        'polling2'
    ],
    extras_require={
        "airflow": ["apache-airflow==1.*,>=1.10"],
        "data": ["dominodatalab-data>=0.1.0"],
    },
)
