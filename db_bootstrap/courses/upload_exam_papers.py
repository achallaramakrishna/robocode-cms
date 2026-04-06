"""
upload_exam_papers.py
=====================
Uploads generated exam paper JSONs to correct asset paths on prod.
Creates the directory structure if it doesn't exist.

Maps course_id → session_uuid (from exam_prep_setup.py output)
Then uploads: exam_prep_final_*.json →
  /opt/robodynamics/cms-engine/workspace/courses/{course_id}/chapters/{session_uuid}/assets/exam_papers/

Run locally via pscp, or run this script on prod to copy from a staging folder.
"""

import os
import shutil

# Mapping: (course_id, session_uuid, exam_file)
EXAM_FILES = [
    (154, "bb2e30fa-d5f6-4fb6-a5fa-8269c104822f", "exam_prep_final_icse_grade10_154.json"),
    (155, "e062ac18-33a6-4e68-90e2-40320cd3466e", "exam_prep_final_icse_grade10_155.json"),
    (156, "bb80fd2f-4d9d-4891-bddf-0b394368fc84", "exam_prep_final_icse_grade10_156.json"),
    (35,  "2cc17ac3-82f8-45e8-95da-5923b7fbc6b7", "exam_prep_final_cbse_grade6_35.json"),
    (34,  "e6df4b61-17d9-468f-8b11-498dfbce35b5", "exam_prep_final_cbse_grade5_34.json"),
    (33,  "3faf9f28-9a3d-4101-975b-23468c458321", "exam_prep_final_cbse_grade4_33.json"),
    (149, "676fc29a-3e33-432b-bbf4-bc3cf00e5cbc", "exam_prep_final_cbse_grade7_149.json"),
    (65,  "951c916e-f235-4138-821e-8bc63b5dfaf1", "exam_prep_final_cbse_grade8_65.json"),
    # Tier 1B
    (47,  "7c8d530a-163a-46ac-8d35-fbbc497b1964", "exam_prep_final_icse_grade5_science_47.json"),
    (66,  "4f4762c0-4b55-48c9-b531-74c8acc75d51", "exam_prep_final_icse_grade5_mathematics_66.json"),
    (43,  "26fa1e40-4977-4614-af65-4c890490ea9c", "exam_prep_final_cbse_grade6_mathematics_43.json"),
    (39,  "af8f6b72-3aca-4033-9b12-9c1f6f1d8249", "exam_prep_final_cbse_grade6_mathematics_39.json"),
    (56,  "d0361e29-abb8-4c4f-916c-0306af54c8ef", "exam_prep_final_cbse_grade4_hindi_56.json"),
    (72,  "dacb1ed7-42c5-4dd8-8cda-74422a53bf29", "exam_prep_final_cbse_grade4_hindi_72.json"),
]

STAGING_DIR = "/opt/robodynamics/cms-engine/db_bootstrap/exam_papers_staging"
BASE_WORKSPACE = "/opt/robodynamics/cms-engine/workspace/courses"

copied = []
missing = []

for course_id, session_uuid, exam_file in EXAM_FILES:
    src = os.path.join(STAGING_DIR, exam_file)
    dest_dir = os.path.join(BASE_WORKSPACE, str(course_id), "chapters", session_uuid, "assets", "exam_papers")
    dest = os.path.join(dest_dir, exam_file)

    if not os.path.exists(src):
        print(f"  MISSING staging file: {exam_file}")
        missing.append(exam_file)
        continue

    os.makedirs(dest_dir, exist_ok=True)
    shutil.copy2(src, dest)
    size_kb = os.path.getsize(dest) // 1024
    print(f"  OK  course={course_id}  {exam_file}  ({size_kb} KB)  →  {dest_dir}")
    copied.append(exam_file)

print(f"\nCopied : {len(copied)}")
print(f"Missing: {len(missing)}")
if missing:
    print("Missing files (not yet generated):")
    for f in missing:
        print(f"  {f}")
