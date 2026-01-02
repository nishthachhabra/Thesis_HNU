"""
Database Authentication Module
Handles user authentication using SQLite database
"""

import sqlite3
import os
from typing import Optional, Dict


class DatabaseAuth:
    """Handle authentication from SQLite database"""

    def __init__(self, db_path='database/hnu_users.db'):
        """Initialize with database path"""
        self.db_path = db_path

    def db_exists(self) -> bool:
        """Check if database exists"""
        return os.path.exists(self.db_path)

    def authenticate_student(self, user_id: str, password: str) -> Optional[Dict]:
        """
        Authenticate student
        Returns user info if authenticated, None otherwise
        """
        if not self.db_exists():
            return None

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, first_name, last_name, course, degree, gender, nationality
                FROM students
                WHERE LOWER(id) = LOWER(?) AND password = ?
            """, (user_id.strip(), password))

            result = cursor.fetchone()
            conn.close()

            if result:
                user_id, first_name, last_name, course, degree, gender, nationality = result
                return {
                    'user_id': user_id,
                    'name': f"{first_name} {last_name}".strip(),
                    'department': course or "Unknown",
                    'degree': degree or "Unknown",
                    'user_type': 'student',
                    'is_hr': False,
                    'is_guest': False,
                    'gender': gender,
                    'nationality': nationality
                }

            return None

        except sqlite3.Error:
            return None

    def authenticate_employee(self, user_id: str, password: str, require_hr: bool = False) -> Optional[Dict]:
        """
        Authenticate employee
        If require_hr=True, only HR department employees can authenticate
        Returns user info if authenticated, None otherwise
        """
        if not self.db_exists():
            return None

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, first_name, last_name, department, gender, nationality
                FROM employees
                WHERE LOWER(id) = LOWER(?) AND password = ?
            """, (user_id.strip(), password))

            result = cursor.fetchone()
            conn.close()

            if result:
                user_id, first_name, last_name, department, gender, nationality = result
                department_upper = (department or "Unknown").upper()
                is_hr = department_upper == 'HR'

                # If HR required but user is not HR, return error
                if require_hr and not is_hr:
                    return {
                        'error': 'not_hr',
                        'department': department_upper
                    }

                return {
                    'user_id': user_id,
                    'name': f"{first_name} {last_name}".strip(),
                    'department': department_upper,
                    'degree': None,
                    'user_type': 'admin' if require_hr else 'employee',
                    'is_hr': is_hr,
                    'is_guest': False,
                    'gender': gender,
                    'nationality': nationality
                }

            return None

        except sqlite3.Error:
            return None

    def get_user_count(self, user_type: str) -> int:
        """Get count of users by type"""
        if not self.db_exists():
            return 0

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            if user_type == 'student':
                cursor.execute("SELECT COUNT(*) FROM students")
            else:
                cursor.execute("SELECT COUNT(*) FROM employees")

            count = cursor.fetchone()[0]
            conn.close()
            return count

        except sqlite3.Error:
            return 0
