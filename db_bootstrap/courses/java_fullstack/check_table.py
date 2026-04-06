import sys
sys.path.insert(0, "/opt/robodynamics/cms-engine/db_bootstrap")
from db_conn import get_connection

conn = get_connection()
c = conn.cursor()

# Describe the table
c.execute("DESCRIBE rd_course_session_details")
print("=== rd_course_session_details columns ===")
for r in c.fetchall():
    print(r)

print()

# Count rows for session 1
c.execute("SELECT COUNT(*) FROM rd_course_session_details WHERE course_session_id = 2669")
print(f"Rows for session 1 (id=2669): {c.fetchone()[0]}")

# Sample rows
c.execute("SELECT * FROM rd_course_session_details WHERE course_session_id = 2669 ORDER BY session_detail_id LIMIT 5")
rows = c.fetchall()
print(f"\nFirst 5 rows:")
for r in rows:
    print(r)

conn.close()
