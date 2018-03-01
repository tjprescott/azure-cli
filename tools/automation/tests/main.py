# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import sys

from automation.utilities.display import display, output
from automation.utilities.path import get_repo_root, get_test_results_dir
from automation.tests.nose_helper import get_nose_runner



def run_tests(modules, parallel, run_live, tests):

    import timeit

    if not modules and not tests:
        display('No tests set to run.')
        sys.exit(1)

    display("""
=============
  Run Tests
=============
""")
    if modules:
        display('Modules: {}'.format(', '.join(name for name, _, _ in modules)))

    # set environment variable
    if run_live:
        os.environ['AZURE_TEST_RUN_LIVE'] = 'True'

    test_paths = tests or [p for _, _, p in modules]

    display('Drive test by nosetests')
    from six import StringIO
    old_stderr = sys.stderr
    test_stderr = StringIO()
    sys.stderr = test_stderr
    results = []
    start_time = timeit.default_timer()
    for path in test_paths:
        results.append(get_nose_runner(parallel=parallel, process_timeout=3600 if run_live else 600)([path]))
    stderr_val = test_stderr.getvalue()
    sys.stderr = old_stderr
    test_stderr.close()
    elapsed_time = timeit.default_timer() - start_time
    print('ELAPSED: {}'.format(elapsed_time))
    failed_tests = summarize_tests(stderr_val)
    return results, failed_tests


def collect_test():
    from importlib import import_module

    paths = import_module('azure.cli').__path__
    result = []
    collect_tests(paths, result, 'azure.cli')
    return result


def collect_tests(path, return_collection, prefix=''):
    from unittest import TestLoader
    from importlib import import_module
    from pkgutil import iter_modules

    loader = TestLoader()
    for _, name, is_pkg in iter_modules(path):
        full_name = '{}.{}'.format(prefix, name)
        module_path = os.path.join(path[0], name)

        if is_pkg:
            collect_tests([module_path], return_collection, full_name)

        if not is_pkg and name.startswith('test'):
            test_module = import_module(full_name)
            for suite in loader.loadTestsFromModule(test_module):
                for test in suite._tests:  # pylint: disable=protected-access
                    return_collection.append(
                        '{}.{}.{}'.format(full_name, test.__class__.__name__, test._testMethodName))  # pylint: disable=protected-access

def summarize_tests(test_output):
    display(test_output)
    failed_tests = []
    for line in test_output.splitlines():
        if '... ERROR' in line or '... FAIL' in line:
            line = line.replace('(', '')
            line = line.replace(')', '')
            try:
                test_name, _, _, _ = line.split(' ')
                line = test_name
            except:
                pass
            failed_tests.append(line)

    if failed_tests:
        display("""
==========
  FAILED
==========
""")
        for failed_test in failed_tests:
            display(failed_test)
    return failed_tests

