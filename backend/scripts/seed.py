"""
Development seed script.
Creates sample users, courses, and enrollments for local development.
Run: python scripts/seed.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import bcrypt
from app import create_app
from app.extensions import db
from app.models import User, UserRole, Course, Enrollment, StudentModel


def seed():
    app = create_app()
    with app.app_context():
        print("Seeding development data...")

        # Check if already seeded
        if User.query.filter_by(email="student@demo.com").first():
            print("  ⚠ Already seeded. Skipping.")
            return

        # Create users
        def make_user(email, username, password, role, display_name):
            pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            u = User(
                email=email,
                username=username,
                password_hash=pw_hash,
                role=role,
                display_name=display_name,
                is_active=True,
            )
            db.session.add(u)
            db.session.flush()
            sm = StudentModel(user_id=u.id)
            db.session.add(sm)
            return u

        student = make_user(
            "student@demo.com", "alice_demo", "Password123!", UserRole.student, "Alice Demo"
        )
        instructor = make_user(
            "instructor@demo.com", "prof_demo", "Password123!", UserRole.instructor, "Prof. Demo"
        )

        # Create courses
        courses_data = [
            {
                "title": "Introduction to Python Programming",
                "code": "CS101",
                "description": "Learn Python fundamentals with hands-on exercises.",
                "syllabus": "Week 1: Variables and Types\nWeek 2: Control Flow\nWeek 3: Functions\nWeek 4: Data Structures",
            },
            {
                "title": "Data Structures and Algorithms",
                "code": "CS201",
                "description": "Core data structures: lists, trees, graphs, and algorithm design.",
                "syllabus": "Week 1: Arrays and Lists\nWeek 2: Stacks and Queues\nWeek 3: Trees\nWeek 4: Graphs",
            },
            {
                "title": "Software Engineering Principles",
                "code": "CS301",
                "description": "Best practices for software design, testing, and maintenance.",
                "syllabus": "Week 1: Design Patterns\nWeek 2: Testing Strategies\nWeek 3: CI/CD\nWeek 4: Code Review",
            },
        ]

        for cd in courses_data:
            course = Course(
                title=cd["title"],
                code=cd["code"],
                description=cd["description"],
                syllabus=cd["syllabus"],
                created_by=instructor.id,
            )
            db.session.add(course)
            db.session.flush()

            # Enroll both users
            for user in [student, instructor]:
                e = Enrollment(user_id=user.id, course_id=course.id)
                db.session.add(e)

        db.session.commit()
        print("  ✓ Created 2 users (student@demo.com / instructor@demo.com, password: Password123!)")
        print("  ✓ Created 3 courses: CS101, CS201, CS301")
        print("Done!")


if __name__ == "__main__":
    seed()

