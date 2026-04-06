"""
update_sessions_prod.py
========================
Updates rd_course_sessions in prod based on the Revised Training Plan.
Updates session_title, session_description (module + assignment), and tier_order.

Run on PROD VPS:
  /opt/robodynamics/venv/bin/python3 update_sessions_prod.py
"""

import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, "/opt/robodynamics/cms-engine/db_bootstrap")
from db_conn import get_connection

COURSE_ID = 162

# Revised sessions from the training plan
REVISED_SESSIONS = [
    {
        "day": 1, "date": "23-Feb-2026", "phase": "Phase 1: Core Java",
        "session_title": "Day 1 - Introduction to Java & Language Fundamentals",
        "session_description": "Introduction to Java, JVM, JDK, JRE. Primitive Data Types & Operators. Flow Control (if/else, switch, loops). Arrays (1D, varargs, Arrays class). Home: Write a Java program using all primitive types, loops, and conditionals. Push to GitHub.",
        "topics": ["Introduction to Java, JVM, JDK, JRE", "Primitive Data Types & Operators", "Flow Control: if/else, switch, loops", "Arrays: 1D, varargs, Arrays class", "Java Coding Best Practices"]
    },
    {
        "day": 2, "date": "24-Feb-2026", "phase": "Phase 1: Core Java",
        "session_title": "Day 2 - OOP: Classes, Inheritance & Polymorphism",
        "session_description": "Classes, Objects, Constructors, this reference. Access Specifiers, static keyword. Wrapper Classes, Type Casting, String Handling. Inheritance, super keyword. Method Overloading and Overriding. Abstract Classes and Interfaces. Runtime Polymorphism. Home: Build a mini OOP model (e.g., Shape hierarchy). Commit & push to Git.",
        "topics": ["Classes, Objects, Constructors, this reference", "Access Specifiers, static keyword", "Wrapper Classes, Type Casting, String Handling", "Inheritance, super keyword, final", "Method Overloading and Overriding", "Abstract Classes and Interfaces", "Runtime Polymorphism"]
    },
    {
        "day": 3, "date": "25-Feb-2026", "phase": "Phase 1: Core Java",
        "session_title": "Day 3 - Exception Handling, Collections & Generics",
        "session_description": "Exception Types, Hierarchy, try-catch-finally. try-with-resources, multi-catch, throw/throws. User-defined Exceptions. Collections Framework: List, Set, Map. Comparable and Comparator. Generics with Collections. Home: Implement a student grade manager using Collections. Handle exceptions gracefully.",
        "topics": ["Exception Types, Hierarchy, try-catch-finally", "try-with-resources, multi-catch, throw/throws", "User-defined Exceptions", "Collections Framework: List, Set, Map", "Iterators, forEach, Comparable, Comparator", "Generics with Collections"]
    },
    {
        "day": 4, "date": "26-Feb-2026", "phase": "Phase 1: Developer Tooling",
        "session_title": "Day 4 - Git & GitHub: Version Control for Professional Developers",
        "session_description": "What is VCS? Why Git? Git Installation & Configuration. Local Repo: init, add, commit, log, diff. Branching: branch, merge, rebase. Remote: clone, push, pull, fetch. GitHub: PRs, code review, GitHub Flow. Conflict resolution. Home: Collaborate on a shared GitHub repo, raise a PR, review a peer's code.",
        "topics": ["What is VCS? Why Git?", "Git Installation & Configuration", "Local Repo: init, add, commit, log, diff", "Branching: branch, merge, rebase", "Remote: clone, push, pull, fetch", "GitHub: PRs, code review, GitHub Flow", "Conflict resolution strategies"]
    },
    {
        "day": 5, "date": "27-Feb-2026", "phase": "Phase 1: Developer Tooling",
        "session_title": "Day 5 - JUnit 5: Test-Driven Development",
        "session_description": "Why Testing? Introduction to TDD. JUnit 5 Setup & Annotations (@Test, @BeforeEach, etc.). Writing unit tests and assertions. Parameterized Tests. Mocking with Mockito: mock, when, verify. Test coverage metrics. Home: Write unit tests for your Collections exercise (Day-3). Achieve 80% or higher coverage.",
        "topics": ["Why Testing? Introduction to TDD", "JUnit 5 Setup & Annotations", "Writing unit tests and assertions", "Parameterized Tests", "Mocking with Mockito: mock, when, verify", "Test coverage metrics"]
    },
    {
        "day": 6, "date": "02-Mar-2026", "phase": "Phase 2: SQL",
        "session_title": "Day 6 - Relational Model & Core SQL",
        "session_description": "The Relational Model & RDBMS concepts. SQL Basics: SELECT, INSERT, UPDATE, DELETE. WHERE clause, ORDER BY, GROUP BY, HAVING. Set functions: COUNT, SUM, AVG, MIN, MAX. DISTINCT, NULL handling. Home: Create a MySQL database for a bookstore. Write SELECT queries with filters, groupings, and aggregations.",
        "topics": ["The Relational Model & RDBMS concepts", "SQL Basics: SELECT, INSERT, UPDATE, DELETE", "WHERE clause, ORDER BY, GROUP BY, HAVING", "Set functions: COUNT, SUM, AVG, MIN, MAX", "DISTINCT, NULL handling"]
    },
    {
        "day": 7, "date": "03-Mar-2026", "phase": "Phase 2: SQL",
        "session_title": "Day 7 - Advanced SQL: JOINs, DDL & Constraints",
        "session_description": "CROSS, INNER, LEFT, RIGHT, FULL OUTER JOINs. SELF JOIN. CREATE DATABASE/TABLE, ALTER TABLE, DROP TABLE. PRIMARY KEY, FOREIGN KEY, UNIQUE, NOT NULL, CHECK constraints. Home: Add relationships to bookstore DB (Authors, Books, Orders). Write JOIN queries.",
        "topics": ["CROSS, INNER, LEFT, RIGHT, FULL OUTER JOINs", "SELF JOIN", "CREATE DATABASE/TABLE, ALTER TABLE, DROP TABLE", "PRIMARY KEY, FOREIGN KEY, UNIQUE constraints", "NOT NULL, CHECK, DEFAULT constraints"]
    },
    {
        "day": 8, "date": "04-Mar-2026", "phase": "Phase 2: SQL",
        "session_title": "Day 8 - Advanced Querying & Performance Basics",
        "session_description": "Window Functions: ROW_NUMBER, RANK, LEAD, LAG. Advanced Filtering: EXISTS, NOT EXISTS. Views & Stored Procedures. Transactions: COMMIT, ROLLBACK, SAVEPOINT. Indexes and query performance basics. Home: Write a stored procedure for bookstore order processing. Use transactions.",
        "topics": ["Window Functions: ROW_NUMBER, RANK, LEAD, LAG", "Advanced Filtering: EXISTS, NOT EXISTS", "Views & Stored Procedures", "Transactions: COMMIT, ROLLBACK, SAVEPOINT", "Indexes and query performance basics"]
    },
    {
        "day": 9, "date": "05-Mar-2026", "phase": "Phase 2: PL/SQL",
        "session_title": "Day 9 - PL/SQL Fundamentals",
        "session_description": "What is PL/SQL? Architecture & Benefits. PL/SQL Block Structure: Declaration, Execution, Exception. Variables, Data Types, Constants. IF-THEN-ELSE, CASE statements. Loops: FOR, WHILE, basic loops. Cursors, exception handling in PL/SQL. Home: Write PL/SQL blocks to compute student grade summaries with error handling.",
        "topics": ["What is PL/SQL? Architecture & Benefits", "PL/SQL Block Structure", "Variables, Data Types, Constants", "IF-THEN-ELSE, CASE statements", "Loops: FOR, WHILE, basic loops", "Cursors and exception handling"]
    },
    {
        "day": 10, "date": "06-Mar-2026", "phase": "Phase 3: Hibernate / JPA",
        "session_title": "Day 10 - ORM Concepts & JPA Introduction",
        "session_description": "Data Persistence & ORM overview. JPA Specification & Hibernate as implementation. Entity Classes, @Entity, @Id, @Column. Persistent Fields and Properties. Using Collections in Entities. Primary Keys in Entities (generated values). Home: Map a 'Product' entity to a MySQL table using JPA. Persist and retrieve data.",
        "topics": ["Data Persistence & ORM overview", "JPA Specification & Hibernate as implementation", "Entity Classes: @Entity, @Id, @Column", "Persistent Fields and Properties", "Using Collections in Entities", "Primary Key strategies"]
    },
    {
        "day": 11, "date": "09-Mar-2026", "phase": "Phase 3: Hibernate / JPA",
        "session_title": "Day 11 - JPA: Entity Lifecycle, Relationships & Querying",
        "session_description": "EntityManager Interface & Lifecycle. Persisting, Finding, Removing, Merging entities. Synchronization with database (flush). Entity Relationships: @OneToOne, @OneToMany, @ManyToOne, @ManyToMany. Fetch Types: LAZY vs EAGER. JPQL and Criteria API. Home: Model an e-commerce schema (User, Product, Order, OrderItem) with JPA relationships.",
        "topics": ["EntityManager Interface & Lifecycle", "Persisting, Finding, Removing, Merging entities", "Entity Relationships: @OneToOne, @OneToMany, @ManyToMany", "Fetch Types: LAZY vs EAGER", "Cascade Operations, Orphan Removal", "JPQL and Criteria API"]
    },
    {
        "day": 12, "date": "10-Mar-2026", "phase": "Phase 3: Spring Framework",
        "session_title": "Day 12 - Spring Core: DI, IoC & Spring MVC",
        "session_description": "Spring Framework overview & ecosystem. Dependency Injection (DI) & Inversion of Control (IoC). Spring Beans: XML and annotation configuration (@Component, @Autowired). Bean scopes and lifecycle. Spring MVC: DispatcherServlet, @Controller, @RequestMapping. Home: Create a simple Spring MVC app that handles a form submission.",
        "topics": ["Spring Framework overview & ecosystem", "Dependency Injection & Inversion of Control", "Spring Beans: @Component, @Autowired, @Configuration", "Bean scopes and lifecycle", "Spring MVC: DispatcherServlet, @Controller, @RequestMapping"]
    },
    {
        "day": 13, "date": "11-Mar-2026", "phase": "Phase 3: Spring Boot",
        "session_title": "Day 13 - Spring Boot: Getting Started & Auto-Configuration",
        "session_description": "Why Spring Boot? Convention over Configuration. Spring Initializr, Starters, CLI. @SpringBootApplication, component scanning. application.properties, profiles (dev/prod). Embedded servers (Tomcat). Logging configuration. Home: Bootstrap a Spring Boot project. Configure profiles for dev and prod. Run with embedded server.",
        "topics": ["Why Spring Boot? Convention over Configuration", "Spring Initializr, Starters, CLI", "@SpringBootApplication and component scanning", "application.properties, profiles (dev/prod)", "Embedded servers (Tomcat)", "Logging configuration"]
    },
    {
        "day": 14, "date": "12-Mar-2026", "phase": "Phase 3: Spring Boot",
        "session_title": "Day 14 - Building RESTful APIs with Spring Boot",
        "session_description": "REST principles: Resources, HTTP Verbs, Status Codes. @RestController, @RequestMapping, @GetMapping, @PostMapping, @PutMapping, @DeleteMapping. @RequestBody, @PathVariable, @RequestParam. ResponseEntity for proper HTTP responses. Exception handling with @ControllerAdvice. Home: Build a complete CRUD REST API for 'Products' with proper error handling and status codes.",
        "topics": ["REST principles: Resources, HTTP Verbs, Status Codes", "@RestController, @GetMapping, @PostMapping, @PutMapping, @DeleteMapping", "@RequestBody, @PathVariable, @RequestParam", "ResponseEntity for proper HTTP responses", "Global exception handling with @ControllerAdvice"]
    },
    {
        "day": 15, "date": "13-Mar-2026", "phase": "Phase 3: Spring Data JPA",
        "session_title": "Day 15 - Spring Data JPA: Repositories & Query Methods",
        "session_description": "Spring Data JPA Overview. JpaRepository, CrudRepository interfaces. Defining Repository Interfaces and query methods. Query Creation from method names. @Query annotation with JPQL. Pagination (Pageable) and Sorting. Home: Integrate Spring Data JPA with your REST API. Add pagination and sorting.",
        "topics": ["Spring Data JPA Overview", "JpaRepository, CrudRepository interfaces", "Query method naming conventions", "@Query annotation with JPQL", "Pagination (Pageable) and Sorting", "Spring Data REST: auto-exposing repositories"]
    },
    {
        "day": 16, "date": "16-Mar-2026", "phase": "Phase 3: Spring Boot",
        "session_title": "Day 16 - Spring Data REST, Validation & API Documentation",
        "session_description": "Spring Data REST: auto-exposing repositories as REST. HAL, HATEOAS concepts. Bean Validation: @Valid, @NotNull, @Size, @Email. Swagger/OpenAPI documentation with springdoc-openapi. Spring Boot Actuator: health, metrics, info endpoints. Home: Add validation to your API. Generate Swagger UI documentation.",
        "topics": ["Spring Data REST: auto-exposing repositories", "HAL, HATEOAS concepts", "Bean Validation: @Valid, @NotNull, @Size, @Email", "Swagger/OpenAPI with springdoc-openapi", "Spring Boot Actuator: health, metrics endpoints"]
    },
    {
        "day": 17, "date": "17-Mar-2026", "phase": "Phase 3: Spring Boot",
        "session_title": "Day 17 - Spring Security: Authentication & JWT Authorization",
        "session_description": "Why Security? Common vulnerabilities (OWASP Top 10 overview). Spring Security architecture. HTTP Basic and Form-based authentication. JWT (JSON Web Token): structure, generation, validation. Securing REST endpoints with JWT. Role-based authorization. Home: Secure your REST API with JWT. Implement login endpoint returning a token.",
        "topics": ["Why Security? OWASP Top 10 overview", "Spring Security architecture", "HTTP Basic and Form-based authentication", "JWT: structure, generation, validation", "Securing REST endpoints with JWT", "Role-based authorization (@PreAuthorize)"]
    },
    {
        "day": 18, "date": "18-Mar-2026", "phase": "Phase 4: JavaScript",
        "session_title": "Day 18 - Modern JavaScript (ES6+) Fundamentals",
        "session_description": "JavaScript in the browser: DOM, events. Variables: var, let, const — scoping differences. Arrow Functions, Destructuring Assignment. Spread/Rest Operators, Template Literals. Promises and Async/Await. ES6 Modules (import/export). Error handling in async code. Home: Build a JavaScript mini-app that fetches data from a public API.",
        "topics": ["JavaScript in the browser: DOM, events", "Variables: var, let, const and scoping", "Arrow Functions, Destructuring, Spread/Rest", "Template Literals, Optional Chaining", "Promises and Async/Await", "ES6 Modules (import/export)"]
    },
    {
        "day": 19, "date": "19-Mar-2026", "phase": "Phase 4: JavaScript",
        "session_title": "Day 19 - Ajax, REST Consumption & Node.js/npm Basics",
        "session_description": "Ajax: XMLHttpRequest vs Fetch vs Axios. RESTful Web Services consumption. HTTP Verbs, Status Codes from client perspective. CORS and how to handle it. Node.js: architecture, core modules (fs, path, http). npm: package.json, installing packages. Home: Use Axios to call your Spring Boot API from a plain HTML/JS page.",
        "topics": ["Ajax: XMLHttpRequest vs Fetch vs Axios", "RESTful Web Services consumption", "CORS and handling it in Spring Boot", "Node.js architecture and core modules", "npm: package.json, installing packages"]
    },
    {
        "day": 20, "date": "20-Mar-2026", "phase": "Phase 4: React.js",
        "session_title": "Day 20 - React Fundamentals: Components, JSX & Props",
        "session_description": "What is React? Virtual DOM, ecosystem. Setting up with Vite (create-react-app alternative). JSX syntax and expressions. Functional and Class Components. Props: passing data, PropTypes. Conditional rendering. Rendering lists with map() and keys. Home: Create a React app that displays a list of products fetched from your Spring Boot API.",
        "topics": ["What is React? Virtual DOM, ecosystem", "Setting up with Vite", "JSX syntax and expressions", "Functional Components and Props", "Conditional rendering, lists with map() and keys"]
    },
    {
        "day": 21, "date": "23-Mar-2026", "phase": "Phase 4: React.js",
        "session_title": "Day 21 - React: State Management with Hooks & Context API",
        "session_description": "useState: local state management. useEffect: side effects, data fetching, cleanup. useRef: DOM references. useContext: consuming context. Custom Hooks. Context API for global state. Lifting state up. Home: Add a shopping cart feature using useState and Context API. Cart state shared across components.",
        "topics": ["useState: local state management", "useEffect: side effects, data fetching, cleanup", "useRef: DOM references", "Custom Hooks", "Context API for global state", "Lifting state up"]
    },
    {
        "day": 22, "date": "24-Mar-2026", "phase": "Phase 4: React.js",
        "session_title": "Day 22 - React: Forms, Validation & React Router",
        "session_description": "Controlled vs Uncontrolled components. Handling form inputs, textarea, select. Form validation (client-side). React Router v6: BrowserRouter, Routes, Route. Navigation: Link, NavLink, useNavigate. Route parameters with useParams. Protected routes. Home: Build Login & Registration forms with validation. Add routing.",
        "topics": ["Controlled vs Uncontrolled form components", "Handling form inputs and validation", "React Router v6: BrowserRouter, Routes, Route", "Navigation: Link, NavLink, useNavigate", "Route parameters with useParams", "Protected routes"]
    },
    {
        "day": 23, "date": "25-Mar-2026", "phase": "Phase 4: React.js",
        "session_title": "Day 23 - Advanced React: Redux Toolkit & API Integration",
        "session_description": "Why Redux? When to use it vs Context. Redux Toolkit: createSlice, configureStore. Actions, Reducers, the Redux Store. RTK Query for data fetching and caching. Async operations with createAsyncThunk. Integrating Redux with React. Home: Integrate Redux Toolkit into your app. Manage auth state. Use RTK Query to fetch products.",
        "topics": ["Why Redux? When to use it vs Context", "Redux Toolkit: createSlice, configureStore", "Actions, Reducers, the Redux Store", "RTK Query for data fetching and caching", "Async operations with createAsyncThunk"]
    },
    {
        "day": 24, "date": "26-Mar-2026", "phase": "Phase 4: React.js",
        "session_title": "Day 24 - React: Styling, UI Libraries & Performance",
        "session_description": "CSS Modules: scoped component styles. Tailwind CSS: utility-first approach. Styled-components: CSS-in-JS. Material UI / Ant Design components. React.memo, useMemo, useCallback for performance. Lazy loading with React.lazy and Suspense. React Testing Library basics. Home: Redesign your app UI using Tailwind CSS. Add lazy loading.",
        "topics": ["CSS Modules: scoped styles", "Tailwind CSS: utility-first approach", "Material UI / Ant Design components", "React.memo, useMemo, useCallback for performance", "Lazy loading with React.lazy and Suspense", "React Testing Library basics"]
    },
    {
        "day": 25, "date": "27-Mar-2026", "phase": "Phase 5: Integration",
        "session_title": "Day 25 - Full-Stack Integration & End-to-End Testing",
        "session_description": "Connecting React frontend to Spring Boot backend in production mode. Environment variables in React (.env files). CORS deep-dive and configuration. Building React for production (npm run build). Serving React static build from Spring Boot. End-to-end integration testing. Home: Run full stack locally. Write at least 3 integration-style tests.",
        "topics": ["Connecting React frontend to Spring Boot backend", "Environment variables in React (.env files)", "CORS deep-dive and configuration", "Building React for production (npm run build)", "Serving React static build from Spring Boot", "End-to-end integration testing"]
    },
    {
        "day": 26, "date": "30-Mar-2026", "phase": "Phase 5: CI/CD",
        "session_title": "Day 26 - Jenkins: CI/CD Pipelines",
        "session_description": "What is CI/CD? Why it matters. Jenkins Installation & Configuration. Creating Jenkins Jobs (Freestyle and Pipeline). Jenkinsfile: declarative pipeline syntax. Integrating Jenkins with GitHub (webhooks). Build, Test, and Deploy stages. Jenkins plugins (Maven, Docker, Slack notifications). Home: Create a Jenkins pipeline for your Spring Boot app.",
        "topics": ["What is CI/CD? Why it matters", "Jenkins Installation & Configuration", "Creating Jenkins Jobs (Freestyle and Pipeline)", "Jenkinsfile: declarative pipeline syntax", "Integrating Jenkins with GitHub (webhooks)", "Build, Test, and Deploy stages"]
    },
    {
        "day": 27, "date": "31-Mar-2026", "phase": "Phase 5: CI/CD",
        "session_title": "Day 27 - Docker: Containerizing Your Applications",
        "session_description": "What is Docker? VMs vs Containers. Docker Architecture: images, containers, registry. Dockerfile: writing and optimizing multi-stage builds. Docker commands: build, run, push, pull. Docker Compose: multi-container applications. Containerizing Spring Boot and React apps. Home: Write Dockerfiles for both apps. Create docker-compose.yml. Run entire stack with one command.",
        "topics": ["What is Docker? VMs vs Containers", "Docker Architecture: images, containers, registry", "Dockerfile: writing and optimizing multi-stage builds", "Docker commands: build, run, push, pull", "Docker Compose: multi-container applications"]
    },
    {
        "day": 28, "date": "01-Apr-2026", "phase": "Phase 5: Deployment",
        "session_title": "Day 28 - Cloud Deployment: AWS / Render / Railway",
        "session_description": "Cloud deployment options overview (AWS EC2, Elastic Beanstalk, Render, Railway). Deploying Spring Boot API to Render/Railway. Deploying React app to Vercel/Netlify. Configuring environment variables in cloud. Custom domains and HTTPS. Monitoring basics: logs, health checks. Home: Deploy your Spring Boot API to Render/Railway. Deploy React app to Vercel/Netlify.",
        "topics": ["Cloud deployment options overview", "Deploying Spring Boot API to Render/Railway", "Deploying React app to Vercel/Netlify", "Configuring environment variables in cloud", "Custom domains and HTTPS", "Monitoring basics: logs, health checks"]
    },
    {
        "day": 29, "date": "02-Apr-2026", "phase": "Phase 5: Capstone",
        "session_title": "Day 29 - Capstone Project Day 1: Design & Backend",
        "session_description": "Capstone project kickoff: build a full-stack app end-to-end. System design: define entities, REST endpoints, database schema. Backend implementation: Spring Boot REST API, Spring Data JPA, Spring Security with JWT. GitHub repository setup with proper branching strategy. Home: Complete the backend — all entities mapped, REST APIs working, tests passing, pushed to GitHub.",
        "topics": ["Capstone project kickoff and system design", "Define entities, REST endpoints, database schema", "Backend implementation: Spring Boot, JPA, Security", "GitHub repository setup with branching strategy", "API testing with Postman"]
    },
    {
        "day": 30, "date": "03-Apr-2026", "phase": "Phase 5: Capstone",
        "session_title": "Day 30 - Capstone Project Day 2: Frontend, Docker & Live Demo",
        "session_description": "React frontend: pages, routing, Redux, API integration. Styling: Tailwind CSS. Dockerize both apps. Deploy to cloud (Render + Vercel). Live demo presentation. Code review and best practices. Interview preparation: Java Full Stack common questions. Certification and Course Completion. Home: GRADUATION — Live demo of your deployed full-stack app. Share your GitHub repo link.",
        "topics": ["React frontend: pages, routing, Redux, API integration", "Styling with Tailwind CSS", "Dockerize both apps", "Deploy to cloud (Render + Vercel)", "Live demo presentation and code review", "Interview prep: Java Full Stack common questions"]
    },
]


def update_sessions():
    conn = get_connection()
    cursor = conn.cursor()

    print(f"\n{'='*60}")
    print(f"Updating rd_course_sessions for course_id={COURSE_ID}")
    print(f"Total sessions to update: {len(REVISED_SESSIONS)}")
    print(f"{'='*60}")

    # Get existing sessions ordered by tier_order
    cursor.execute("""
        SELECT course_session_id, session_title, tier_order
        FROM rd_course_sessions
        WHERE course_id = %s
        ORDER BY tier_order
    """, (COURSE_ID,))
    existing = cursor.fetchall()
    print(f"\nExisting sessions: {len(existing)}")
    for row in existing:
        print(f"  id={row[0]:4d} | order={row[2]:2d} | {row[1][:60]}")

    if len(existing) != len(REVISED_SESSIONS):
        print(f"\nWARNING: {len(existing)} existing sessions vs {len(REVISED_SESSIONS)} in revised plan!")
        print("Proceeding by matching on tier_order (day number)...")

    print(f"\n{'='*60}")
    print("Updating sessions...")
    print(f"{'='*60}")

    updated = 0
    for sess_data, existing_row in zip(REVISED_SESSIONS, existing):
        course_session_id = existing_row[0]
        old_title = existing_row[1]
        new_title = sess_data["session_title"]
        new_description = sess_data["session_description"]
        day = sess_data["day"]

        cursor.execute("""
            UPDATE rd_course_sessions
            SET session_title = %s,
                session_description = %s,
                tier_order = %s
            WHERE course_session_id = %s AND course_id = %s
        """, (new_title, new_description, day, course_session_id, COURSE_ID))

        updated += 1
        print(f"  [{day:02d}] UPDATED id={course_session_id}")
        print(f"       OLD: {old_title[:70]}")
        print(f"       NEW: {new_title[:70]}")

    conn.commit()

    print(f"\n{'='*60}")
    print(f"Done! Updated {updated} sessions in rd_course_sessions")
    print(f"{'='*60}")

    cursor.close()
    conn.close()


if __name__ == "__main__":
    update_sessions()
