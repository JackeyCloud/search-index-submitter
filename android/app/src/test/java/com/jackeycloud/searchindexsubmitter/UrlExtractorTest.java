package com.jackeycloud.searchindexsubmitter;

import static org.junit.Assert.assertEquals;

import java.util.Arrays;
import java.util.List;

import org.junit.Test;

public class UrlExtractorTest {
    @Test
    public void extractsUrlFromXiaohongshuShareText() {
        String share = "复制后打开小红书，查看笔记 https://xhslink.com/a1B2C3，更多精彩内容";
        assertEquals(Arrays.asList("https://xhslink.com/a1B2C3"), UrlExtractor.extract(share));
    }

    @Test
    public void deduplicatesAndTrimsChinesePunctuation() {
        String text = "https://example.com/a。 再看 https://example.com/a";
        assertEquals(Arrays.asList("https://example.com/a"), UrlExtractor.extract(text));
    }

    @Test
    public void acceptsBareDomainWhenNoExplicitUrlExists() {
        List<String> urls = UrlExtractor.extract("请提交 example.com/path");
        assertEquals(Arrays.asList("https://example.com/path"), urls);
    }
}
