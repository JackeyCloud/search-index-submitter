from search_submitter.config import AppConfig
from search_submitter.engine import run_submissions
from search_submitter.models import IndexCheck, IndexState, SiteTarget, Status, SubmissionResult


class IndexedProvider:
    id = "fake"
    display_name = "Fake"

    def check_indexed(self, target, url):
        return IndexCheck(IndexState.INDEXED, "found")

    def submit(self, target, sitemap_url, dry_run=False):
        raise AssertionError("submit must not run for indexed URLs")


class FakeClient:
    def get(self, url):
        from search_submitter.http import HttpResponse

        return HttpResponse(404, "", {})


def test_all_indexed_urls_skip_submission(monkeypatch):
    monkeypatch.setattr("search_submitter.engine.HttpClient", lambda timeout: FakeClient())
    monkeypatch.setattr("search_submitter.engine.build_providers", lambda config, client: {"fake": IndexedProvider()})
    target = SiteTarget("example.com", "https://example.com/", ("https://example.com/",))
    results = run_submissions([target], ["fake"], AppConfig())
    assert results[0].status is Status.SKIPPED
    assert "无需重复提交" in results[0].message
