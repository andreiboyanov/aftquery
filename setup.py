from setuptools import setup, find_packages

NAME = "aftquery"
DESCRIPTION = (
    "A command line tools for discovering info about"
    "tennis tournaments and players in Belgium"
)
URL = "https://github.com/andreiboyanov/aftquery"
EMAIL = "andrei.boyanov@gmail.com"

AUTHOR = "Andrei Boyanov"

setup(
    name=NAME,
    version="0.1.0",
    description=DESCRIPTION,
    author=AUTHOR,
    author_email=EMAIL,
    url=URL,
    install_requires=["pymongo", "Flask-PyMongo", "beautifulsoup4", "requests"],
    py_modules=['aftquery'],
    entry_points={
        'console_scripts': ['aftquery=aftquery.aftsearch:main']
    },
    python_requires=">=3.0",
    include_package_data=True,
    license="GPL",
    classifiers=[
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
    ],
)
