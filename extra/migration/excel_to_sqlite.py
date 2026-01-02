"""
Excel to SQLite Migration Script
Converts students.xlsx and employees.xlsx to SQLite database
"""

import pandas as pd
import sqlite3
from pathlib import Path
from datetime import datetime


class ExcelToSQLite:
    """Migrate Excel data to SQLite database"""

    def __init__(self, db_name='hnu_users.db'):
        """
        Initialize the migration tool

        Args:
            db_name: Name of the SQLite database file
        """
        self.db_name = db_name
        self.conn = None
        self.cursor = None

    def connect(self):
        """Connect to SQLite database"""
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        print(f"✅ Connected to database: {self.db_name}")

    def create_tables(self):
        """Create database tables"""

        # Students table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id TEXT PRIMARY KEY,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                gender TEXT,
                nationality TEXT,
                course TEXT,
                degree TEXT,
                password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Employees table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS employees (
                id TEXT PRIMARY KEY,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                gender TEXT,
                nationality TEXT,
                password TEXT NOT NULL,
                department TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create indexes for faster lookups
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_students_id ON students(id)
        ''')

        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_employees_id ON employees(id)
        ''')

        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_employees_dept ON employees(department)
        ''')

        self.conn.commit()
        print("✅ Tables created successfully")

    def migrate_students(self, excel_file='students.xlsx'):
        """
        Migrate students data from Excel to SQLite

        Args:
            excel_file: Path to students Excel file
        """
        if not Path(excel_file).exists():
            print(f"❌ File not found: {excel_file}")
            return False

        try:
            # Read Excel file
            df = pd.read_excel(excel_file)
            print(f"\n📚 Reading {excel_file}...")
            print(f"   Columns: {df.columns.tolist()}")
            print(f"   Rows: {len(df)}")

            # Normalize column names
            df.columns = [col.strip().lower().replace(' ', '_') for col in df.columns]

            # Map columns to database fields
            column_mapping = {
                'id': 'id',
                'firstname': 'first_name',
                'lastname': 'last_name',
                'gender': 'gender',
                'nationality': 'nationality',
                'course': 'course',
                'degree': 'degree',
                'password': 'password'
            }

            # Rename columns
            df = df.rename(columns=column_mapping)

            # Insert data
            inserted = 0
            skipped = 0

            for idx, row in df.iterrows():
                try:
                    self.cursor.execute('''
                        INSERT OR REPLACE INTO students
                        (id, first_name, last_name, gender, nationality, course, degree, password)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        str(row['id']).strip(),
                        str(row['first_name']).strip(),
                        str(row['last_name']).strip(),
                        str(row.get('gender', '')).strip(),
                        str(row.get('nationality', '')).strip(),
                        str(row.get('course', '')).strip(),
                        str(row.get('degree', '')).strip(),
                        str(row['password']).strip()
                    ))
                    inserted += 1
                except Exception as e:
                    print(f"   ⚠️ Row {idx + 1} skipped: {e}")
                    skipped += 1

            self.conn.commit()
            print(f"✅ Students migrated: {inserted} inserted, {skipped} skipped")
            return True

        except Exception as e:
            print(f"❌ Error migrating students: {e}")
            return False

    def migrate_employees(self, excel_file='employees.xlsx'):
        """
        Migrate employees data from Excel to SQLite

        Args:
            excel_file: Path to employees Excel file
        """
        if not Path(excel_file).exists():
            print(f"❌ File not found: {excel_file}")
            return False

        try:
            # Read Excel file
            df = pd.read_excel(excel_file)
            print(f"\n👔 Reading {excel_file}...")
            print(f"   Columns: {df.columns.tolist()}")
            print(f"   Rows: {len(df)}")

            # Normalize column names
            df.columns = [col.strip().lower().replace(' ', '_') for col in df.columns]

            # Map columns to database fields
            column_mapping = {
                'id': 'id',
                'firstname': 'first_name',
                'lastname': 'last_name',
                'gender': 'gender',
                'nationality': 'nationality',
                'password': 'password',
                'department': 'department'
            }

            # Rename columns
            df = df.rename(columns=column_mapping)

            # Insert data
            inserted = 0
            skipped = 0

            for idx, row in df.iterrows():
                try:
                    self.cursor.execute('''
                        INSERT OR REPLACE INTO employees
                        (id, first_name, last_name, gender, nationality, password, department)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        str(row['id']).strip(),
                        str(row['first_name']).strip(),
                        str(row['last_name']).strip(),
                        str(row.get('gender', '')).strip(),
                        str(row.get('nationality', '')).strip(),
                        str(row['password']).strip(),
                        str(row['department']).strip()
                    ))
                    inserted += 1
                except Exception as e:
                    print(f"   ⚠️ Row {idx + 1} skipped: {e}")
                    skipped += 1

            self.conn.commit()
            print(f"✅ Employees migrated: {inserted} inserted, {skipped} skipped")
            return True

        except Exception as e:
            print(f"❌ Error migrating employees: {e}")
            return False

    def verify_migration(self):
        """Verify the migration by counting records"""
        print("\n" + "="*50)
        print("📊 MIGRATION VERIFICATION")
        print("="*50)

        # Count students
        self.cursor.execute("SELECT COUNT(*) FROM students")
        students_count = self.cursor.fetchone()[0]
        print(f"📚 Students in database: {students_count}")

        # Count employees
        self.cursor.execute("SELECT COUNT(*) FROM employees")
        employees_count = self.cursor.fetchone()[0]
        print(f"👔 Employees in database: {employees_count}")

        # Show sample student
        print("\n📚 Sample Student:")
        self.cursor.execute("SELECT * FROM students LIMIT 1")
        student = self.cursor.fetchone()
        if student:
            print(f"   ID: {student[0]}")
            print(f"   Name: {student[1]} {student[2]}")
            print(f"   Course: {student[5]}, Degree: {student[6]}")

        # Show sample employee
        print("\n👔 Sample Employee:")
        self.cursor.execute("SELECT * FROM employees LIMIT 1")
        employee = self.cursor.fetchone()
        if employee:
            print(f"   ID: {employee[0]}")
            print(f"   Name: {employee[1]} {employee[2]}")
            print(f"   Department: {employee[6]}")

        # Show departments
        print("\n🏛️ Departments:")
        self.cursor.execute("SELECT department, COUNT(*) FROM employees GROUP BY department")
        departments = self.cursor.fetchall()
        for dept, count in departments:
            print(f"   {dept}: {count} employees")

        # Show courses
        print("\n📖 Courses:")
        self.cursor.execute("SELECT course, COUNT(*) FROM students GROUP BY course")
        courses = self.cursor.fetchall()
        for course, count in courses:
            print(f"   {course}: {count} students")

        print("\n" + "="*50)

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            print("\n✅ Database connection closed")


def main():
    """Main migration function"""
    print("="*50)
    print("🔄 EXCEL TO SQLITE MIGRATION")
    print("="*50)

    # Initialize migrator
    migrator = ExcelToSQLite('hnu_users.db')

    try:
        # Connect to database
        migrator.connect()

        # Create tables
        migrator.create_tables()

        # Migrate students
        migrator.migrate_students('students.xlsx')

        # Migrate employees
        migrator.migrate_employees('employees.xlsx')

        # Verify migration
        migrator.verify_migration()

        print("\n✅ Migration completed successfully!")
        print(f"📁 Database file: {migrator.db_name}")

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Close connection
        migrator.close()


if __name__ == "__main__":
    main()
