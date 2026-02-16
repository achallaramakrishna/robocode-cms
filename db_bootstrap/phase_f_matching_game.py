# -------------------------------------------------
# 🔹 Matching Game
# -------------------------------------------------

def insert_matching_game(cursor, session_detail_pk, game_meta):

    cursor.execute("""
        INSERT INTO rd_matching_games
        (
            name,
            description,
            course_session_detail_id
        )
        VALUES (%s, %s, %s)
    """, (
        game_meta.get("name"),
        game_meta.get("description"),
        session_detail_pk
    ))

    return cursor.lastrowid


def insert_matching_category(cursor, game_id, category):

    cursor.execute("""
        INSERT INTO rd_matching_categories
        (
            game_id,
            category_name
        )
        VALUES (%s, %s)
    """, (
        game_id,
        category.get("categoryName")
    ))

    return cursor.lastrowid


def insert_matching_item(cursor, item, category_id):

    cursor.execute("""
        INSERT INTO rd_matching_items
        (
            item_name,
            correct_category_id,
            matching_text,
            image_name
        )
        VALUES (%s, %s, %s, %s)
    """, (
        item.get("itemName"),
        category_id,
        item.get("matchingText"),
        item.get("imageName")
    ))
