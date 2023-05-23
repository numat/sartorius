"""Package manager setup for Sartorius driver."""
from setuptools import setup

with open('README.md') as in_file:
    long_description = in_file.read()

setup(
    name="sartorius",
    version="0.5.0",
    description="Python driver for Sartorius and Minebea Intec scales.",
    long_description=long_description,
    long_description_content_type='text/markdown',
    url="https://github.com/numat/sartorius/",
    author="Patrick Fuller",
    author_email="pat@numat-tech.com",
    packages=['sartorius'],
    package_data={'sartorius': ['py.typed']},
    install_requires=['pyserial'],
    extras_require={

        'test': [
            'mypy==1.3.0',
            'pytest>=6,<8',
            'pytest-cov>=4,<5',
            'pytest-asyncio==0.*',
            'ruff==0.0.269',
            'types-pyserial',
        ]
    },
    entry_points={
        'console_scripts': [('sartorius = sartorius:command_line')]
    },
    license='GPLv2',
    classifiers=[
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Development Status :: 4 - Beta',
        'Natural Language :: English',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Scientific/Engineering :: Human Machine Interfaces'
    ]
)
