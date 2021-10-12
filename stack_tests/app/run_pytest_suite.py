"""integration tests - run_test_suite - Function for running the unit test suite"""
import json
import os
import pytest
from typing import TypedDict, List
import xmltodict


class Failure(TypedDict):
    message: str
    text: str


class Testcase(TypedDict):
    classname: str
    name: str
    time: str
    failure: Failure


class Testsuite(TypedDict):
    name: str
    errors: str
    failures: str
    skipped: str
    tests: str
    time: str
    timestamp: str
    hostname: str
    testcase: List[Testcase]


class Testsuites(TypedDict):
    testsuite: Testsuite


class PyTestResults(TypedDict):
    testsuites: Testsuites


def import_testresults(path_for_xml_results: str) -> PyTestResults:
    """Imports pytest results from xml file. Returns dictionary

    Args:
        path_for_xml_results (str): path for xml results

    Returns:
        PyTestResults: Pytest results as dictionary
    """
    with open(path_for_xml_results) as fp:
        contents: str = fp.read()
    os.remove(path_for_xml_results)
    res: str = json.dumps(xmltodict.parse(contents))
    res = res.replace("@", "").replace("#", "")
    return json.loads(res)


def run_pytest_suite(path_for_xml_results: str, test_dir: str) -> bool:
    """Run pytest suite. Raises error if no tests are detected, that are errors, or there are failures

    Args:
        path_for_xml_results (str): path to pytest xml results
        test_dir (str): directory for pytests tests

    Raises:
        Exception: raises exception if no tests are found
        Exception: raises exception if tests return errors
        Exception: raises exception if tests return failures

    Returns:
        bool: True if tests are successful
    """

    pytest.main([
        f"{test_dir}",
        f"--junit-xml={path_for_xml_results}",
    ])

    pytest_results: PyTestResults = import_testresults(path_for_xml_results=path_for_xml_results)

    if pytest_results["testsuites"]["testsuite"]["tests"] == "0":
        raise Exception("Pytests did not detect any tests")

    if pytest_results["testsuites"]["testsuite"]["errors"] != "0":
        raise Exception("Pytests returned errors")

    if pytest_results["testsuites"]["testsuite"]["failures"] != "0":
        raise Exception("Pytest returned failures")

    return True
