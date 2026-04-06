"""
bootstrap_prod.py
=================
Self-contained bootstrap for prod VPS.
Runs directly on /opt/robodynamics/cms-engine/ using the prod venv.

Usage:
    /opt/robodynamics/venv/bin/python3 bootstrap_prod.py --phase ALL
"""

import sys
import os
import json
import uuid
import argparse
from pathlib import Path

# ── prod paths ────────────────────────────────────────────────────────────────
BOOTSTRAP_DIR  = Path("/opt/robodynamics/cms-engine/db_bootstrap")
WORKSPACE_BASE = Path("/opt/robodynamics/cms-engine/workspace/courses")
SCRIPT_DIR     = Path(__file__).resolve().parent

sys.path.insert(0, str(BOOTSTRAP_DIR))
from db_conn import get_connection

# ── course definition ─────────────────────────────────────────────────────────
COURSE = {
    "course_name":        "Java Full Stack - 120 Hours",
    "course_category_id": 8,
    "subject":            "Java Full Stack",
    "board":              "Industry",
    "tier_level":         "beginner",
    "description":        "Comprehensive 120-hour Java Full Stack training covering Core Java 8, Spring Boot, Hibernate/JPA, React, Node.js, SQL, PL/SQL, JUnit, Git and Jenkins. Instructor-Led (30 sessions x 4 hrs each)."
}

SESSIONS = [
    {"day": 1,  "session_title": "Day 1 - Core Java: Introduction & Language Fundamentals",
     "session_description": "Introduction to Java, Language Fundamentals, Primitive Data Types, Operators, Flow Control, Classes and Objects.",
     "topics": ["Introduction to Java","Language Fundamentals","Primitive Data Types","Operators and Assignments","Flow Control: Java Control Statements","Classes and Objects","Access Specifiers","Constructors: Default and Parameterized","this reference","Using static keyword","Best Practices"]},

    {"day": 2,  "session_title": "Day 2 - Core Java: Exploring Java Basics & OOP",
     "session_description": "Wrapper Classes, Type Casting, String Handling, Inheritance, Polymorphism and Abstract Classes/Interfaces.",
     "topics": ["Wrapper Classes","Type casting","String Handling","Inheritance","Using super keyword","Method and Constructor overloading","Method overriding","Using final keyword","Abstract class","Interfaces","Default and static methods on Interface","Runtime Polymorphism","Best Practices"]},

    {"day": 3,  "session_title": "Day 3 - Core Java: Exception Handling & Arrays",
     "session_description": "Complete Exception Handling lifecycle and Arrays with varargs.",
     "topics": ["Exception Types and Hierarchy","Try-catch-finally","Try-with-resources","Multi catch blocks","Throwing exceptions using throw","Declaring exceptions using throws","User defined Exceptions","One dimensional array","Using varargs","Using Arrays class","Best Practices"]},

    {"day": 4,  "session_title": "Day 4 - Core Java: Collections, Generics & Property Files",
     "session_description": "Java Collections Framework, Generics, Comparable/Comparator and Property Files.",
     "topics": ["Collections Framework","Collection Interfaces","Implementing Classes","Iterating Collections using foreach and iterator","Comparable and Comparator","Using Generics with Collections","What are Property Files","Types of Property files","User defined Properties","Best Practices"]},

    {"day": 5,  "session_title": "Day 5 - Basic Git",
     "session_description": "Version Control with Git from installation to collaborative workflows.",
     "topics": ["Introduction to Version Control Systems","Understanding Git: What is Git and Why to Use it","Git Basics: Installation and Configuration","Git Workflow: Working with Local Repositories","Branching and Merging in Git","Collaborative Development with Remote Repositories","Resolving Conflicts and Undoing Changes","Git Best Practices and Tips","Git Hosting Services: GitHub, GitLab, Bitbucket"]},

    {"day": 6,  "session_title": "Day 6 - Jenkins (CI/CD)",
     "session_description": "Continuous Integration and Deployment with Jenkins.",
     "topics": ["Introduction to CI/CD","Understanding Jenkins","Jenkins Installation and Configuration","Creating and Running Jenkins Jobs","Jenkins Pipelines: Introduction and Basics","Integrating Jenkins with Git","Jenkins Plugins and Extensions","Monitoring and Troubleshooting Jenkins Builds","Best Practices for Jenkins","Hands-on Exercises"]},

    {"day": 7,  "session_title": "Day 7 - JUnit (Unit Testing & TDD)",
     "session_description": "Unit Testing and Test-Driven Development with JUnit and Mockito.",
     "topics": ["Introduction to Unit Testing and TDD","Understanding JUnit","Setting Up Java Environment for JUnit","Writing Your First JUnit Test Cases","Test Suites and Test Fixtures","Assertions and Test Annotations","Parameterized Tests in JUnit","Mocking and Stubbing with Mockito","Best Practices for Unit Tests","Hands-on Exercises"]},

    {"day": 8,  "session_title": "Day 8 - JavaScript Basics & DOM",
     "session_description": "JavaScript fundamentals, ECMAScript versions, DOM manipulation and events.",
     "topics": ["JavaScript Basics","JavaScript or ECMAScript?","Which Version of JavaScript am I Using?","Writing and Testing JavaScript","Editors and the F12 Tools","Key Parts of a Script","The Document Object Model (DOM)","Accessing Objects from the DOM","Responding to Events","Adding Elements to the DOM"]},

    {"day": 9,  "session_title": "Day 9 - jQuery, Ajax & RESTful Web Services",
     "session_description": "jQuery library, Ajax calls, RESTful Web Services and OData.",
     "topics": ["Introduction to jQuery","Downloading the jQuery Library","Selecting Elements using jQuery","Working with Data Returned by jQuery","Setting CSS Properties","Running Functions Against jQuery Return Set","Web Services and HTTP Verbs","Data Formats XML and JSON","Ajax","RESTful Web Services","OData Queries and Updates"]},

    {"day": 10, "session_title": "Day 10 - Spring Boot Introduction",
     "session_description": "Spring Boot starters, DI, component scans, configuration and logging.",
     "topics": ["Spring Boot starters, CLI, Gradle plugin","Application class and @SpringBootApplication","Dependency injection","Component scans","Configuration","Externalize configuration using application.properties","Context Root and Management ports","Logging","Build Systems","Structuring Your Code","Spring Beans and Dependency Injection"]},

    {"day": 11, "session_title": "Day 11 - Spring Boot Essentials & Spring Data JPA",
     "session_description": "Spring Boot Essentials and Spring Data JPA repository patterns.",
     "topics": ["Application Development and Configuration","Embedded Servers","Data Access","Common application properties","Auto-configuration classes","Spring Boot Dependencies","Spring Data JPA Intro and Overview","Core Concepts and @RepositoryRestResource","Defining Query methods","Query Creation","Using JPA Named Queries","Defining Repository Interfaces","Creating Repository instances","JPA Repositories","Persisting Entities and Transactions"]},

    {"day": 12, "session_title": "Day 12 - Spring Data REST & Spring Framework Core",
     "session_description": "Spring Data REST and Spring Framework IoC, DI, Bean scopes and lifecycle.",
     "topics": ["Spring Data REST Introduction and Overview","Adding Spring Data REST to a Spring Boot Project","Configuring Spring Data REST","Repository resources, Status Codes, Http methods","Spring Data REST Associations","Introduction to Spring Framework","Dependency Injection and AOP","Configuring Spring Beans using XML and annotations","DI and IoC in Spring","Bean scopes and Lifecycle in Spring"]},

    {"day": 13, "session_title": "Day 13 - Spring MVC",
     "session_description": "Spring MVC architecture, DispatcherServlet, controllers and JSP views.",
     "topics": ["Introduction to Spring MVC architecture and DispatcherServlet","Configuring Spring MVC application context and controller mappings","Creating Controller classes to handle user requests","Integrating Spring MVC with JSP for view rendering"]},

    {"day": 14, "session_title": "Day 14 - React: Getting Started",
     "session_description": "React ecosystem, environment setup, JSX syntax and components.",
     "topics": ["Introduction to React and its ecosystem","Setting up development environment (Node.js, npm)","Creating your first React application","Understanding JSX syntax","Creating functional and class components","Props and state in React components"]},

    {"day": 15, "session_title": "Day 15 - React: Events, State Management & Lists",
     "session_description": "Event handling, useState/setState, lifecycle methods, lists, keys and conditional rendering.",
     "topics": ["Event handling in React","Managing state with useState and setState","React component lifecycle methods","Rendering lists with map()","Using keys for efficient list rendering","Conditional rendering in React"]},

    {"day": 16, "session_title": "Day 16 - React: Forms, Hooks & Context API",
     "session_description": "React forms, controlled components, hooks and Context API.",
     "topics": ["Handling form inputs in React","Controlled vs. uncontrolled components","Form validation in React","Introduction to React hooks","Working with useState, useEffect, and custom hooks","Using Context API for global state management"]},

    {"day": 17, "session_title": "Day 17 - React: Routing & Redux",
     "session_description": "React Router, nested routes, Redux state management.",
     "topics": ["Setting up routing in React applications","Creating routes and nested routes","Navigation and route parameters","State management with Redux","Actions, reducers, and the Redux store","Integrating Redux with React applications"]},

    {"day": 18, "session_title": "Day 18 - React: Styling & API Data Fetching",
     "session_description": "CSS Modules, styled-components, responsive design and HTTP requests.",
     "topics": ["CSS modules and scoped styles","CSS-in-JS libraries like styled-components","Responsive design and media queries","Making HTTP requests in React","Using useEffect for data fetching","Handling loading and error states"]},

    {"day": 19, "session_title": "Day 19 - Node.js Primer & npm",
     "session_description": "Node.js fundamentals, core modules, require/module.exports and npm.",
     "topics": ["Introduction to Node.js","Why Node.js? Asynchronous and Non-Blocking I/O","Setting up the Development Environment","Understanding Node.js Core Modules","Understanding require, module.exports","fs, path, os, http, url modules","What is npm?","Understanding package.json","Installing and Uninstalling Packages"]},

    {"day": 20, "session_title": "Day 20 - Node.js: Routing, Error Handling & Deployment",
     "session_description": "Routing in Node.js, error handling, debugging and deployment.",
     "topics": ["Understanding routing","Request-response cycle and URL parsing","Using the http module for basic routing","Parsing URLs and query strings","Handling different HTTP request methods","Creating route handlers","Routing and Error Handling","Debugging and Performance Optimization","Deployment"]},

    {"day": 21, "session_title": "Day 21 - Advanced JavaScript (ES6+)",
     "session_description": "Modern JavaScript: arrow functions, destructuring, promises, async/await, modules.",
     "topics": ["Arrow Functions","Destructuring Assignment","Spread and Rest Operators","Template Literals","Promises and Async/Await","ES6 Modules (import/export)","ES6 Classes","Map, Set, WeakMap, WeakSet","Iterators and Generators","Error Handling in Async Code"]},

    {"day": 22, "session_title": "Day 22 - Hibernate with JPA: Introduction & Entities",
     "session_description": "Data persistence overview, ORM tools, JPA specifications and Entity classes.",
     "topics": ["Introduction and overview of data persistence","Overview of ORM tools","Understanding JPA","JPA Specifications","Requirements for Entity Classes","Persistent Fields and Properties","Using Collections in Entity Fields","Validating Persistent Fields","Primary Keys in Entities"]},

    {"day": 23, "session_title": "Day 23 - Hibernate with JPA: Managing Entities & Querying",
     "session_description": "EntityManager interface, entity lifecycle, JPQL and Criteria API.",
     "topics": ["The EntityManager Interface","Container-Managed Entity Managers","Application-Managed Entity Managers","Finding Entities Using the EntityManager","Managing an Entity Instance Lifecycle","Persisting, Removing and Synchronizing Entity Instances","Persistence Units","Java Persistence Query Language (JPQL)","Criteria API"]},

    {"day": 24, "session_title": "Day 24 - Hibernate with JPA: Entity Relationships",
     "session_description": "Bidirectional/unidirectional relationships, cascade operations.",
     "topics": ["Direction in Entity Relationships","Bidirectional Relationships","Unidirectional Relationships","Queries and Relationship Direction","Cascade Operations and Relationships","@OneToOne, @OneToMany, @ManyToOne, @ManyToMany","Fetch Types: LAZY vs EAGER","Orphan Removal","Best Practices for JPA Relationships"]},

    {"day": 25, "session_title": "Day 25 - SQL: Introduction & Basic Commands",
     "session_description": "Relational Model, basic SQL syntax, SELECT, INSERT, UPDATE, DELETE.",
     "topics": ["The Relational Model","Understanding Basic SQL Syntax","Basic SQL Commands: SELECT","Basic SQL Commands: INSERT","Basic SQL Commands: UPDATE","Basic SQL Commands: DELETE","The SELECT List and Wildcard (*)","The FROM Clause","How to Constrain the Result Set","DISTINCT and NOT DISTINCT"]},

    {"day": 26, "session_title": "Day 26 - SQL: Filtering, Ordering & Grouping",
     "session_description": "WHERE clause, ORDER BY, GROUP BY, HAVING and set functions.",
     "topics": ["WHERE Clause","Boolean Operators: AND, OR","Other Boolean Operators: BETWEEN, LIKE, IN, IS","ORDER BY","Set Functions (COUNT, SUM, AVG, MIN, MAX)","Set Function and Qualifiers","GROUP BY","HAVING clause"]},

    {"day": 27, "session_title": "Day 27 - SQL: JOINs & DDL",
     "session_description": "All JOIN types (CROSS, INNER, OUTER, SELF) and DDL commands.",
     "topics": ["CROSS JOIN","INNER JOIN","LEFT OUTER JOIN","RIGHT OUTER JOIN","FULL OUTER JOIN","SELF JOIN","CREATE DATABASE","CREATE TABLE","NULL Values and PRIMARY KEY","CONSTRAINT, ALTER TABLE, DROP TABLE"]},

    {"day": 28, "session_title": "Day 28 - PL/SQL Basics",
     "session_description": "PL/SQL block structure, variables, conditional control structures.",
     "topics": ["What is PL/SQL?","Benefits and applications of PL/SQL","PL/SQL architecture and components","Anatomy of a PL/SQL block","Declaration section: variables and data types","Execution section: executable statements","IF-THEN-ELSE statement","CASE statement for multiple conditions","Handling NULL values with NULLIF and COALESCE"]},

    {"day": 29, "session_title": "Day 29 - Full Stack Integration Lab",
     "session_description": "Hands-on: React frontend + Spring Boot REST API + MySQL/Hibernate.",
     "topics": ["Project Architecture: Frontend + Backend + Database","Setting up Spring Boot REST API","Configuring Hibernate/JPA with MySQL","Creating Entity classes and Repositories","Building RESTful endpoints","Connecting React frontend to Spring Boot API","Axios/Fetch for API calls from React","CORS configuration in Spring Boot","End-to-end CRUD operations","Deployment on Tomcat"]},

    {"day": 30, "session_title": "Day 30 - Capstone Project & Assessment",
     "session_description": "Final capstone project, code review, assessment, interview prep.",
     "topics": ["Capstone Project Presentation","Code Review and Best Practices","End-to-End System Walkthrough","Interview Preparation: Java Full Stack","Common Interview Questions: Core Java","Common Interview Questions: Spring Boot & Hibernate","Common Interview Questions: React","Career Guidance and Next Steps","Certification and Course Completion"]},
]

STATE_FILE = SCRIPT_DIR / "prod_state.json"


# ── state helpers ─────────────────────────────────────────────────────────────
def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


# ── PHASE A ───────────────────────────────────────────────────────────────────
def phase_a(state):
    print("\n" + "="*60)
    print("PHASE A -- Creating course in rd_courses (PROD)")
    print("="*60)

    conn   = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT course_id FROM rd_courses
        WHERE course_name = %s AND course_category_id = %s LIMIT 1
    """, (COURSE["course_name"], COURSE["course_category_id"]))
    row = cursor.fetchone()

    if row:
        course_id = row[0]
        print(f"Course already exists --> course_id={course_id}")
    else:
        cursor.execute("""
            INSERT INTO rd_courses
            (course_name, course_category_id, category, course_level, tier_level, is_active)
            VALUES (%s, %s, %s, %s, %s, 1)
        """, (
            COURSE["course_name"], COURSE["course_category_id"],
            COURSE["subject"], COURSE["board"], COURSE["tier_level"]
        ))
        conn.commit()
        course_id = cursor.lastrowid
        print(f"Course inserted --> course_id={course_id}")

    cursor.close()
    conn.close()

    state["course_id"] = course_id
    save_state(state)
    print(f"Phase A complete -- course_id={course_id}")
    return course_id


# ── PHASE B ───────────────────────────────────────────────────────────────────
def phase_b(state):
    print("\n" + "="*60)
    print("PHASE B -- Creating 30 sessions in rd_course_sessions (PROD)")
    print("="*60)

    course_id = state["course_id"]
    conn      = get_connection()
    cursor    = conn.cursor()

    sessions_out = []

    for idx, sess in enumerate(SESSIONS, start=1):
        title = sess["session_title"]

        cursor.execute("""
            SELECT course_session_id, session_uuid
            FROM rd_course_sessions
            WHERE course_id = %s AND session_title = %s LIMIT 1
        """, (course_id, title))
        row = cursor.fetchone()

        if row:
            session_id, session_uuid = row
            print(f"  [{idx:02d}] EXISTS: '{title}' --> id={session_id}")
        else:
            session_uuid = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO rd_course_sessions
                (course_id, session_title, session_uuid, session_type, tier_level, tier_order, version)
                VALUES (%s, %s, %s, 'session', 'BEGINNER', %s, 1)
            """, (course_id, title, session_uuid, idx))
            conn.commit()
            session_id = cursor.lastrowid
            print(f"  [{idx:02d}] INSERTED: '{title}' --> id={session_id}")

        sessions_out.append({**sess, "course_session_id": session_id, "session_uuid": session_uuid})

    cursor.close()
    conn.close()

    state["sessions"] = sessions_out
    save_state(state)
    print(f"Phase B complete -- {len(sessions_out)} sessions ready")
    return sessions_out


# ── PHASE C ───────────────────────────────────────────────────────────────────
def phase_c(state):
    print("\n" + "="*60)
    print("PHASE C -- Creating workspace folder structure (PROD)")
    print("="*60)

    course_id = state["course_id"]
    base      = WORKSPACE_BASE / str(course_id) / "chapters"

    asset_dirs = [
        "assets/flashcards", "assets/quizzes",
        "assets/matchinggame", "assets/matchingpair",
        "assets/lab_manuals",  "assets/exam_papers",
        "assets/notes",
    ]

    for sess in state["sessions"]:
        chapter_dir = base / sess["session_uuid"]
        for d in asset_dirs:
            (chapter_dir / d).mkdir(parents=True, exist_ok=True)
        print(f"  [Day {sess['day']:02d}] Workspace ready: {chapter_dir}")

    print(f"Phase C complete -- workspace at: {base}")


# ── asset generators ──────────────────────────────────────────────────────────
def _gen_flashcards(sess, out_dir):
    topics = sess["topics"]
    cards  = []
    cid    = 1
    for t in topics[:8]:
        cards.append({"card_id": f"CON_{cid:03d}", "front": {"type": "text", "content": f"What is {t}?"}, "back": {"type": "text", "content": f"[Explanation: {t}]"}, "tier_level": "beginner", "order": cid}); cid += 1
    for t in topics[:5]:
        cards.append({"card_id": f"DEF_{cid:03d}", "front": {"type": "text", "content": f"Define: {t}"}, "back": {"type": "text", "content": f"[Definition: {t}]"}, "tier_level": "beginner", "order": cid}); cid += 1
    for t in topics[:4]:
        cards.append({"card_id": f"CODE_{cid:03d}", "front": {"type": "text", "content": f"Code example for: {t}"}, "back": {"type": "code", "language": "java", "content": f"// {t}\n// [Code example]"}, "tier_level": "beginner", "order": cid}); cid += 1
    for t in topics[:3]:
        cards.append({"card_id": f"BP_{cid:03d}", "front": {"type": "text", "content": f"Best practices for: {t}"}, "back": {"type": "text", "content": f"[Best practices: {t}]"}, "tier_level": "beginner", "order": cid}); cid += 1

    data = {"meta": {"asset_type": "flashcard", "category": "concept", "tier": "beginner", "set_number": 1, "chapter_id": sess["session_uuid"], "chapter_title": sess["session_title"], "version": 1}, "cards": cards}
    f = out_dir / "fc_concept_beginner_01.json"
    f.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"      Flashcards --> {f.name} ({len(cards)} cards)")
    return f


def _gen_quiz(sess, out_dir):
    topics = sess["topics"]
    qs = []
    for t in topics:
        qs.append({"question_text": f"Which BEST describes '{t}'?", "difficulty_level": "medium", "max_marks": 1,
                   "options": [{"option_text": f"Correct answer about {t}", "is_correct": True},
                                {"option_text": f"Distractor 1 for {t}", "is_correct": False},
                                {"option_text": f"Distractor 2 for {t}", "is_correct": False},
                                {"option_text": f"Distractor 3 for {t}", "is_correct": False}]})
        qs.append({"question_text": f"What is the primary purpose of {t}?", "difficulty_level": "easy", "max_marks": 1,
                   "options": [{"option_text": f"Primary purpose of {t}", "is_correct": True},
                                {"option_text": "Wrong purpose 1", "is_correct": False},
                                {"option_text": "Wrong purpose 2", "is_correct": False},
                                {"option_text": "Wrong purpose 3", "is_correct": False}]})
    data = {"type": "premium_mcq", "title": f"{sess['session_title']} - Quiz Set 1", "difficulty": "Mixed", "chapter_id": sess["session_uuid"], "questions": qs[:20]}
    f = out_dir / "premium_quiz_set_01.json"
    f.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"      Quiz --> {f.name} ({len(data['questions'])} questions)")
    return f


def _gen_matching_game(sess, out_dir):
    topics = sess["topics"]
    items  = [{"itemName": t, "matchingText": f"[Description: {t}]"} for t in topics[:8]]
    data   = {"type": "matchinggame", "category": "definition", "title": f"{sess['session_title']} - Matching Game", "difficulty": "Medium", "chapter_id": sess["session_uuid"], "items": items}
    f = out_dir / "mg_definition_01.json"
    f.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"      Matching Game --> {f.name} ({len(items)} items)")
    return f


def _gen_matching_pair(sess, out_dir):
    topics = sess["topics"]
    pairs  = [{"left": t, "right": f"[Match: {t}]"} for t in topics[:8]]
    data   = {"type": "matchingpair", "category": "definition", "title": f"{sess['session_title']} - Matching Pairs", "difficulty": "Beginner", "chapter_id": sess["session_uuid"], "pairs": pairs}
    f = out_dir / "mp_definition_01.json"
    f.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"      Matching Pair --> {f.name} ({len(pairs)} pairs)")
    return f


def _gen_lab_manual(sess, out_dir):
    topics = sess["topics"]
    day    = sess["day"]
    exercises = []
    for i, t in enumerate(topics[:6], 1):
        exercises.append({"exercise_number": i, "title": f"Lab {i}: Hands-on with {t}", "objective": f"Understand and implement {t}.", "estimated_time": "20-30 minutes", "difficulty": "beginner",
                          "steps": [f"Step 1: Set up environment for {t}", f"Step 2: Write code implementing {t}", "Step 3: Test your implementation", "Step 4: Discuss output with trainer"],
                          "expected_output": f"[Expected output for {t}]", "challenge": f"Extension: Modify {t} to handle edge cases."})
    data = {"type": "lab_manual", "title": f"Day {day} Lab Manual - {sess['session_title']}", "session": f"Day {day}", "chapter_id": sess["session_uuid"], "duration": "4 hours",
            "tools_required": ["JDK 21", "Eclipse IDE", "MySQL Workbench", "VS Code", "Node.js", "Git", "Maven"], "exercises": exercises}
    f = out_dir / f"lab_day_{day:02d}.json"
    f.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"      Lab Manual --> {f.name} ({len(exercises)} exercises)")
    return f


def _gen_exam_paper(sess, out_dir):
    topics = sess["topics"]
    day    = sess["day"]
    sections = [
        {"section_name": "Section A - MCQ", "section_type": "mcq", "total_marks": 5, "instructions": "Each question carries 1 mark.",
         "questions": [{"question_number": i+1, "question_text": f"Which correctly describes {t}?", "marks": 1, "options": [f"Correct: {t}", "Wrong 1", "Wrong 2", "Wrong 3"], "correct_option": 1} for i, t in enumerate(topics[:5])]},
        {"section_name": "Section B - Short Answer", "section_type": "short_answer", "total_marks": 12, "instructions": "Answer any 4. Each carries 3 marks.",
         "questions": [{"question_number": i+1, "question_text": f"Explain {t} with an example.", "marks": 3} for i, t in enumerate(topics[:4])]},
        {"section_name": "Section C - Coding", "section_type": "coding", "total_marks": 16, "instructions": "Answer any 2. Each carries 8 marks.",
         "questions": [{"question_number": i+1, "question_text": f"Write a Java program demonstrating {t}.", "marks": 8} for i, t in enumerate(topics[:3])]},
    ]
    data = {"type": "exam_paper", "title": f"Day {day} Assessment - {sess['session_title']}", "session": f"Day {day}", "chapter_id": sess["session_uuid"],
            "duration_minutes": 60, "total_marks": 33, "exam_type": "Session Assessment",
            "instructions": ["Read all questions carefully.", "Attempt all sections.", "Show your code clearly.", "No mobile phones allowed."],
            "sections": sections}
    f = out_dir / f"exam_day_{day:02d}.json"
    f.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"      Exam Paper --> {f.name}")
    return f


def _gen_notes(sess, out_dir):
    topics = sess["topics"]
    day    = sess["day"]
    topic_notes = [{"topic": t, "summary": f"[Summary: {t}]", "key_points": [f"Key point 1: {t}", f"Key point 2: {t}", f"Key point 3: {t}"],
                    "code_example": {"language": "java", "description": f"Example for {t}", "code": f"// {t}\n// [Code example]"},
                    "common_mistakes": [f"Common mistake 1: {t}", f"Common mistake 2: {t}"]} for t in topics]
    data = {"type": "session_notes", "title": f"Day {day} Notes - {sess['session_title']}", "session": f"Day {day}", "chapter_id": sess["session_uuid"],
            "description": sess.get("session_description", ""),
            "learning_objectives": [f"Understand {topics[0]}" if topics else "", f"Implement {topics[1]}" if len(topics) > 1 else "", f"Apply best practices for {topics[2]}" if len(topics) > 2 else ""],
            "topics": topic_notes,
            "home_assignment": {"title": f"Day {day} Home Assignment", "description": f"Practice: {', '.join(topics[:3])}",
                                "tasks": [f"Task 1: Implement {topics[0]}" if topics else "", f"Task 2: Write unit tests for {topics[1]}" if len(topics) > 1 else ""]},
            "references": ["https://docs.oracle.com/en/java/", "https://spring.io/docs", "https://react.dev/docs"]}
    f = out_dir / f"notes_day_{day:02d}.json"
    f.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"      Notes --> {f.name} ({len(topics)} topics)")
    return f


# ── PHASE D ───────────────────────────────────────────────────────────────────
def phase_d(state):
    print("\n" + "="*60)
    print("PHASE D -- Generating all assets per session (PROD)")
    print("="*60)

    course_id = state["course_id"]
    base      = WORKSPACE_BASE / str(course_id) / "chapters"
    total     = 0

    for sess in state["sessions"]:
        chapter_dir = base / sess["session_uuid"]
        day = sess["day"]
        print(f"\n  Day {day:02d}: {sess['session_title']}")

        _gen_flashcards(   sess, chapter_dir / "assets/flashcards")
        _gen_quiz(         sess, chapter_dir / "assets/quizzes")
        _gen_matching_game(sess, chapter_dir / "assets/matchinggame")
        _gen_matching_pair(sess, chapter_dir / "assets/matchingpair")
        _gen_lab_manual(   sess, chapter_dir / "assets/lab_manuals")
        _gen_exam_paper(   sess, chapter_dir / "assets/exam_papers")
        _gen_notes(        sess, chapter_dir / "assets/notes")
        total += 7

    print(f"\nPhase D complete -- {total} assets generated")


# ── PHASE E ───────────────────────────────────────────────────────────────────
def phase_e(state):
    print("\n" + "="*60)
    print("PHASE E -- Registering assets in rd_course_session_details (PROD)")
    print("="*60)

    course_id = state["course_id"]
    base      = WORKSPACE_BASE / str(course_id) / "chapters"
    conn      = get_connection()
    cursor    = conn.cursor()
    inserted  = 0
    skipped   = 0

    for sess in state["sessions"]:
        chapter_dir = base / sess["session_uuid"]
        session_id  = sess["course_session_id"]
        day         = sess["day"]

        assets = [
            ("flashcard",    "fc_concept_beginner_01",     chapter_dir / "assets/flashcards/fc_concept_beginner_01.json"),
            ("quiz",         "premium_quiz_set_01",         chapter_dir / "assets/quizzes/premium_quiz_set_01.json"),
            ("matchinggame", "mg_definition_01",            chapter_dir / "assets/matchinggame/mg_definition_01.json"),
            ("matchingpair", "mp_definition_01",            chapter_dir / "assets/matchingpair/mp_definition_01.json"),
            ("lab_manual",   f"lab_day_{day:02d}",         chapter_dir / f"assets/lab_manuals/lab_day_{day:02d}.json"),
            ("exam_paper",   f"exam_day_{day:02d}",        chapter_dir / f"assets/exam_papers/exam_day_{day:02d}.json"),
            ("notes",        f"notes_day_{day:02d}",       chapter_dir / f"assets/notes/notes_day_{day:02d}.json"),
        ]

        for asset_type, topic, file_path in assets:
            cursor.execute("""
                SELECT course_session_detail_id FROM rd_course_session_details
                WHERE course_session_id = %s AND type = %s AND topic = %s LIMIT 1
            """, (session_id, asset_type, topic))

            if cursor.fetchone():
                skipped += 1
                continue

            cursor.execute("""
                INSERT INTO rd_course_session_details
                (course_id, course_session_id, topic, type, file, version, tier_level)
                VALUES (%s, %s, %s, %s, %s, 1, 'BEGINNER')
            """, (course_id, session_id, topic, asset_type, str(file_path)))
            inserted += 1

        conn.commit()
        print(f"  Day {day:02d}: 7 asset rows registered (session_id={session_id})")

    cursor.close()
    conn.close()
    print(f"\nPhase E complete -- inserted={inserted}, skipped={skipped}")


# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", default="ALL", choices=["A","B","C","D","E","ALL"])
    args = parser.parse_args()

    state = load_state()
    phase = args.phase.upper()

    print(f"\nJava Full Stack - Prod Bootstrap")
    print(f"Phase: {phase}")

    if phase in ("A", "ALL"):
        phase_a(state)
        state = load_state()

    if phase in ("B", "ALL"):
        if "course_id" not in state:
            print("ERROR: Run Phase A first"); sys.exit(1)
        phase_b(state)
        state = load_state()

    if phase in ("C", "ALL"):
        if "course_id" not in state:
            print("ERROR: Run Phase A first"); sys.exit(1)
        phase_c(state)

    if phase in ("D", "ALL"):
        if not state.get("sessions"):
            print("ERROR: Run Phase B first"); sys.exit(1)
        phase_d(state)

    if phase in ("E", "ALL"):
        if not state.get("sessions"):
            print("ERROR: Run Phase B first"); sys.exit(1)
        phase_e(state)

    state = load_state()
    print(f"\n=== PROD Bootstrap Complete ===")
    print(f"  Course ID : {state.get('course_id', 'N/A')}")
    print(f"  Sessions  : {len(state.get('sessions', []))}")
    print(f"  Website   : https://robodynamics.in")


if __name__ == "__main__":
    main()
