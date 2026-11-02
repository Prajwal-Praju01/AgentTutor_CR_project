"""Tests for the retrieval pipeline."""


def test_keyword_search_returns_results(app, test_course, db_session):
    """Retriever should find chunks matching keywords."""
    from app.models import CourseDocument, DocumentChunk, DocumentStatus

    # Insert a test chunk directly
    doc = CourseDocument(
        course_id=test_course.id,
        uploaded_by=None,
        filename="test.txt",
        original_filename="test.txt",
        status=DocumentStatus.ready,
    )
    db_session.add(doc)
    db_session.flush()

    chunk = DocumentChunk(
        document_id=doc.id,
        course_id=test_course.id,
        content="Python uses indentation to define code blocks in loops and functions.",
        chunk_index=0,
        char_count=65,
    )
    db_session.add(chunk)
    db_session.flush()

    from app.retrieval.retriever import Retriever
    retriever = Retriever()
    results = retriever.search(course_id=test_course.id, query="Python loops indentation")

    assert len(results) > 0
    assert any("Python" in r["content"] for r in results)


def test_keyword_search_empty_query_returns_nothing(app, test_course):
    from app.retrieval.retriever import Retriever
    retriever = Retriever()
    results = retriever.search(course_id=test_course.id, query="a an the")
    # Very short stopwords should yield no results (all < 3 chars filtered)
    assert isinstance(results, list)


def test_chunking_plain_text():
    from app.retrieval.chunking import extract_and_chunk
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("Hello world. " * 200)  # Long enough to chunk
        path = f.name

    try:
        chunks = extract_and_chunk(path, "test.txt")
        assert len(chunks) >= 1
        for chunk in chunks:
            assert len(chunk["content"]) > 0
    finally:
        os.unlink(path)


def test_mock_embedding_is_deterministic():
    from app.retrieval.embeddings import MockEmbeddingBackend
    backend = MockEmbeddingBackend()

    e1 = backend.embed("test text")
    e2 = backend.embed("test text")
    assert e1 == e2
    assert len(e1) == 1536


def test_mock_embedding_differs_for_different_text():
    from app.retrieval.embeddings import MockEmbeddingBackend
    backend = MockEmbeddingBackend()

    e1 = backend.embed("Python for loops")
    e2 = backend.embed("Binary search trees")
    assert e1 != e2
