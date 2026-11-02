# API

The backend exposes JSON endpoints below `/api/v1`. Protected endpoints use
`Authorization: Bearer <access-token>`.

## Public

- `GET /health`
- `POST /auth/register`
- `POST /auth/login`

## Authenticated application endpoints

- `GET /auth/me`
- `GET /courses`
- `POST /courses`
- `GET /courses/{course_id}`
- `PATCH /courses/{course_id}`
- `POST /courses/{course_id}/enroll`
- `POST /courses/{course_id}/documents`
- `GET /courses/{course_id}/documents`
- `DELETE /courses/{course_id}/documents/{document_id}`
- `POST /sessions`
- `GET /sessions/{session_id}`
- `GET /sessions/{session_id}/history`
- `POST /sessions/{session_id}/messages`
- `GET /sessions/{session_id}/states`
- `PATCH /sessions/{session_id}/end`
- `GET /students/me/progress`

Evaluation results are available at `GET /evaluations/{evaluation_id}` to
instructors and administrators only.

Errors use the shape:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Request validation failed",
    "details": []
  }
}
```

The backend owns authorization and validation; clients must not rely on
frontend route protection for access control.
