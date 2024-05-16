import pathlib
import re
import sys

from setuptools import find_packages, setup

if sys.version_info < (3,7):
    message = f"dominodatalab requires Python '>=3.7.0' but the running Python is {'.'.join(map(str,sys.version_info[:3]))}"
    message += "\nConsider Checking python-domino and domino compatibility"
    sys.exit(message)

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
        mo = re.match('__version__ = "([^\']+)"', line)
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
    download_url=f"https://github.com/dominodatalab/python-domino/archive/release-{get_version()}.zip",
    license="Apache Software License (Apache 2.0)",
    description="Python bindings for the Domino API",
    long_description=README,
    long_description_content_type="text/markdown",
    keywords=["Domino Data Lab", "API"],
    python_requires='>=3.9.0',
    install_requires=["packaging", "requests>=2.4.2", "beautifulsoup4~=4.11", "polling2~=0.5.0",
                      "urllib3~=1.26.12", "typing-extensions>=4.5.0", "frozendict~=2.3.4", "python-dateutil~=2.8.2",
                      "retry==0.9.2"],
    extras_require={
        "airflow": ["apache-airflow==2.2.4"],
        "data": ["dominodatalab-data>=0.1.0"],
        "dev": [
            "black==22.3.0",
            "flake8==4.0.1",
            "Jinja2==2.11.3",
            "nbconvert==6.3.0",
            "packaging==21.3",
            "polling2==0.5.0",
            "pre-commit==2.19.0",
            "pyspark==3.3.0",
            "pytest==6.2.2",
            "requests_mock==1.9.3",
            "tox==3.25.1",
            "frozendict==2.3.4",
        ],
    },
)
