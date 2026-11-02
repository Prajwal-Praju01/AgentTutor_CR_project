"""Tests for restricted research evaluation results."""
from app.models import EvaluationRun, User, UserRole


def test_student_cannot_read_evaluation(client, db_session, test_user):
    evaluation = EvaluationRun(
        experiment_name="smoke",
        condition="E",
        status="complete",
        results={"sample_size": 1},
    )
    db_session.add(evaluation)
    db_session.commit()

    from app.services.auth_service import create_tokens
    access_token, _ = create_tokens(test_user.id)
    response = client.get(
        f"/api/v1/evaluations/{evaluation.id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 403


def test_instructor_can_read_evaluation(client, db_session):
    instructor = User(
        email="instructor@test.com",
        username="instructor",
        password_hash="not-used",
        role=UserRole.instructor,
        display_name="Instructor",
    )
    db_session.add(instructor)
    evaluation = EvaluationRun(
        experiment_name="smoke",
        condition="E",
        status="complete",
        results={"sample_size": 1},
    )
    db_session.add(evaluation)
    db_session.commit()

    from app.services.auth_service import create_tokens
    access_token, _ = create_tokens(instructor.id)
    response = client.get(
        f"/api/v1/evaluations/{evaluation.id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    assert response.get_json()["evaluation"]["results"] == {"sample_size": 1}
