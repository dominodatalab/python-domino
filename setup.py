from distutils.core import setup

setup(
    name='python-domino',
    version='0.2.2',
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
