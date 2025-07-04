#!/usr/bin/env python3
"""
Comprehensive API testing script for the Document Extractor application.
Tests all endpoints and verifies backend functionality.
"""

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict

import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"


class APITester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []

    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test result."""
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} - {test_name}: {details}")
        self.test_results.append(
            {"test": test_name, "success": success, "details": details}
        )

    def test_health_endpoint(self) -> bool:
        """Test basic health endpoint."""
        try:
            response = self.session.get(f"{self.base_url}/health")
            success = response.status_code == 200
            self.log_test("Health Endpoint", success, f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("Health Endpoint", False, f"Error: {str(e)}")
            return False

    def test_detailed_health_endpoint(self) -> bool:
        """Test detailed health endpoint."""
        try:
            response = self.session.get(f"{self.base_url}/health/detailed")
            success = response.status_code == 200
            data = response.json() if success else {}
            self.log_test(
                "Detailed Health Endpoint",
                success,
                f"Status: {response.status_code}, Data: {json.dumps(data, indent=2)}",
            )
            return success
        except Exception as e:
            self.log_test("Detailed Health Endpoint", False, f"Error: {str(e)}")
            return False

    def test_root_endpoint(self) -> bool:
        """Test root endpoint returns HTML."""
        try:
            response = self.session.get(f"{self.base_url}/")
            success = (
                response.status_code == 200
                and "text/html" in response.headers.get("content-type", "")
            )
            self.log_test(
                "Root Endpoint",
                success,
                f"Status: {response.status_code}, Content-Type: {response.headers.get('content-type')}",
            )
            return success
        except Exception as e:
            self.log_test("Root Endpoint", False, f"Error: {str(e)}")
            return False

    def test_api_tasks_endpoint(self) -> Dict[str, Any]:
        """Test /api/tasks endpoint."""
        try:
            response = self.session.get(f"{self.base_url}/api/tasks")
            success = response.status_code == 200
            data = response.json() if success else []
            self.log_test(
                "API Tasks Endpoint",
                success,
                f"Status: {response.status_code}, Tasks count: {len(data)}",
            )
            return {"success": success, "data": data}
        except Exception as e:
            self.log_test("API Tasks Endpoint", False, f"Error: {str(e)}")
            return {"success": False, "data": []}

    def create_test_file(self) -> Path:
        """Create a simple test file for upload."""
        test_content = """
        # Test Document

        This is a test document for API testing.

        ## Section 1
        Some content here.

        ## Section 2
        More content here.
        """

        test_file = Path("/tmp/test_document.txt")
        test_file.write_text(test_content)
        return test_file

    def test_file_upload(self) -> Dict[str, Any]:
        """Test file upload endpoint."""
        try:
            test_file = self.create_test_file()

            with open(test_file, "rb") as f:
                files = {"file": ("test_document.txt", f, "text/plain")}
                response = self.session.post(
                    f"{self.base_url}/uploadfile/", files=files
                )

            success = response.status_code == 200
            data = response.json() if success else {}

            details = f"Status: {response.status_code}"
            if success:
                details += f", Task ID: {data.get('task_id', 'N/A')}"
            else:
                details += f", Error: {data.get('detail', 'Unknown error')}"

            self.log_test("File Upload", success, details)

            # Cleanup
            test_file.unlink(missing_ok=True)

            return {"success": success, "data": data}
        except Exception as e:
            self.log_test("File Upload", False, f"Error: {str(e)}")
            return {"success": False, "data": {}}

    def test_task_result(self, task_id: str) -> Dict[str, Any]:
        """Test task result endpoint."""
        try:
            response = self.session.get(f"{self.base_url}/api/tasks/{task_id}/result")
            success = response.status_code in [200, 404]  # 404 is OK if task not ready
            data = response.json() if response.status_code == 200 else {}

            details = f"Status: {response.status_code}"
            if response.status_code == 200:
                details += f", Has markdown: {'markdown' in data}"
            elif response.status_code == 404:
                details += ", Task not ready yet"
            else:
                details += f", Error: {data.get('detail', 'Unknown error')}"

            self.log_test("Task Result", success, details)
            return {"success": success, "data": data}
        except Exception as e:
            self.log_test("Task Result", False, f"Error: {str(e)}")
            return {"success": False, "data": {}}

    def test_task_monitoring(self, task_id: str, max_wait: int = 30) -> bool:
        """Monitor task completion."""
        logger.info(f"Monitoring task {task_id} for up to {max_wait} seconds...")

        start_time = time.time()
        while time.time() - start_time < max_wait:
            # Check task status via /api/tasks
            tasks_response = self.test_api_tasks_endpoint()
            if tasks_response["success"]:
                for task in tasks_response["data"]:
                    if task.get("task_id") == task_id:
                        status = task.get("status", "UNKNOWN")
                        logger.info(f"Task {task_id} status: {status}")

                        if status == "SUCCESS":
                            self.log_test(
                                "Task Completion",
                                True,
                                f"Task completed successfully in {time.time() - start_time:.1f}s",
                            )
                            return True
                        elif status == "FAILURE":
                            self.log_test(
                                "Task Completion",
                                False,
                                f"Task failed after {time.time() - start_time:.1f}s",
                            )
                            return False

            time.sleep(2)

        self.log_test(
            "Task Completion", False, f"Task did not complete within {max_wait} seconds"
        )
        return False

    def test_download_endpoint(self, task_id: str) -> bool:
        """Test markdown download endpoint."""
        try:
            response = self.session.get(f"{self.base_url}/download_markdown/{task_id}")
            success = response.status_code == 200

            details = f"Status: {response.status_code}"
            if success:
                content_length = len(response.content)
                details += f", Content length: {content_length} bytes"
                details += (
                    f", Content-Type: {response.headers.get('content-type', 'N/A')}"
                )
            else:
                details += f", Error: {response.text[:100]}..."

            self.log_test("Download Endpoint", success, details)
            return success
        except Exception as e:
            self.log_test("Download Endpoint", False, f"Error: {str(e)}")
            return False

    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive API tests."""
        logger.info("🚀 Starting comprehensive API tests...")

        # Basic connectivity tests
        self.test_health_endpoint()
        self.test_detailed_health_endpoint()
        self.test_root_endpoint()
        self.test_api_tasks_endpoint()

        # File upload and processing test
        upload_result = self.test_file_upload()

        if upload_result["success"]:
            task_id = upload_result["data"].get("task_id")
            if task_id:
                # Monitor task completion
                task_completed = self.test_task_monitoring(task_id, max_wait=60)

                # Test result endpoint
                self.test_task_result(task_id)

                # Test download if task completed
                if task_completed:
                    self.test_download_endpoint(task_id)

        # Summary
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)

        logger.info(f"\n📊 Test Summary: {passed}/{total} tests passed")

        # Print failed tests
        failed_tests = [result for result in self.test_results if not result["success"]]
        if failed_tests:
            logger.info("\n❌ Failed tests:")
            for test in failed_tests:
                logger.info(f"  - {test['test']}: {test['details']}")

        return {
            "passed": passed,
            "total": total,
            "success_rate": passed / total if total > 0 else 0,
            "results": self.test_results,
        }


def main():
    """Main test execution."""
    tester = APITester()
    results = tester.run_comprehensive_test()

    # Exit with appropriate code
    if results["success_rate"] == 1.0:
        logger.info("🎉 All tests passed!")
        exit(0)
    else:
        logger.error(f"⚠️ {results['total'] - results['passed']} tests failed!")
        exit(1)


if __name__ == "__main__":
    main()
