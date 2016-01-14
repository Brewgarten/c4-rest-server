import sys

from setuptools import setup, find_packages

import versioneer


needs_pytest = {"pytest", "test", "ptr", "coverage"}.intersection(sys.argv)
pytest_runner = ["pytest-runner"] if needs_pytest else []

setup(
    author = "IBM",
    author_email = "",
    cmdclass = versioneer.get_cmdclass(),
    description = "REST server and device manager for project C4",
    entry_points = {},
    install_requires = [
        "c4-systemmanager",
        "futures",
        "tornado"
    ],
    keywords = "python c4 rest",
    license = "IBM",
    name = "c4-rest-server",
    package_data = {},
    packages = find_packages(),
    setup_requires=[] + pytest_runner,
    tests_require=[
        "pytest",
        "pytest-cov"
    ],
    url = "",
    version = versioneer.get_version(),
)
