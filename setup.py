from setuptools import setup

setup(
    name='Portal',
    version='0.1.0',
    author='D. Adeboye',
    author_email='david.adeboye@outlook.com',
    packages=['command-portal'],
    scripts=['bin/portal'],
    url='https://github.com/adeboyed/Portal',
    license='LICENSE',
    description='Portal is a command line tool for running commands with no dependencies.',
    long_description=open('README.md').read(),
    install_requires=[
        'toml',
        'docker'
    ],
)