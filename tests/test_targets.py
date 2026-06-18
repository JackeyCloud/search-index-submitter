import pytest

from search_submitter.targets import normalize_url, parse_targets


def test_normalize_domain_and_strip_fragment():
    assert normalize_url("Example.COM/a#x") == "https://example.com/a"


def test_parse_groups_urls_by_site():
    targets = parse_targets("example.com/a\nhttps://example.com/b\nhttps://other.test")
    assert len(targets) == 2
    assert targets[0].site_url == "https://example.com/"
    assert targets[0].urls == ("https://example.com/a", "https://example.com/b")


def test_sitemap_template():
    target = parse_targets("example.com", "https://{host}/sitemap-index.xml")[0]
    assert target.sitemap_url == "https://example.com/sitemap-index.xml"


def test_invalid_scheme():
    with pytest.raises(ValueError):
        normalize_url("ftp://example.com/file")
