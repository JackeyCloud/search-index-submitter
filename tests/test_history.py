from pathlib import Path

from search_submitter.history import HistoryStore
from search_submitter.models import IndexState, Status, SubmissionResult


def test_history_persists_and_merges_index_status(tmp_path: Path):
    path = tmp_path / "history.db"
    store = HistoryStore(path)
    result = SubmissionResult(
        "Google",
        "https://example.com/",
        Status.SUCCESS,
        "ok",
        {
            "provider_id": "google",
            "index_checks": [
                {"url": "https://example.com/page", "state": "not_indexed", "message": "not found"}
            ],
        },
    )
    store.record_submission(["https://example.com/page"], [result])
    store.update_index_status("https://example.com/page", "google", IndexState.INDEXED)

    record = HistoryStore(path).list_records()[0]
    assert record.submission_count == 1
    assert record.submitted_providers == {"google": "success"}
    assert record.index_statuses == {"google": "indexed"}
    assert record.last_checked_at


def test_unknown_refresh_does_not_erase_indexed_state(tmp_path: Path):
    store = HistoryStore(tmp_path / "history.db")
    store.record_submission(["https://example.com/"], [])
    store.update_index_status("https://example.com/", "bing", IndexState.INDEXED)
    store.update_index_status("https://example.com/", "bing", IndexState.UNKNOWN)
    assert store.list_records()[0].index_statuses["bing"] == "indexed"
