import logging
import time
from contextvars import ContextVar
from functools import wraps

log = logging.getLogger(__name__)

# Context variable to store timings per request
_timings: ContextVar[list[tuple[str, float]] | None] = ContextVar("timings", default=None)


def start_timing_context() -> None:
    """Start a new timing context for the current request."""
    _timings.set([])


def record_timing(name: str, duration_ms: float) -> None:
    """Record a timing entry."""
    timings = _timings.get()
    if timings is not None:
        timings.append((name, duration_ms))
    # Also log immediately for debugging
    log.info(f"[TIMING] {name}: {duration_ms:.1f}ms")


def get_timings() -> list[tuple[str, float]]:
    """Get all recorded timings."""
    return _timings.get() or []


def log_timing_summary() -> None:
    """Log a summary of all recorded timings."""
    timings = get_timings()
    if not timings:
        return

    log.info("=" * 60)
    log.info("[TIMING SUMMARY]")
    log.info("-" * 60)

    total = 0.0
    for name, duration in timings:
        log.info(f"  {name:<40} {duration:>8.1f}ms")
        total += duration

    log.info("-" * 60)
    log.info(f"  {'Total recorded':<40} {total:>8.1f}ms")
    log.info("=" * 60)


class TimingBlock:
    """Context manager for timing a code block."""

    def __init__(self, name: str):
        self.name = name
        self.start = None

    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, *args):
        elapsed_ms = (time.perf_counter() - self.start) * 1000
        record_timing(self.name, elapsed_ms)
