"""Package manager setup for Sartorius driver."""
from setuptools import setup

with open('README.md', 'r') as in_file:
    long_description = in_file.read()

setup(
    name="sartorius",
    version="0.2.1",
    description="Python driver for Sartorius and Minebea Intec scales.",
    long_description=long_description,
    long_description_content_type='text/markdown',
    url="http://github.com/numat/sartorius/",
    author="Patrick Fuller",
    author_email="pat@numat-tech.com",
    packages=['sartorius'],
    entry_points={
        'console_scripts': [('sartorius = sartorius:command_line')]
    },
    license='GPLv2',
    classifiers=[
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Development Status :: 4 - Beta',
        'Natural Language :: English',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: Scientific/Engineering :: Human Machine Interfaces'
    ]
)
