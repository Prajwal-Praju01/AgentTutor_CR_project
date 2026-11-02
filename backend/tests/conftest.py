"""
Pytest configuration and fixtures.
Uses SQLite in-memory database for fast, isolated tests.
"""
import pytest
from app import create_app
from app.config import Settings
from app.extensions import db as _db


@pytest.fixture(scope="session")
def test_settings():
    """Override settings for test environment."""
    return Settings(
        flask_env="testing",
        flask_debug=False,
        secret_key="test-secret-key",
        database_url="sqlite:///:memory:",
        test_database_url="sqlite:///:memory:",
        llm_provider="mock",
        embedding_provider="mock",
        enable_vector_search=False,
        jwt_secret_key="test-jwt-secret",
    )


@pytest.fixture(scope="session")
def app(test_settings):
    """Session-scoped test application."""
    _app = create_app(settings=test_settings)
    _app.config["TESTING"] = True
    _app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"

    with _app.app_context():
        _db.create_all()
        yield _app
        _db.drop_all()


@pytest.fixture(scope="session")
def client(app):
    return app.test_client()


@pytest.fixture(autouse=True)
def clean_db(app):
    """
    Clear all table rows between tests.
    Works with SQLite in-memory; avoids the bind/transaction issues of newer SQLAlchemy.
    """
    yield
    with app.app_context():
        # Delete in reverse dependency order to respect FK constraints
        for table in reversed(_db.metadata.sorted_tables):
            _db.session.execute(table.delete())
        _db.session.commit()


@pytest.fixture
def db_session(app):
    with app.app_context():
        yield _db.session


@pytest.fixture
def test_user(app, db_session):
    """Create a standard test student user."""
    import bcrypt
    from app.models import User, UserRole, StudentModel

    pw_hash = bcrypt.hashpw(b"TestPass123!", bcrypt.gensalt()).decode()
    user = User(
        email="testuser@test.com",
        username="testuser",
        password_hash=pw_hash,
        role=UserRole.student,
        display_name="Test User",
    )
    db_session.add(user)
    db_session.flush()

    sm = StudentModel(user_id=user.id)
    db_session.add(sm)
    db_session.commit()

    return user


@pytest.fixture
def test_course(app, db_session, test_user):
    """Create a test course with the test user enrolled."""
    from app.models import Course, Enrollment

    course = Course(
        title="Test Course",
        code="TEST101",
        description="A test course",
        created_by=test_user.id,
    )
    db_session.add(course)
    db_session.flush()

    enrollment = Enrollment(user_id=test_user.id, course_id=course.id)
    db_session.add(enrollment)
    db_session.commit()

    return course


@pytest.fixture
def auth_headers(app, test_user):
    """Return Authorization headers for the test user."""
    from app.services.auth_service import create_tokens
    with app.app_context():
        access_token, _ = create_tokens(test_user.id)
    return {"Authorization": f"Bearer {access_token}"}
