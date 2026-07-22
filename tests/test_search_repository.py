"""Search repository tests."""

import uuid

from sqlalchemy.orm import Session

from src.database.models.job_search import JobSearch
from src.repositories.search_repository import SearchRepository


def _build_search(**kwargs: bool | str) -> JobSearch:
    """Build a job search with default values."""
    defaults: dict[str, bool | str] = {
        "keyword": "python",
        "state": "SP",
        "municipality": "São Paulo",
        "remote": False,
        "active": True,
    }
    defaults.update(kwargs)
    return JobSearch(**defaults)


def test_get_all_active(db: Session) -> None:
    """Verify only active searches are returned."""
    repo = SearchRepository(db)
    db.add_all(
        [
            _build_search(keyword="python", active=True),
            _build_search(keyword="java", active=False),
        ]
    )
    db.commit()

    results = repo.get_all_active()

    assert len(results) == 1
    assert results[0].keyword == "python"


def test_get_by_id(db: Session) -> None:
    """Verify search retrieval by id."""
    repo = SearchRepository(db)
    search = _build_search()
    db.add(search)
    db.commit()

    result = repo.get_by_id(search.id)

    assert result is not None
    assert result.id == search.id


def test_get_by_id_not_found(db: Session) -> None:
    """Verify None returned when id does not exist."""
    repo = SearchRepository(db)

    result = repo.get_by_id(uuid.uuid4())

    assert result is None


def test_get_by_status(db: Session) -> None:
    """Verify search retrieval by active status."""
    repo = SearchRepository(db)
    db.add_all(
        [
            _build_search(keyword="python", active=True),
            _build_search(keyword="java", active=False),
        ]
    )
    db.commit()

    active_results = repo.get_by_status(True)
    inactive_results = repo.get_by_status(False)

    assert len(active_results) == 1
    assert active_results[0].keyword == "python"
    assert len(inactive_results) == 1
    assert inactive_results[0].keyword == "java"
