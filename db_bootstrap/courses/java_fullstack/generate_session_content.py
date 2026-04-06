"""
generate_session_content.py
============================
Generates AI-powered content for Java Full Stack course sessions using Claude API.

Generates TWO sets per session:
  Set 1 = Academic / conceptual (theory-based)
  Set 2 = Banking / Finance domain-specific (real-world examples)

Asset types per set:
  - flashcards      (fc_*.json)
  - quiz            (quiz_*.json)
  - matching_game   (mg_*.json)
  - matching_pair   (mp_*.json)
  - lab_manual      (lab_*.json)
  - exam_paper      (exam_*.json)
  - notes           (notes_*.json)

Usage:
    python generate_session_content.py --session 1 --api-key sk-ant-...
    python generate_session_content.py --session 1 --api-key sk-ant-... --set 2
    python generate_session_content.py --all --api-key sk-ant-...
"""

import sys
import os
import json
import time
import argparse
from pathlib import Path
import requests

# ─── Configuration ───────────────────────────────────────────────────────────

CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"
CLAUDE_MODEL   = "claude-sonnet-4-6"

# Output directory (local - we'll upload to prod after)
OUTPUT_DIR = Path(__file__).parent / "generated_content"

# ─── Session data (revised training plan) ────────────────────────────────────

SESSIONS = [
    {
        "day": 1,
        "date": "23-Feb-2026",
        "phase": "Phase 1: Java Foundations",
        "session_title": "Day 1 - Introduction to Java & Language Fundamentals",
        "topics": [
            "Introduction to Java: History, Platform Independence, JVM/JDK/JRE architecture",
            "Primitive Data Types: byte, short, int, long, float, double, char, boolean",
            "Operators: arithmetic, relational, logical, bitwise, assignment, ternary",
            "Flow Control: if/else, switch-case, for, while, do-while, break, continue",
            "Arrays: 1D arrays, multi-dimensional arrays, varargs, Arrays class methods",
            "Best Practices: naming conventions, code readability, Java coding standards"
        ],
        "home_assignment": "Write a Java program using all primitive types, loops, and conditionals. Push to GitHub.",
        "session_uuid": "be0aaa5c-9ba5-41d7-a524-9d3f71b97ca7",
        "course_session_id": 2669
    },
    {
        "day": 2,
        "date": "24-Feb-2026",
        "phase": "Phase 1: Java Foundations",
        "session_title": "Day 2 - OOP: Classes, Inheritance & Polymorphism",
        "topics": [
            "Classes and Objects: fields, methods, constructors, this keyword",
            "Access Specifiers: public, private, protected, default",
            "Inheritance: extends, super keyword, method overriding",
            "Polymorphism: runtime polymorphism, method overloading",
            "Abstract Classes and Interfaces: abstract methods, default/static interface methods",
            "Wrapper Classes, String handling, Type casting, final keyword"
        ],
        "home_assignment": "Design a class hierarchy for a banking system (Account, SavingsAccount, CurrentAccount).",
        "session_uuid": None,
        "course_session_id": 2670
    },
    {
        "day": 3,
        "date": "25-Feb-2026",
        "phase": "Phase 1: Java Foundations",
        "session_title": "Day 3 - Exception Handling, Collections & Generics",
        "topics": [
            "Exception Handling: try-catch-finally, try-with-resources, multi-catch",
            "throw vs throws, custom exceptions, exception hierarchy",
            "Collections Framework: List, Set, Map, Queue interfaces",
            "Implementing Classes: ArrayList, LinkedList, HashSet, TreeSet, HashMap, TreeMap",
            "Iterators, forEach, Comparable and Comparator",
            "Generics: type parameters, bounded wildcards, generic methods"
        ],
        "home_assignment": "Implement a bank transaction processor that handles exceptions and uses Collections.",
        "session_uuid": None,
        "course_session_id": 2671
    },
]

# ─── Claude API helper ────────────────────────────────────────────────────────

def call_claude(api_key: str, prompt: str, max_tokens: int = 4096) -> str:
    """Call Claude API and return the text response."""
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    payload = {
        "model": CLAUDE_MODEL,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}]
    }

    resp = requests.post(CLAUDE_API_URL, headers=headers, json=payload, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    return data["content"][0]["text"]


def parse_json_response(text: str) -> dict:
    """Extract JSON from Claude's response (handles code block wrapping)."""
    text = text.strip()
    # Remove markdown code blocks
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()
    return json.loads(text)


# ─── Prompt builders ─────────────────────────────────────────────────────────

def build_flashcard_prompt(session: dict, domain: str) -> str:
    topics_str = "\n".join(f"  - {t}" for t in session["topics"])

    if domain == "academic":
        context = "Focus on core concepts, definitions, syntax, and theoretical understanding."
        example_hint = "Use general programming examples (e.g., Employee, Animal, Shape classes)."
    else:
        context = "Frame every concept in a Banking/Finance domain context."
        example_hint = "Use banking examples: Account, Transaction, Customer, Loan, Balance, Interest Rate, IFSC code, etc."

    return f"""You are an expert Java instructor creating flashcards for a training course.

Session: {session['session_title']}
Date: {session['date']}
Topics covered:
{topics_str}

Domain: {domain.upper()}
{context}
{example_hint}

Generate 20 high-quality flashcards in JSON format. Each card should have:
- A meaningful question on the front (not just "What is X?")
- A complete, accurate answer on the back
- Mix of: concept definitions, code snippets, comparison questions, "why/when" questions
- 5 cards should have code examples on the back

Return ONLY valid JSON in this exact structure:
{{
  "meta": {{
    "asset_type": "flashcard",
    "session_day": {session['day']},
    "session_title": "{session['session_title']}",
    "domain": "{domain}",
    "total_cards": 20
  }},
  "cards": [
    {{
      "card_id": "FC_001",
      "front": {{
        "type": "text",
        "content": "Question here"
      }},
      "back": {{
        "type": "text",
        "content": "Answer here"
      }},
      "category": "concept|definition|code|comparison|best_practice",
      "difficulty": "easy|medium|hard",
      "order": 1
    }}
  ]
}}

For code cards, use "type": "code" and "language": "java" in the back object."""


def build_quiz_prompt(session: dict, domain: str) -> str:
    topics_str = "\n".join(f"  - {t}" for t in session["topics"])

    if domain == "academic":
        context = "Focus on theoretical understanding, syntax rules, and concept verification."
        example_hint = "Use general Java examples."
    else:
        context = "Frame questions around real banking/finance scenarios."
        example_hint = "Questions should involve banking domain: transactions, accounts, loans, interest calculations."

    return f"""You are an expert Java instructor creating a multiple-choice quiz.

Session: {session['session_title']}
Date: {session['date']}
Topics:
{topics_str}

Domain: {domain.upper()}
{context}
{example_hint}

Generate 15 multiple-choice questions. Requirements:
- Mix difficulty: 5 easy, 7 medium, 3 hard
- 4 options each, exactly 1 correct
- Distractors should be plausible (common mistakes, misconceptions)
- Include code-based questions (at least 5 questions with code snippets)
- Cover ALL listed topics

Return ONLY valid JSON:
{{
  "meta": {{
    "asset_type": "quiz",
    "session_day": {session['day']},
    "session_title": "{session['session_title']}",
    "domain": "{domain}",
    "total_questions": 15,
    "total_marks": 20
  }},
  "questions": [
    {{
      "question_id": "Q001",
      "question_text": "Question text here",
      "code_snippet": null,
      "difficulty_level": "easy|medium|hard",
      "marks": 1,
      "options": [
        {{"option_id": "A", "option_text": "Option A", "is_correct": true}},
        {{"option_id": "B", "option_text": "Option B", "is_correct": false}},
        {{"option_id": "C", "option_text": "Option C", "is_correct": false}},
        {{"option_id": "D", "option_text": "Option D", "is_correct": false}}
      ],
      "explanation": "Why the correct answer is correct"
    }}
  ]
}}"""


def build_matching_game_prompt(session: dict, domain: str) -> str:
    topics_str = "\n".join(f"  - {t}" for t in session["topics"])

    if domain == "academic":
        context = "Match Java concepts to their definitions/purposes."
    else:
        context = "Match Java concepts to their banking/finance use cases."

    return f"""You are creating a matching game exercise for a Java training session.

Session: {session['session_title']}
Topics: {', '.join(session['topics'][:6])}

Domain: {domain.upper()}
{context}

Create a matching game with 10 pairs. Each pair: a TERM on the left, its MATCH on the right.
Make the matches challenging but fair. Include 3 code-related pairs.

Return ONLY valid JSON:
{{
  "meta": {{
    "asset_type": "matching_game",
    "session_day": {session['day']},
    "session_title": "{session['session_title']}",
    "domain": "{domain}",
    "total_pairs": 10,
    "instructions": "Drag each term on the left to match with its correct definition on the right."
  }},
  "pairs": [
    {{
      "pair_id": 1,
      "term": {{
        "id": "T1",
        "content": "JVM",
        "type": "text"
      }},
      "match": {{
        "id": "M1",
        "content": "Java Virtual Machine - executes bytecode and provides platform independence",
        "type": "text"
      }}
    }}
  ]
}}"""


def build_matching_pair_prompt(session: dict, domain: str) -> str:
    topics_str = ", ".join(session["topics"][:5])

    if domain == "academic":
        context = "Pair Java code snippets with their output or purpose."
    else:
        context = "Pair Java concepts with banking domain real-world examples."

    return f"""Create a matching pairs exercise for Java training.

Session: {session['session_title']}
Topics: {topics_str}

Domain: {domain.upper()}
{context}

Create 8 matching pairs. Format similar to flashcard pairs - show two related items side by side.
Mix: concept-to-example, code-to-output, term-to-definition.

Return ONLY valid JSON:
{{
  "meta": {{
    "asset_type": "matching_pair",
    "session_day": {session['day']},
    "session_title": "{session['session_title']}",
    "domain": "{domain}",
    "total_pairs": 8,
    "instructions": "Match each item in Column A with its corresponding item in Column B."
  }},
  "pairs": [
    {{
      "pair_id": 1,
      "column_a": {{
        "id": "A1",
        "content": "Item in column A",
        "type": "text|code"
      }},
      "column_b": {{
        "id": "B1",
        "content": "Matching item in column B",
        "type": "text|code"
      }},
      "explanation": "Why these match"
    }}
  ]
}}"""


def build_lab_manual_prompt(session: dict, domain: str) -> str:
    topics_str = "\n".join(f"  {i+1}. {t}" for i, t in enumerate(session["topics"]))

    if domain == "academic":
        scenario = "General programming exercises to solidify conceptual understanding."
        project = "a Student Grade Management System"
    else:
        scenario = "Banking/Finance domain exercises with realistic business scenarios."
        project = "a Bank Account Management System for XYZ Bank"

    return f"""You are creating a lab manual for a Java training session.

Session: {session['session_title']}
Date: {session['date']}
Phase: {session['phase']}
Topics:
{topics_str}
Home Assignment: {session['home_assignment']}

Domain: {domain.upper()}
Scenario: {scenario}
Project: {project}

Create a comprehensive lab manual with 5 exercises. Each exercise should be progressively harder.
Include: objectives, step-by-step instructions, code starters, expected output, and reflection questions.

Return ONLY valid JSON:
{{
  "meta": {{
    "asset_type": "lab_manual",
    "session_day": {session['day']},
    "session_title": "{session['session_title']}",
    "domain": "{domain}",
    "duration_minutes": 120,
    "total_exercises": 5
  }},
  "overview": {{
    "objectives": ["Objective 1", "Objective 2", "Objective 3"],
    "prerequisites": ["Prerequisite 1"],
    "tools": ["JDK 17+", "IntelliJ IDEA / VS Code", "Git"]
  }},
  "exercises": [
    {{
      "exercise_id": "LAB_01",
      "title": "Exercise title",
      "difficulty": "beginner|intermediate|advanced",
      "duration_minutes": 20,
      "objective": "What student will learn",
      "scenario": "Business/learning scenario description",
      "instructions": [
        "Step 1: ...",
        "Step 2: ..."
      ],
      "starter_code": "// Java starter code here\\npublic class Exercise1 {{\\n  // TODO: Complete this\\n}}",
      "expected_output": "Expected console output or behavior",
      "hints": ["Hint 1", "Hint 2"],
      "reflection_questions": ["Question 1?", "Question 2?"]
    }}
  ],
  "submission_instructions": "Push your completed code to GitHub with commit message: 'Day {session['day']} Lab Complete'"
}}"""


def build_exam_paper_prompt(session: dict, domain: str) -> str:
    topics_str = "\n".join(f"  - {t}" for t in session["topics"])

    if domain == "academic":
        context = "Standard technical exam with theoretical and coding questions."
        scenario = "General Java programming exercises."
    else:
        context = "Domain-specific exam with banking/finance programming challenges."
        scenario = "All programming questions involve banking systems: transactions, accounts, interest calculations, validation."

    return f"""Create a comprehensive exam paper for a Java training session.

Session: {session['session_title']}
Date: {session['date']}
Topics:
{topics_str}

Domain: {domain.upper()}
{context}
{scenario}

Create an exam with 4 sections (Total: 50 marks, Duration: 90 minutes):
Section A: MCQ (10 marks) - 10 questions x 1 mark
Section B: Short Answer (15 marks) - 5 questions x 3 marks
Section C: Programming Exercises (20 marks) - 4 exercises x 5 marks
Section D: Bonus/Advanced (5 marks) - 1 challenging problem

Return ONLY valid JSON:
{{
  "meta": {{
    "asset_type": "exam_paper",
    "session_day": {session['day']},
    "session_title": "{session['session_title']}",
    "domain": "{domain}",
    "total_marks": 50,
    "duration_minutes": 90,
    "passing_marks": 35
  }},
  "instructions": [
    "Read all questions carefully before answering.",
    "For programming questions, write clean and well-commented code.",
    "Time management: spend ~1 min per MCQ, ~5 min per short answer, ~12 min per programming exercise."
  ],
  "sections": [
    {{
      "section_id": "A",
      "section_title": "Multiple Choice Questions",
      "marks_per_question": 1,
      "total_marks": 10,
      "questions": [
        {{
          "question_id": "A1",
          "question_text": "Question here",
          "options": ["A. Option A", "B. Option B", "C. Option C", "D. Option D"],
          "correct_answer": "A",
          "marks": 1
        }}
      ]
    }},
    {{
      "section_id": "B",
      "section_title": "Short Answer Questions",
      "marks_per_question": 3,
      "total_marks": 15,
      "questions": [
        {{
          "question_id": "B1",
          "question_text": "Short answer question here",
          "marks": 3,
          "model_answer": "Expected answer",
          "key_points": ["Point 1", "Point 2", "Point 3"]
        }}
      ]
    }},
    {{
      "section_id": "C",
      "section_title": "Programming Exercises",
      "marks_per_question": 5,
      "total_marks": 20,
      "questions": [
        {{
          "question_id": "C1",
          "question_text": "Programming problem statement",
          "scenario": "Business context for the problem",
          "requirements": ["Requirement 1", "Requirement 2"],
          "starter_code": "public class Solution {{\\n  // Write your code here\\n}}",
          "marks": 5,
          "evaluation_criteria": ["Correctness: 2 marks", "Code quality: 2 marks", "Edge cases: 1 mark"]
        }}
      ]
    }},
    {{
      "section_id": "D",
      "section_title": "Bonus Challenge",
      "total_marks": 5,
      "questions": [
        {{
          "question_id": "D1",
          "question_text": "Advanced/bonus problem statement",
          "marks": 5,
          "hint": "Optional hint"
        }}
      ]
    }}
  ]
}}"""


def build_notes_prompt(session: dict, domain: str) -> str:
    topics_str = "\n".join(f"  {i+1}. {t}" for i, t in enumerate(session["topics"]))

    if domain == "academic":
        context = "Academic-style comprehensive study notes with theory, syntax, and examples."
        examples = "Use general programming examples (Employee, Shape, Animal classes, etc.)."
    else:
        context = "Domain-focused notes with banking/finance real-world applications."
        examples = "Frame all examples in banking context: BankAccount, Transaction, Customer, Loan, CreditCard classes."

    return f"""You are an expert Java instructor writing comprehensive study notes.

Session: {session['session_title']}
Date: {session['date']}
Phase: {session['phase']}

Topics to cover in depth:
{topics_str}

Home Assignment: {session['home_assignment']}

Domain: {domain.upper()}
{context}
{examples}

Write thorough study notes that a student can use to learn from scratch and revise.
Include: clear explanations, syntax boxes, worked code examples, common mistakes, tips.

Return ONLY valid JSON:
{{
  "meta": {{
    "asset_type": "notes",
    "session_day": {session['day']},
    "session_title": "{session['session_title']}",
    "date": "{session['date']}",
    "phase": "{session['phase']}",
    "domain": "{domain}",
    "reading_time_minutes": 45
  }},
  "overview": {{
    "summary": "2-3 sentence overview of what this session covers and why it matters",
    "learning_outcomes": [
      "By end of session, student will be able to..."
    ],
    "prerequisite_knowledge": ["Prior knowledge needed"]
  }},
  "sections": [
    {{
      "section_id": "S1",
      "title": "Section title (maps to a topic)",
      "content": "Detailed explanation of the concept (3-5 paragraphs minimum)",
      "syntax_box": {{
        "description": "Syntax explanation",
        "code": "// Java syntax example\\ncode here"
      }},
      "examples": [
        {{
          "title": "Example title",
          "description": "What this example demonstrates",
          "code": "// Complete working Java code example",
          "output": "Expected output or explanation of result"
        }}
      ],
      "key_points": ["Important point 1", "Important point 2"],
      "common_mistakes": ["Mistake to avoid 1", "Mistake to avoid 2"]
    }}
  ],
  "quick_reference": {{
    "cheat_sheet": [
      {{"item": "Concept name", "description": "One-line explanation"}}
    ]
  }},
  "home_assignment": {{
    "title": "Home Assignment",
    "description": "{session['home_assignment']}",
    "hints": ["Hint 1", "Hint 2"],
    "submission": "Push to GitHub with README explaining your solution"
  }}
}}"""


# ─── Generator ───────────────────────────────────────────────────────────────

def generate_session_assets(session: dict, api_key: str, sets: list = [1, 2]):
    """Generate all assets for a session."""
    day = session["day"]
    print(f"\n{'='*60}")
    print(f"Generating content for Day {day}: {session['session_title']}")
    print(f"{'='*60}")

    domain_map = {1: "academic", 2: "banking_finance"}

    for set_num in sets:
        domain = domain_map[set_num]
        print(f"\n--- Set {set_num}: {domain.upper()} ---")

        # Create output directory
        set_dir = OUTPUT_DIR / f"day_{day:02d}" / f"set_{set_num}"
        set_dir.mkdir(parents=True, exist_ok=True)

        assets = [
            ("notes",          build_notes_prompt,         f"notes_day_{day:02d}_set{set_num}.json",   8096),
            ("flashcards",     build_flashcard_prompt,     f"fc_set{set_num}_day_{day:02d}.json",      4096),
            ("quiz",           build_quiz_prompt,          f"quiz_set{set_num}_day_{day:02d}.json",    4096),
            ("matching_game",  build_matching_game_prompt, f"mg_set{set_num}_day_{day:02d}.json",      3096),
            ("matching_pair",  build_matching_pair_prompt, f"mp_set{set_num}_day_{day:02d}.json",      3096),
            ("lab_manual",     build_lab_manual_prompt,    f"lab_set{set_num}_day_{day:02d}.json",     6096),
            ("exam_paper",     build_exam_paper_prompt,    f"exam_set{set_num}_day_{day:02d}.json",    8096),
        ]

        for asset_type, prompt_fn, filename, max_tokens in assets:
            outfile = set_dir / filename

            if outfile.exists():
                print(f"  ⏭  {asset_type} already exists: {filename}")
                continue

            print(f"  🔄 Generating {asset_type}...", end="", flush=True)

            try:
                prompt = prompt_fn(session, domain)
                response_text = call_claude(api_key, prompt, max_tokens)
                content = parse_json_response(response_text)

                with open(outfile, "w", encoding="utf-8") as f:
                    json.dump(content, f, indent=2, ensure_ascii=False)

                print(f" ✅ saved → {outfile.name}")

                # Rate limiting: 1 second between calls
                time.sleep(1)

            except json.JSONDecodeError as e:
                print(f" ⚠️  JSON parse error: {e}")
                # Save raw response for debugging
                raw_file = set_dir / f"_raw_{filename}"
                raw_file.write_text(response_text, encoding="utf-8")
                print(f"     Raw response saved to: {raw_file.name}")

            except requests.HTTPError as e:
                print(f" ❌ API error: {e}")
                if e.response.status_code == 429:
                    print("     Rate limited. Waiting 30 seconds...")
                    time.sleep(30)

            except Exception as e:
                print(f" ❌ Error: {e}")
                import traceback
                traceback.print_exc()


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate Claude-powered content for Java Full Stack course")
    parser.add_argument("--api-key", required=True, help="Anthropic API key (sk-ant-...)")
    parser.add_argument("--session", type=int, default=None, help="Session day number (1-30). Omit for --all.")
    parser.add_argument("--all", action="store_true", help="Generate for all sessions")
    parser.add_argument("--set", type=int, choices=[1, 2], default=None, help="Only generate set 1 or set 2. Default: both.")
    args = parser.parse_args()

    if not args.api_key.startswith("sk-ant-"):
        print("Warning: API key doesn't start with sk-ant-. Make sure it's a valid Anthropic key.")

    sets = [args.set] if args.set else [1, 2]

    if args.all:
        sessions_to_process = SESSIONS
    elif args.session:
        sessions_to_process = [s for s in SESSIONS if s["day"] == args.session]
        if not sessions_to_process:
            print(f"Error: No session found for day {args.session} in the configured sessions.")
            print(f"Available days: {[s['day'] for s in SESSIONS]}")
            sys.exit(1)
    else:
        print("Error: Specify --session <day> or --all")
        parser.print_help()
        sys.exit(1)

    print(f"\n🚀 Claude Content Generator - Java Full Stack Course")
    print(f"   Model: {CLAUDE_MODEL}")
    print(f"   Sessions: {[s['day'] for s in sessions_to_process]}")
    print(f"   Sets: {sets}")
    print(f"   Output: {OUTPUT_DIR}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for session in sessions_to_process:
        generate_session_assets(session, args.api_key, sets=sets)

    print(f"\n\n✅ Generation complete! Files saved to: {OUTPUT_DIR}")
    print(f"\nNext steps:")
    print(f"  1. Review generated files in {OUTPUT_DIR}")
    print(f"  2. Run upload_to_prod.py to push to VPS and register in DB")


if __name__ == "__main__":
    main()
