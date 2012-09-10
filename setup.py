from distutils.core import setup
import sys

setup(
    name='Baskit',
    version='0.2.1.5',
    description='Minecraft Server Manager',
    author='Steven McGrath',
    author_email='steve@chigeek.com',
    url='https://github.com/SteveMcGrath/baskit',
    packages=['baskit', 'baskit.mc'],
    entry_points = {
        'console_scripts': [
            'baskit = baskit.cli:cli',
            ]
    },
    #data_files=[
    #],
    #install_requires=[
    #],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: System :: Systems Administration',
    ]
)