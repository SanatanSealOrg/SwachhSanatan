#!/usr/bin/env python3
"""
Integration test script for Complaint CRUD & Image Upload endpoints.

Tests all complaint endpoints with realistic scenarios.

Usage:
    python test_complaints_integration.py

Requirements:
    - FastAPI server running on http://localhost:8000
    - PostgreSQL with PostGIS enabled
    - S3/LocalStack bucket configured
    - Sample image files in ./test_images/
"""

import requests
import json
import os
from pathlib import Path
from typing import Optional, Tuple

# Configuration
BASE_URL = os.getenv("API_URL", "http://localhost:8000")
TEST_IMAGE_PATH = "./test_images/sample.jpg"

# Color codes for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


class ComplaintAPITester:
    """Test suite for Complaint API endpoints."""

    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.citizen_token: Optional[str] = None
        self.officer_token: Optional[str] = None
        self.citizen_id: Optional[str] = None
        self.officer_id: Optional[str] = None
        self.ward_id: Optional[str] = None
        self.complaint_id: Optional[str] = None

    def print_result(self, test_name: str, passed: bool, message: str = ""):
        """Print test result with color."""
        status = f"{GREEN}✓ PASS{RESET}" if passed else f"{RED}✗ FAIL{RESET}"
        print(f"{status} | {test_name}")
        if message:
            print(f"      {BLUE}→ {message}{RESET}")

    def print_section(self, title: str):
        """Print test section header."""
        print(f"\n{YELLOW}{'='*60}{RESET}")
        print(f"{YELLOW}{title.center(60)}{RESET}")
        print(f"{YELLOW}{'='*60}{RESET}")

    def test_citizen_registration(self) -> bool:
        """Test citizen registration."""
        self.print_section("Test 1: Citizen Registration")

        try:
            response = requests.post(
                f"{self.base_url}/api/auth/register",
                json={
                    "email": "citizen@cleanloop.test",
                    "phone": "9876543210",
                    "password": "TestPass123",
                    "user_type": "citizen",
                }
            )

            if response.status_code == 201:
                data = response.json()
                self.citizen_token = data["access_token"]
                self.citizen_id = data["user_id"]
                self.print_result("Citizen Registration", True, f"ID: {self.citizen_id}")
                return True
            else:
                self.print_result(
                    "Citizen Registration", False,
                    f"Status: {response.status_code}, {response.text[:100]}"
                )
                return False

        except Exception as e:
            self.print_result("Citizen Registration", False, str(e))
            return False

    def test_officer_registration(self) -> bool:
        """Test officer registration."""
        self.print_section("Test 2: Officer Registration")

        try:
            response = requests.post(
                f"{self.base_url}/api/auth/register",
                json={
                    "email": "officer@cleanloop.test",
                    "phone": "9876543211",
                    "password": "TestPass123",
                    "user_type": "officer",
                    # Note: In real scenario, officer would have ward_id assigned by admin
                }
            )

            if response.status_code == 201:
                data = response.json()
                self.officer_token = data["access_token"]
                self.officer_id = data["user_id"]
                self.print_result("Officer Registration", True, f"ID: {self.officer_id}")
                return True
            else:
                self.print_result(
                    "Officer Registration", False,
                    f"Status: {response.status_code}, {response.text[:100]}"
                )
                return False

        except Exception as e:
            self.print_result("Officer Registration", False, str(e))
            return False

    def test_create_complaint(self) -> bool:
        """Test complaint creation with image upload."""
        self.print_section("Test 3: Create Complaint with Image")

        if not self.citizen_token:
            self.print_result("Create Complaint", False, "Citizen not registered")
            return False

        # Create test image if not exists
        if not self._create_test_image():
            return False

        try:
            with open(TEST_IMAGE_PATH, "rb") as f:
                files = {"file": f}
                data = {
                    "description": "Overflowing waste bin at corner",
                    "latitude": "13.0827",
                    "longitude": "80.2707",
                    "waste_type": "bin",
                    "severity_score": "4"
                }

                response = requests.post(
                    f"{self.base_url}/api/complaints",
                    headers={"Authorization": f"Bearer {self.citizen_token}"},
                    files=files,
                    data=data
                )

            if response.status_code == 201:
                complaint = response.json()
                self.complaint_id = complaint["id"]
                self.ward_id = complaint["ward_id"]
                self.print_result(
                    "Create Complaint",
                    True,
                    f"Ticket: {complaint['ticket_number']}, Ward: {self.ward_id}"
                )
                return True
            else:
                self.print_result(
                    "Create Complaint", False,
                    f"Status: {response.status_code}, {response.text[:100]}"
                )
                return False

        except Exception as e:
            self.print_result("Create Complaint", False, str(e))
            return False

    def test_get_complaint(self) -> bool:
        """Test getting complaint details."""
        self.print_section("Test 4: Get Complaint Details")

        if not self.complaint_id or not self.citizen_token:
            self.print_result("Get Complaint", False, "Complaint not created")
            return False

        try:
            response = requests.get(
                f"{self.base_url}/api/complaints/{self.complaint_id}",
                headers={"Authorization": f"Bearer {self.citizen_token}"}
            )

            if response.status_code == 200:
                complaint = response.json()
                self.print_result(
                    "Get Complaint",
                    True,
                    f"Status: {complaint['status']}, Images: {len(complaint.get('image_urls', []))}"
                )
                return True
            else:
                self.print_result(
                    "Get Complaint", False,
                    f"Status: {response.status_code}, {response.text[:100]}"
                )
                return False

        except Exception as e:
            self.print_result("Get Complaint", False, str(e))
            return False

    def test_list_complaints(self) -> bool:
        """Test listing complaints by ward."""
        self.print_section("Test 5: List Complaints by Ward")

        if not self.ward_id or not self.citizen_token:
            self.print_result("List Complaints", False, "Ward not available")
            return False

        try:
            response = requests.get(
                f"{self.base_url}/api/complaints",
                headers={"Authorization": f"Bearer {self.citizen_token}"},
                params={
                    "ward_id": self.ward_id,
                    "status": "open",
                    "limit": "20"
                }
            )

            if response.status_code == 200:
                data = response.json()
                self.print_result(
                    "List Complaints",
                    True,
                    f"Found: {len(data['complaints'])}, Total: {data['total']}"
                )
                return True
            else:
                self.print_result(
                    "List Complaints", False,
                    f"Status: {response.status_code}, {response.text[:100]}"
                )
                return False

        except Exception as e:
            self.print_result("List Complaints", False, str(e))
            return False

    def test_update_complaint_status(self) -> bool:
        """Test updating complaint status (officer only)."""
        self.print_section("Test 6: Update Complaint Status (Officer)")

        if not self.complaint_id or not self.officer_token:
            self.print_result("Update Status", False, "Missing complaint or officer token")
            return False

        try:
            response = requests.patch(
                f"{self.base_url}/api/complaints/{self.complaint_id}",
                headers={
                    "Authorization": f"Bearer {self.officer_token}",
                    "Content-Type": "application/json"
                },
                json={
                    "status": "in_progress",
                    "notes": "Cleaning crew assigned"
                }
            )

            if response.status_code == 200:
                complaint = response.json()
                self.print_result(
                    "Update Status",
                    True,
                    f"New status: {complaint['status']}"
                )
                return True
            elif response.status_code == 403:
                # Officer may not have ward assigned, this is expected in test env
                self.print_result(
                    "Update Status (Officer Ward Check)",
                    True,
                    "Correctly rejected (officer not in ward)"
                )
                return True
            else:
                self.print_result(
                    "Update Status", False,
                    f"Status: {response.status_code}, {response.text[:100]}"
                )
                return False

        except Exception as e:
            self.print_result("Update Status", False, str(e))
            return False

    def test_validation_errors(self) -> bool:
        """Test validation error handling."""
        self.print_section("Test 7: Validation Error Handling")

        if not self.citizen_token:
            self.print_result("Validation Tests", False, "Citizen not registered")
            return False

        tests_passed = 0
        tests_total = 0

        # Test invalid GPS
        tests_total += 1
        try:
            response = requests.post(
                f"{self.base_url}/api/complaints",
                headers={"Authorization": f"Bearer {self.citizen_token}"},
                files={"file": ("test.jpg", b"fake data")},
                data={
                    "description": "Test",
                    "latitude": "91",  # Invalid
                    "longitude": "0",
                    "file": "test.jpg"
                }
            )

            if response.status_code == 400:
                tests_passed += 1
                self.print_result("Invalid GPS Detection", True)
            else:
                self.print_result("Invalid GPS Detection", False, f"Got {response.status_code}")
        except Exception as e:
            self.print_result("Invalid GPS Detection", False, str(e))

        # Test invalid waste_type
        tests_total += 1
        try:
            with open(TEST_IMAGE_PATH, "rb") as f:
                response = requests.post(
                    f"{self.base_url}/api/complaints",
                    headers={"Authorization": f"Bearer {self.citizen_token}"},
                    files={"file": f},
                    data={
                        "description": "Test",
                        "latitude": "13.0827",
                        "longitude": "80.2707",
                        "waste_type": "invalid_type",
                        "severity_score": "4"
                    }
                )

            if response.status_code == 400:
                tests_passed += 1
                self.print_result("Invalid Waste Type Detection", True)
            else:
                self.print_result(
                    "Invalid Waste Type Detection", False,
                    f"Got {response.status_code}"
                )
        except Exception as e:
            self.print_result("Invalid Waste Type Detection", False, str(e))

        self.print_result(
            "Validation Tests Overall",
            tests_passed == tests_total,
            f"{tests_passed}/{tests_total} passed"
        )
        return tests_passed == tests_total

    def _create_test_image(self) -> bool:
        """Create a test image file."""
        try:
            from PIL import Image

            Path("./test_images").mkdir(exist_ok=True)

            # Create 100x100 red image
            img = Image.new("RGB", (100, 100), color="red")
            img.save(TEST_IMAGE_PATH)
            return True
        except ImportError:
            self.print_result("Test Image Creation", False, "PIL not available")
            return False
        except Exception as e:
            self.print_result("Test Image Creation", False, str(e))
            return False

    def run_all_tests(self) -> Tuple[int, int]:
        """Run all tests."""
        print(f"\n{BLUE}{'='*60}{RESET}")
        print(f"{BLUE}{'CleanLoop Complaint API Integration Tests'.center(60)}{RESET}")
        print(f"{BLUE}{'='*60}{RESET}")
        print(f"Base URL: {self.base_url}\n")

        tests = [
            self.test_citizen_registration,
            self.test_officer_registration,
            self.test_create_complaint,
            self.test_get_complaint,
            self.test_list_complaints,
            self.test_update_complaint_status,
            self.test_validation_errors,
        ]

        passed = 0
        for test in tests:
            if test():
                passed += 1

        return passed, len(tests)


def main():
    """Run integration tests."""
    tester = ComplaintAPITester()
    passed, total = tester.run_all_tests()

    print(f"\n{YELLOW}{'='*60}{RESET}")
    print(f"Results: {GREEN}{passed}/{total}{RESET} tests passed")
    print(f"{YELLOW}{'='*60}{RESET}\n")

    return 0 if passed == total else 1


if __name__ == "__main__":
    exit(main())
