"""
check_courses.py - List all courses and session_materials content on prod.
"""
import mysql.connector
import os

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Jatni@752050",
    database="robodynamics_db",
    charset="utf8mb4"
)
cur = conn.cursor()

# 1. Describe the courses table to get correct column names
print("=" * 70)
print("rd_courses TABLE COLUMNS:")
print("=" * 70)
cur.execute("DESCRIBE rd_courses")
cols = cur.fetchall()
col_names = [c[0] for c in cols]
for c in cols:
    print(f"  {c[0]:30s}  {c[1]}")

print()

# 2. Fetch all courses dynamically
cur.execute("SELECT * FROM rd_courses ORDER BY course_id LIMIT 200")
rows = cur.fetchall()

print("=" * 100)
header = " | ".join(f"{col_names[i]}" for i in range(len(col_names)))
print(header)
print("-" * 100)
for row in rows:
    line = " | ".join(str(v)[:40] if v is not None else "NULL" for v in row)
    print(line)

print(f"\nTotal courses: {len(rows)}")

# 3. Session counts per course
print("\n" + "=" * 70)
print("SESSION COUNTS PER COURSE:")
print("=" * 70)
cur.execute("""
    SELECT c.course_id, c.course_name, COUNT(cs.course_session_id) as sessions
    FROM rd_courses c
    LEFT JOIN rd_course_sessions cs ON cs.course_id = c.course_id
    GROUP BY c.course_id
    ORDER BY c.course_id
""")
sc_rows = cur.fetchall()
for r in sc_rows:
    print(f"  course_id={r[0]:4d}  sessions={r[2]:3d}  |  {r[1]}")

# 4. session_materials directory
print("\n" + "=" * 70)
print("SESSION MATERIALS  (/opt/robodynamics/session_materials/)")
print("=" * 70)
base = "/opt/robodynamics/session_materials"
if os.path.exists(base):
    course_dirs = sorted(d for d in os.listdir(base) if os.path.isdir(os.path.join(base, d)))
    if not course_dirs:
        print("  (directory exists but is empty)")
    for d in course_dirs:
        dpath = os.path.join(base, d)
        files = [f for f in os.listdir(dpath) if os.path.isfile(os.path.join(dpath, f))]
        html_f = [f for f in files if f.endswith('.html')]
        pdf_f  = [f for f in files if f.endswith('.pdf')]
        print(f"\n  course_id={d}:  {len(html_f)} HTML  |  {len(pdf_f)} PDF  |  {len(files)} total files")
        for f in sorted(files):
            sz = os.path.getsize(os.path.join(dpath, f)) // 1024
            print(f"    {f:<60s}  ({sz} KB)")
else:
    print(f"  Does not exist: {base}")
    # Check alternate
    alt = "/opt/robodynamics/sessionMaterials"
    if os.path.exists(alt):
        print(f"\n  Found alternate path: {alt}")
        for item in os.listdir(alt):
            print(f"    {item}")

conn.close()
print("\nDone.")
