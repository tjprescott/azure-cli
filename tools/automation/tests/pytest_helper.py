# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function
from ..utilities.path import get_repo_root


def get_pytest_runner(parallel=True):
    """Create a pytest execution method"""

    def _run_pytest(test_paths):

        import multiprocessing
        from subprocess import call

        arguments = '-n {} -d '.format(multiprocessing.cpu_count()) if parallel else ''
        arguments += ' '.join(test_paths)
        result = call(('python -m pytest ' + arguments).split())
        return result

    return _run_pytest
