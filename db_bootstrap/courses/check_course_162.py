"""
check_course_162.py - Confirm course 162 details in prod.
"""
import mysql.connector

conn = mysql.connector.connect(
    host="localhost", user="root", password="Jatni@752050",
    database="robodynamics_db", charset="utf8mb4"
)
cur = conn.cursor()

# 1. Course record
print("=" * 70)
print("COURSE 162 — DETAILS")
print("=" * 70)
cur.execute("""
    SELECT course_id, course_name, course_level, course_status,
           course_start_date, course_end_date, course_instructor,
           is_active, category, course_duration
    FROM rd_courses WHERE course_id = 162
""")
row = cur.fetchone()
if row:
    labels = ["course_id","course_name","course_level","course_status",
              "start_date","end_date","instructor","is_active","category","duration"]
    for l, v in zip(labels, row):
        print(f"  {l:<20} = {v}")
else:
    print("  NOT FOUND")

# 2. Sessions
print("\n" + "=" * 70)
print("SESSIONS (rd_course_sessions)")
print("=" * 70)
cur.execute("""
    SELECT course_session_id, tier_order, session_title,
           session_uuid, tier_level
    FROM rd_course_sessions
    WHERE course_id = 162
    ORDER BY tier_order
""")
sessions = cur.fetchall()
print(f"  Total sessions: {len(sessions)}")
print(f"  {'ID':<8} {'Order':<6} {'UUID':<38} {'Title'}")
print(f"  {'-'*8} {'-'*6} {'-'*38} {'-'*40}")
for s in sessions:
    print(f"  {s[0]:<8} {s[1]:<6} {str(s[3]):<38} {s[2][:60]}")

# 3. Session details (assets) for first session
print("\n" + "=" * 70)
print("SESSION DETAILS — Session 1 assets (rd_course_session_details)")
print("=" * 70)
if sessions:
    first_sid = sessions[0][0]
    cur.execute("""
        SELECT course_session_detail_id, type, topic, file, tier_level
        FROM rd_course_session_details
        WHERE course_session_id = %s
    """, (first_sid,))
    details = cur.fetchall()
    for d in details:
        print(f"  detail_id={d[0]}  type={d[1]:<14} file={d[3]}")

# 4. Total assets across all sessions
print("\n" + "=" * 70)
print("TOTAL ASSETS ACROSS ALL SESSIONS")
print("=" * 70)
cur.execute("""
    SELECT type, COUNT(*) as cnt
    FROM rd_course_session_details
    WHERE course_id = 162
    GROUP BY type ORDER BY cnt DESC
""")
for row in cur.fetchall():
    print(f"  {row[0]:<20} : {row[1]} rows")

# 5. Enrollments
print("\n" + "=" * 70)
print("ENROLLED STUDENTS")
print("=" * 70)
try:
    cur.execute("""
        SELECT e.enrollment_id, u.username, u.email, e.enrollment_date, e.status
        FROM rd_enrollments e
        JOIN rd_users u ON u.user_id = e.user_id
        WHERE e.course_id = 162
    """)
    enroll = cur.fetchall()
    if enroll:
        for e in enroll:
            print(f"  enrollment_id={e[0]}  user={e[1]}  email={e[2]}  date={e[3]}  status={e[4]}")
    else:
        print("  No enrollments found")
except Exception as ex:
    print(f"  (enrollment query error: {ex})")

conn.close()
print("\nDone.")
