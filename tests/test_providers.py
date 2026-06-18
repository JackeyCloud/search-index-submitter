from search_submitter.config import AppConfig
from search_submitter.http import HttpResponse
from search_submitter.models import SiteTarget, Status
from search_submitter.providers.baidu import BaiduProvider
from search_submitter.providers.bing import BingProvider
from search_submitter.providers.indexnow import IndexNowProvider


class FakeClient:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.response

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.response


TARGET = SiteTarget("example.com", "https://example.com/", ("https://example.com/",))


def test_indexnow_dry_run_without_network():
    client = FakeClient(HttpResponse(200, "", {}))
    result = IndexNowProvider(AppConfig(indexnow_key="abc"), client).submit(TARGET, "https://example.com/sitemap.xml", True)
    assert result.status is Status.DRY_RUN
    assert client.calls == []


def test_baidu_success_response():
    client = FakeClient(HttpResponse(200, '{"remain":99,"success":1}', {}))
    result = BaiduProvider(AppConfig(baidu_token="secret"), client).submit(TARGET, "https://example.com/sitemap.xml")
    assert result.status is Status.SUCCESS
    assert "99" in result.message


def test_baidu_uses_host_token_map():
    client = FakeClient(HttpResponse(200, '{"remain":9,"success":1}', {}))
    config = AppConfig(baidu_token="default", baidu_token_map="example.com=mapped-secret")
    BaiduProvider(config, client).submit(TARGET, "https://example.com/sitemap.xml")
    assert "mapped-secret" in client.calls[0][0]
    assert "default" not in client.calls[0][0]


def test_missing_credentials_is_skipped():
    client = FakeClient(HttpResponse(200, "", {}))
    result = IndexNowProvider(AppConfig(), client).submit(TARGET, "https://example.com/sitemap.xml")
    assert result.status is Status.SKIPPED


def test_bing_duplicate_check_detects_existing_record():
    client = FakeClient(HttpResponse(200, '{"d":{"Url":"https://example.com/"}}', {}))
    result = BingProvider(AppConfig(bing_api_key="secret"), client).check_indexed(TARGET, TARGET.site_url)
    assert result.state.value == "indexed"
