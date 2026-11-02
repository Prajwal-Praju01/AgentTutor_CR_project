# AgentTutor — Database Schema and Migrations

AgentTutor uses SQLAlchemy 2.0 with Alembic for database schema versioning and migrations. The primary production database is PostgreSQL with `pgvector` support, with seamless SQLite in-memory capability for automated testing.

## Entity Relationship Overview

```
 [User] 1──* [Enrollment] *──1 [Course]
   │                              │
   │ 1                            │ 1
   │                              │
   *                              *
[Session]                     [CourseDocument]
   │                              │
   ├── 1──* [Message]             └── 1──* [DocumentChunk]
   │
   ├── 1──1 [DebuggingTask]
   │           ├── 1──* [LearningState]
   │           ├── 1──* [QuestionNode] 1──* [StudentResponse]
   │           ├── 1──* [ProposedFix]
   │           └── 1──* [BugHypothesis]
   │
   └── 1──* [StudentModelSnapshot] *──1 [StudentModel] 1──1 [User]
```

## Tables & Primary Data Structures

1. **`users`**: UUID primary key, credentials hashed via bcrypt, user role enum (`student`, `instructor`, `admin`), timestamps.
2. **`courses`**: Course catalog entries, title, unique course code (`CS101`), description, syllabus, creator FK.
3. **`enrollments`**: Many-to-many relationship tracking user course registrations with unique constraint `(user_id, course_id)`.
4. **`course_documents`**: Uploaded learning resources, filename, mime type, byte size, page count, document status enum (`pending`, `processing`, `ready`, `failed`).
5. **`document_chunks`**: Segmented document passages (800 character window with 100 character overlap), page numbers, detected section headings, and vector embeddings.
6. **`sessions`**: Interaction container (`tutoring` or `debugging`), student reference, course reference, status (`active`, `completed`, `abandoned`).
7. **`messages`**: Transcript records with sender role (`student`, `tutor`, `system`), message content, and structured metadata JSON.
8. **`student_models`**: Persistent student profile containing running concept mastery scores, frequency-counted misconceptions, and course state tracking.
9. **`student_model_snapshots`**: Point-in-time understanding level assessments (0-3), hint depths (1-4), justifications, and recorded confidence.
10. **`debugging_tasks`**: Socratic debugging problem definition, buggy code, programming language, expected behavior, and resolution status.
11. **`learning_states`**: Canonical ordered milestones for isolating bugs with task dependency DAG arrays.
12. **`question_nodes`**: TreeInstruct hierarchical question tree nodes with question type (`root`, `child`, `sibling`), tree depth, branch index, and active state flags.
13. **`student_responses`**: Student answers to question nodes linked with verifier verdicts (`correct`, `partially_correct`, `incorrect`, `uncertain`), justifications, and confidence scores.
14. **`proposed_fixes`**: Student-submitted code patches with static syntax validation and execution test results.
15. **`llm_call_logs`**: Complete audit logs capturing prompt versions, caller agent names, provider names, models, token usage, and latency.
16. **`evaluation_runs`**: Research experiment results tracking benchmark conditions, datasets, sample sizes, and computed metrics.

## Migrations

Alembic configuration is managed in `backend/alembic.ini` and `backend/migrations/env.py`.

To apply migrations:
```bash
python -m alembic upgrade head
```

To create a new revision:
```bash
python -m alembic revision --autogenerate -m "description"
```

