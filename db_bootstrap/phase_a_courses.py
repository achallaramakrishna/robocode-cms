from db_conn import get_connection


def find_existing_course(cursor, ctx):
    sql = """
        SELECT course_id
        FROM rd_courses
        WHERE course_name = %s
          AND course_category_id = %s
        LIMIT 1
    """
    cursor.execute(
        sql,
        (ctx["course_name"], ctx["course_category_id"])
    )
    row = cursor.fetchone()
    return row[0] if row else None


def insert_course(cursor, ctx):
    sql = """
        INSERT INTO rd_courses
        (
            course_name,
            course_category_id,
            category,
            course_level,
            tier_level,
            is_active
        )
        VALUES (%s, %s, %s, %s, %s, 1)
    """
    cursor.execute(
        sql,
        (
            ctx["course_name"],
            ctx["course_category_id"],
            ctx.get("subject"),
            ctx.get("board"),
            ctx.get("tier_level", "beginner").lower()
        )
    )
    return cursor.lastrowid


def ensure_course(ctx):
    conn = get_connection()
    cursor = conn.cursor()

    course_id = find_existing_course(cursor, ctx)

    if course_id:
        print(f"⏭️ Course already exists → course_id={course_id}")
        cursor.close()
        conn.close()
        return course_id

    course_id = insert_course(cursor, ctx)
    conn.commit()

    print(f"✅ Course inserted → course_id={course_id}")

    cursor.close()
    conn.close()
    return course_id
