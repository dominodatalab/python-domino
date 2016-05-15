from distutils.core import setup

setup(
    name='python-domino',
    version='0.1.4',
    author='Domino Data labs',
    author_email='chris@dominodatalab.com',
    packages=['domino'],
    scripts=[],
    url='http://www.dominodatalab.com',
    license='LICENSE.txt',
    description='Python bindings for Domino API',
    long_description='',
    install_requires=[
        'requests>=2.4.2'
    ]
)