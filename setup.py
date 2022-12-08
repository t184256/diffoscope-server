# SPDX-FileCopyrightText: 2022 Alexander Sosedkin <monk@unboiled.info>
# SPDX-License-Identifier: AGPL-3.0-or-later

from setuptools import setup

setup(
    name='diffoscope-server',
    version='0.0.1',
    url='https://github.com/t184256/diffoscope-server',
    author='Alexander Sosedkin',
    author_email='monk@unboiled.info',
    description="diffoscope-server",
    packages=[
        'diffoscope_server',
    ],
    install_requires=[
        'flask',
    ],
    entry_points={
        'console_scripts': [
            'diffoscope-server = diffoscope_server.main:main',
        ],
    },
)
