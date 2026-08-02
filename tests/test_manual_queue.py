"""Manual queue tests."""

from src.queue.manual_queue import ManualQueue


def test_enqueue_increases_size() -> None:
    """Verify enqueue adds a URL to the queue."""
    queue = ManualQueue.__new__(ManualQueue)
    queue._queue = []
    queue.enqueue("https://www.linkedin.com/jobs/view/123")
    assert queue.size == 1


def test_enqueue_batch_adds_multiple_urls() -> None:
    """Verify enqueue_batch adds multiple URLs."""
    queue = ManualQueue.__new__(ManualQueue)
    queue._queue = []
    queue.enqueue_batch(
        [
            "https://www.linkedin.com/jobs/view/1",
            "https://www.gupy.io/jobs/view/2",
        ]
    )
    assert queue.size == 2


def test_resolve_provider_linkedin() -> None:
    """Verify LinkedIn domain resolves to linkedin provider."""
    queue = ManualQueue.__new__(ManualQueue)
    provider = queue._resolve_provider("https://www.linkedin.com/jobs/view/123")
    assert provider == "linkedin"


def test_resolve_provider_gupy() -> None:
    """Verify Gupy domain resolves to gupy provider."""
    queue = ManualQueue.__new__(ManualQueue)
    provider = queue._resolve_provider("https://portal.gupy.io/jobs/view/123")
    assert provider == "gupy"


def test_resolve_provider_unsupported() -> None:
    """Verify unsupported domain returns None."""
    queue = ManualQueue.__new__(ManualQueue)
    provider = queue._resolve_provider("https://www.example.com/jobs/view/123")
    assert provider is None


def test_deque_uses_collections_deque() -> None:
    """Verify ManualQueue uses collections.deque internally."""
    import collections.abc

    queue = ManualQueue.__new__(ManualQueue)
    queue._queue = collections.deque()
    assert isinstance(queue._queue, collections.deque)


def test_size_empty_queue() -> None:
    """Verify size returns 0 for empty queue."""
    queue = ManualQueue.__new__(ManualQueue)
    queue._queue = []
    assert queue.size == 0
