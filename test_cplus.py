import os
import subprocess
import re
import json
import argparse
from typing import List, Dict, Any

class CppFunction:
    def __init__(self, name: str, return_type: str, parameters: List[str]):
        self.name = name
        self.return_type = return_type
        self.parameters = parameters

    def __str__(self):
        return f"{self.return_type} {self.name}({', '.join(self.parameters)})"

class CppParser:
    @staticmethod
    def parse_file(file_path: str) -> List[CppFunction]:
        with open(file_path, 'r') as file:
            content = file.read()

        function_pattern = r'(\w+)\s+(\w+)\s*\(([\w\s,]*)\)\s*{'
        matches = re.finditer(function_pattern, content)

        functions = []
        for match in matches:
            return_type, name, params = match.groups()
            parameters = [param.strip() for param in params.split(',') if param.strip()]
            functions.append(CppFunction(name, return_type, parameters))

        return functions

class TestGenerator:
    @staticmethod
    def generate_test_file(functions: List[CppFunction], output_file: str):
        with open(output_file, 'w') as file:
            file.write("#include <iostream>\n")
            file.write("#include <cassert>\n")
            file.write("#include \"../src/functions.h\"\n\n")

            for func in functions:
                file.write(f"void test_{func.name}() {{\n")
                file.write(f"    // TODO: Implement test for {func.name}\n")
                file.write(f"    // Example: assert({func.name}(...) == expected_result);\n")
                file.write("}\n\n")

            file.write("int main() {\n")
            for func in functions:
                file.write(f"    test_{func.name}();\n")
            file.write("    std::cout << \"All tests passed!\" << std::endl;\n")
            file.write("    return 0;\n")
            file.write("}\n")

class TestRunner:
    @staticmethod
    def compile_and_run(test_file: str) -> Dict[str, Any]:
        compile_command = f"g++ -std=c++11 -I../src {test_file} -o test_executable"
        run_command = "./test_executable"

        try:
            subprocess.run(compile_command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as e:
            return {"success": False, "stage": "compilation", "error": e.stderr.decode()}

        try:
            result = subprocess.run(run_command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return {"success": True, "output": result.stdout.decode()}
        except subprocess.CalledProcessError as e:
            return {"success": False, "stage": "execution", "error": e.stderr.decode()}

class TestAutomationTool:
    def __init__(self, src_dir: str, test_dir: str):
        self.src_dir = src_dir
        self.test_dir = test_dir

    def run(self):
        cpp_files = [f for f in os.listdir(self.src_dir) if f.endswith('.cpp')]

        for cpp_file in cpp_files:
            src_file_path = os.path.join(self.src_dir, cpp_file)
            functions = CppParser.parse_file(src_file_path)

            test_file_name = f"test_{cpp_file}"
            test_file_path = os.path.join(self.test_dir, test_file_name)

            TestGenerator.generate_test_file(functions, test_file_path)
            print(f"Generated test file: {test_file_path}")

            result = TestRunner.compile_and_run(test_file_path)
            if result["success"]:
                print(f"Test results for {cpp_file}:")
                print(result["output"])
            else:
                print(f"Error in {result['stage']} for {cpp_file}:")
                print(result["error"])

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="C++ Test Automation Tool")
    parser.add_argument("src_dir", help="Directory containing C++ source files")
    parser.add_argument("test_dir", help="Directory to store generated test files")
    args = parser.parse_args()

    tool = TestAutomationTool(args.src_dir, args.test_dir)
    tool.run()
