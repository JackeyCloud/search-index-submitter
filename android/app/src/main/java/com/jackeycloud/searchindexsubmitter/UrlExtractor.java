package com.jackeycloud.searchindexsubmitter;

import java.net.URI;
import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public final class UrlExtractor {
    private static final Pattern EXPLICIT_URL = Pattern.compile(
            "(?i)\\b(?:https?://|www\\.)[^\\s\\u3000<>\\\"'“”‘’，。；：！？）】》」』、]+"
    );
    private static final Pattern BARE_DOMAIN = Pattern.compile(
            "(?i)(?<![@\\w])(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\\.)+[a-z]{2,}(?:/[^\\s\\u3000<>\\\"'“”‘’，。；：！？）】》」』、]*)?"
    );
    private static final String TRAILING = ".,;:!?)]}。，；：！？）】》」』、";

    private UrlExtractor() {
    }

    public static List<String> extract(String text) {
        Set<String> results = new LinkedHashSet<>();
        collect(EXPLICIT_URL, text == null ? "" : text, results);
        if (results.isEmpty()) {
            collect(BARE_DOMAIN, text == null ? "" : text, results);
        }
        return new ArrayList<>(results);
    }

    private static void collect(Pattern pattern, String text, Set<String> results) {
        Matcher matcher = pattern.matcher(text);
        while (matcher.find()) {
            String value = trimTrailing(matcher.group());
            String normalized = normalize(value);
            if (normalized != null) {
                results.add(normalized);
            }
        }
    }

    private static String trimTrailing(String value) {
        while (!value.isEmpty() && TRAILING.indexOf(value.charAt(value.length() - 1)) >= 0) {
            value = value.substring(0, value.length() - 1);
        }
        return value;
    }

    private static String normalize(String value) {
        try {
            if (!value.toLowerCase(Locale.ROOT).startsWith("http://")
                    && !value.toLowerCase(Locale.ROOT).startsWith("https://")) {
                value = "https://" + value;
            }
            URI uri = URI.create(value);
            String scheme = uri.getScheme() == null ? "https" : uri.getScheme().toLowerCase(Locale.ROOT);
            String host = uri.getHost();
            if (host == null || !(scheme.equals("http") || scheme.equals("https"))) {
                return null;
            }
            String path = uri.getRawPath();
            if (path == null || path.isEmpty()) {
                path = "/";
            }
            return new URI(scheme, uri.getUserInfo(), host.toLowerCase(Locale.ROOT), uri.getPort(), path,
                    uri.getRawQuery(), null).toASCIIString();
        } catch (Exception ignored) {
            return null;
        }
    }
}
