#!/usr/bin/env python
from setuptools import setup

setup(
    name='singleflight',
    version='0.1.3',
    description='Coalesce multiple identical call into one, preventing thundering-herd/stampede to database/other backends',
    long_description=open('README.md', 'r').read(),
    long_description_content_type="text/markdown",
    keywords=['cache', 'stampede', 'thundering-herd'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Software Development :: Libraries',
    ],
    platforms=[
        'Any',
    ],
    python_requires='>=3.5',
    license='MIT',
    author='Aaron Dwi Caesar',
    author_email='aarondwico@gmail.com',
    maintainer_email='aarondwico@gmail.com',
    url='http://github.com/aarondwi/singleflight',
    packages=["singleflight",],
    install_requires=[],
    include_package_data=True,
    zip_safe=False,
    test_suite='tests',
    tests_require=['coverage'],
)