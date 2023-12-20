from setuptools import find_packages, setup
from os import path


NAME = "ostilhou"
VERSION = "0.1.4"
DESCRIPTION = "Breton language speech to text tools"
URL = "https://github.com/gweltou/ostilhou/"
AUTHOR = "Gweltaz Duval-Guennoc"
EMAIL = "gweltou@hotmail.com"
REQUIRES_PYTHON = ">=3.6.0"


# The directory containing this file
HERE = path.dirname(__file__)

with open(path.join(HERE, "requirements.txt")) as fd:
    REQUIREMENTS = [line.strip() for line in fd.readlines() if line.strip()]


setup(
    name=NAME,
    url=URL,
    version=VERSION,
    author=AUTHOR,
    licence="MIT",
    author_email=EMAIL,
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    python_requires=REQUIRES_PYTHON,
    install_requires=REQUIREMENTS,
    classifiers=[
		"Intended Audience :: Developers",
		"License :: OSI Approved :: MIT License",
		"Programming Language :: Python",
		"Programming Language :: Python :: 3",
		"Programming Language :: Python :: 3.6",
		"Programming Language :: Python :: 3.7",
		"Programming Language :: Python :: 3.8",
		"Programming Language :: Python :: 3.9",
		"Operating System :: OS Independent"
	],
    packages=find_packages(),
    package_data={"ostilhou": ["asr/*", "dicts/*", "hspell/*", "hspell/hunspell-dictionary/*"]},
    setup_requires=["pytest-runner"],
    tests_require=["pytest"],
	test_suite="tests",
    entry_points={
        "console_scripts": [
            "srt2split = ostilhou:srt2split",
            "wavesplit = wavesplit:main",
        ],
    }
)
