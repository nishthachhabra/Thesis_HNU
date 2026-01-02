# 📊 Data Migration Folder

This folder contains all files related to migrating user data from Excel to SQLite database.

## 📁 Files

### Excel Source Files
- **`students.xlsx`** (13 KB) - Original student data with 50 records
  - Columns: ID, FirstName, LastName, Gender, Nationality, Course, Degree, Password
  - Courses: AIDA (26), DIM (11), SIM (13)

- **`employees.xlsx`** (8.0 KB) - Original employee data with 50 records
  - Columns: ID, FirstName, LastName, Gender, Nationality, Password, Department
  - Departments: HR (15), Tech (8), Professor (11), Admin (10), Sales (6)

### Migration Script
- **`excel_to_sqlite.py`** (10 KB) - Python script to migrate Excel data to SQLite
  - Creates 2 tables: `students` and `employees`
  - Includes indexes for performance
  - Auto-generates timestamps

### Database
- **`hnu_users.db`** (48 KB) - SQLite database containing migrated data
  - **Table 1**: `students` (50 records)
  - **Table 2**: `employees` (50 records)

---

## 🚀 How to Run Migration

### Option 1: Run the script directly
```bash
cd /Users/yatin/Desktop/thesis_nishtha_2025/HNUChatbot/migration
conda activate nish
python excel_to_sqlite.py
```

### Option 2: Import and use programmatically
```python
from excel_to_sqlite import ExcelToSQLite

# Create migrator
migrator = ExcelToSQLite('hnu_users.db')
migrator.connect()
migrator.create_tables()
migrator.migrate_students('students.xlsx')
migrator.migrate_employees('employees.xlsx')
migrator.verify_migration()
migrator.close()
```

---

## 📊 Database Schema

### Students Table
```sql
CREATE TABLE students (
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
);
```

### Employees Table
```sql
CREATE TABLE employees (
    id TEXT PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    gender TEXT,
    nationality TEXT,
    password TEXT NOT NULL,
    department TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🔍 Querying the Database

### Connect to database
```python
import sqlite3
conn = sqlite3.connect('migration/hnu_users.db')
cursor = conn.cursor()
```

### Query examples
```python
# Get all students
cursor.execute("SELECT * FROM students")
students = cursor.fetchall()

# Get all employees
cursor.execute("SELECT * FROM employees")
employees = cursor.fetchall()

# Get HR employees only
cursor.execute("SELECT * FROM employees WHERE department = 'HR'")
hr_employees = cursor.fetchall()

# Get students by course
cursor.execute("SELECT * FROM students WHERE course = 'AIDA'")
aida_students = cursor.fetchall()

# Authenticate student
cursor.execute("SELECT * FROM students WHERE id = ? AND password = ?", ('QK51', 'Qahft1'))
student = cursor.fetchone()
```

---

## 📈 Migration Statistics

✅ **Students**: 50 records migrated
✅ **Employees**: 50 records migrated
✅ **Indexes**: 3 indexes created for performance
✅ **Total database size**: 48 KB

---

## 🔧 Dependencies

- Python 3.x
- pandas
- openpyxl
- sqlite3 (built-in)

Install with:
```bash
pip install pandas openpyxl
```

---

## 📝 Notes

- The migration script uses `INSERT OR REPLACE` to handle duplicates
- IDs are case-sensitive and stored as TEXT
- Passwords are stored as plain text (for development only - use hashing in production!)
- All timestamps are auto-generated
- The database file is portable and can be moved anywhere

---

## ⚠️ Important

**For Production Use:**
- Implement password hashing (bcrypt, argon2)
- Add proper authentication mechanisms
- Use environment variables for sensitive data
- Implement proper error handling
- Add logging for audit trails
- Consider database migrations for schema changes
