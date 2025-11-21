"""
Minimal setup.py for custom setuptools_scm configuration.

All package metadata is defined in pyproject.toml (PEP 621).
This file exists only to provide custom version scheme logic for PR builds.
"""

import os

from setuptools import setup


def local_scheme(version):
    """
    Custom local version scheme for PR builds.

    - For PRs: Adds .dev{GITHUB_RUN_ID} suffix for unique TestPyPI versions
    - For releases: No local version suffix (clean version numbers)

    This enables TestPyPI publishing on PRs without version conflicts.
    """
    if os.environ.get("IS_PULL_REQUEST"):
        return f".dev{os.environ.get('GITHUB_RUN_ID', 'local')}"
    return ""


# All metadata in pyproject.toml - this just configures version scheme
setup(use_scm_version={"local_scheme": local_scheme})
