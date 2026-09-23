"""Metrics tracker for provider execution statistics."""

from collections import defaultdict
from threading import Lock

_metrics: dict[str, dict[str, int]] = defaultdict(
    lambda: {"executions": 0, "jobs_found": 0},
)
_metrics_lock = Lock()


def record_execution(provider_name: str, jobs_found: int) -> None:
    """Record a provider execution in the metrics store.

    Args:
        provider_name (str): Name of the provider.
        jobs_found (int): Number of vacancies found.
    """
    with _metrics_lock:
        _metrics[provider_name]["executions"] += 1
        _metrics[provider_name]["jobs_found"] += jobs_found


def get_metrics() -> dict[str, dict[str, dict[str, int]]]:
    """Return a copy of the current metrics wrapped in providers key.

    Returns:
        dict[str, dict[str, dict[str, int]]]: Metrics per provider.
    """
    with _metrics_lock:
        result: dict[str, dict[str, int]] = {}
        for k, v in _metrics.items():
            result[k] = {"executions": v["executions"], "jobs_found": v["jobs_found"]}
        return {"providers": result}
