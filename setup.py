"""
Flask-Meld
--------------
A way to meld your frontend and backend code
"""
import re
from setuptools import setup

with open('flask_meld/__init__.py', 'r') as f:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
                        f.read(), re.MULTILINE).group(1)

setup(
    name='Flask-Meld',
    version=version,
    url='http://github.com/mikeabrahamsen/Flask-Meld/',
    license='MIT',
    author='Michael Abrahamsen',
    author_email='mail@michaelabrahamsen.com',
    description='Meld your Flask applications',
    long_description=__doc__,
    packages=['flask_meld'],
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=[
        'Flask>=0.9',
        'beautifulsoup4',
        'orjson',
        'flask-socketio',
        'gevent-websocket>=0.10.1'
    ],
    tests_require=[
        'pytest'
    ],
    test_suite='tests',
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
