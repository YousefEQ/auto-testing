import xml.etree.ElementTree as ET
import json
import importlib
import unittest
import sys
import time
import concurrent.futures
import logging
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class TestCase:
    name: str
    module: str
    function: str
    inputs: List[Any]
    expected_output: Any
    setup: str = None
    teardown: str = None

class CustomTestLoader:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.test_cases: List[TestCase] = []

    def load_tests(self) -> None:
        if self.file_path.endswith('.xml'):
            self._load_xml_tests()
        elif self.file_path.endswith('.json'):
            self._load_json_tests()
        else:
            raise ValueError("Unsupported file format. Use XML or JSON.")

    def _load_xml_tests(self) -> None:
        tree = ET.parse(self.file_path)
        root = tree.getroot()
        for test_case in root.findall('test_case'):
            self.test_cases.append(TestCase(
                name=test_case.get('name'),
                module=test_case.find('module').text,
                function=test_case.find('function').text,
                inputs=eval(test_case.find('inputs').text),
                expected_output=eval(test_case.find('expected_output').text),
                setup=test_case.find('setup').text if test_case.find('setup') is not None else None,
                teardown=test_case.find('teardown').text if test_case.find('teardown') is not None else None
            ))

    def _load_json_tests(self) -> None:
        with open(self.file_path, 'r') as file:
            data = json.load(file)
            for test_case in data:
                self.test_cases.append(TestCase(**test_case))

class DynamicTest(unittest.TestCase):
    def __init__(self, test_case: TestCase):
        super().__init__('run_test')
        self.test_case = test_case

    def setUp(self) -> None:
        if self.test_case.setup:
            exec(self.test_case.setup)

    def tearDown(self) -> None:
        if self.test_case.teardown:
            exec(self.test_case.teardown)

    def run_test(self) -> None:
        module = importlib.import_module(self.test_case.module)
        function = getattr(module, self.test_case.function)
        result = function(*self.test_case.inputs)
        self.assertEqual(result, self.test_case.expected_output)

class TestResult:
    def __init__(self, test_case: TestCase, success: bool, error_message: str = None, execution_time: float = 0):
        self.test_case = test_case
        self.success = success
        self.error_message = error_message
        self.execution_time = execution_time

class TestRunner:
    def __init__(self, test_cases: List[TestCase], parallel: bool = False, max_workers: int = 4):
        self.test_cases = test_cases
        self.parallel = parallel
        self.max_workers = max_workers
        self.results: List[TestResult] = []

    def run_tests(self) -> None:
        if self.parallel:
            self._run_parallel()
        else:
            self._run_sequential()

    def _run_sequential(self) -> None:
        for test_case in self.test_cases:
            self._run_single_test(test_case)

    def _run_parallel(self) -> None:
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            executor.map(self._run_single_test, self.test_cases)

    def _run_single_test(self, test_case: TestCase) -> None:
        start_time = time.time()
        test = DynamicTest(test_case)
        result = unittest.TestResult()
        test.run(result)
        execution_time = time.time() - start_time

        if result.wasSuccessful():
            self.results.append(TestResult(test_case, True, execution_time=execution_time))
        else:
            error_message = str(result.errors[0][1]) if result.errors else str(result.failures[0][1])
            self.results.append(TestResult(test_case, False, error_message, execution_time))

    def generate_report(self) -> Dict[str, Any]:
        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results if result.success)
        failed_tests = total_tests - passed_tests
        total_time = sum(result.execution_time for result in self.results)

        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "total_time": total_time,
            "details": [
                {
                    "name": result.test_case.name,
                    "success": result.success,
                    "execution_time": result.execution_time,
                    "error_message": result.error_message
                } for result in self.results
            ]
        }

def run_tests(file_path: str, parallel: bool = False, max_workers: int = 4) -> None:
    loader = CustomTestLoader(file_path)
    loader.load_tests()

    runner = TestRunner(loader.test_cases, parallel, max_workers)
    runner.run_tests()

    report = runner.generate_report()
    print(json.dumps(report, indent=2))

    logging.info(f"Total tests: {report['total_tests']}")
    logging.info(f"Passed tests: {report['passed_tests']}")
    logging.info(f"Failed tests: {report['failed_tests']}")
    logging.info(f"Total execution time: {report['total_time']:.2f} seconds")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    if len(sys.argv) < 2:
        print("Usage: python test_tool.py <path_to_test_file> [--parallel] [--max-workers N]")
        sys.exit(1)

    test_file = sys.argv[1]
    parallel = "--parallel" in sys.argv
    max_workers = 4

    if "--max-workers" in sys.argv:
        index = sys.argv.index("--max-workers")
        if index + 1 < len(sys.argv):
            max_workers = int(sys.argv[index + 1])

    run_tests(test_file, parallel, max_workers)
