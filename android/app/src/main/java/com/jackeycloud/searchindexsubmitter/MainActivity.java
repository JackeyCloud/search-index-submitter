package com.jackeycloud.searchindexsubmitter;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.text.Editable;
import android.text.InputType;
import android.text.TextWatcher;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.view.WindowInsets;
import android.view.WindowInsetsController;
import android.widget.Button;
import android.widget.CheckBox;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URI;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class MainActivity extends Activity {
    private static final int BG = Color.rgb(246, 249, 254);
    private static final int CARD = Color.WHITE;
    private static final int FIELD = Color.rgb(248, 250, 252);
    private static final int BORDER = Color.rgb(220, 230, 242);
    private static final int TEXT = Color.rgb(23, 32, 51);
    private static final int MUTED = Color.rgb(100, 116, 139);
    private static final int BLUE = Color.rgb(36, 117, 232);
    private static final String PREFS = "search_submitter";
    private static final String GUIDE_URL = "https://github.com/JackeyCloud/search-index-submitter/blob/main/docs/%E6%90%9C%E7%B4%A2%E5%BC%95%E6%93%8E%E4%B8%80%E9%94%AE%E6%8F%90%E4%BA%A4%E5%B7%A5%E5%85%B7_%E7%94%A8%E6%88%B7%E9%85%8D%E7%BD%AE%E4%B8%8E%E4%BD%BF%E7%94%A8%E6%8C%87%E5%8D%97.md";

    private final ExecutorService executor = Executors.newSingleThreadExecutor();
    private SharedPreferences prefs;
    private HistoryStore historyStore;
    private EditText input;
    private TextView extractionHint;
    private TextView results;
    private Button submitButton;
    private Button refreshButton;
    private CheckBox indexNowCheck;
    private CheckBox baiduCheck;
    private CheckBox bingCheck;
    private CheckBox yandexCheck;
    private LinearLayout historyContainer;
    private TextView configHint;
    private boolean updatingText;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        configureSystemBars();
        prefs = getSharedPreferences(PREFS, MODE_PRIVATE);
        historyStore = new HistoryStore(this);
        setContentView(buildUi());
        handleSharedText(getIntent());
        showOnboardingIfNeeded();
    }

    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        setIntent(intent);
        handleSharedText(intent);
    }

    @Override
    protected void onDestroy() {
        executor.shutdownNow();
        historyStore.close();
        super.onDestroy();
    }

    private View buildUi() {
        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        scroll.setBackgroundColor(BG);

        LinearLayout root = vertical();
        root.setPadding(dp(20), dp(16), dp(20), dp(28));
        root.setBackgroundColor(BG);
        applySafeAreaInsets(root);
        scroll.addView(root, matchWrap());

        LinearLayout header = horizontal();
        LinearLayout titleArea = vertical();
        TextView title = text("内容收录助手", 26, TEXT, true);
        TextView subtitle = text("让自有网站内容更快被搜索引擎发现", 13, MUTED, false);
        titleArea.addView(title);
        titleArea.addView(subtitle);
        header.addView(titleArea, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));
        refreshButton = button("⟳", false);
        refreshButton.setContentDescription("刷新历史网址收录状态");
        refreshButton.setOnClickListener(v -> refreshHistory());
        header.addView(refreshButton, new LinearLayout.LayoutParams(dp(52), dp(46)));
        Button settings = button("账号与平台", false);
        settings.setOnClickListener(v -> showSettings());
        LinearLayout.LayoutParams settingsParams = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, dp(46));
        settingsParams.setMarginStart(dp(8));
        header.addView(settings, settingsParams);
        root.addView(header, marginBottom(16));

        LinearLayout hero = vertical();
        hero.setPadding(dp(16), dp(14), dp(16), dp(14));
        hero.setBackground(rounded(Color.rgb(234, 244, 255), Color.rgb(191, 220, 255), 14));
        hero.addView(text("一次粘贴，多平台发现", 18, Color.rgb(20, 89, 168), true));
        TextView heroCopy = text("自动提取链接、提交前查重、保存提交记录，帮助你的官网、博客、产品页和内容站点更快进入搜索引擎发现流程。", 13, Color.rgb(51, 74, 105), false);
        heroCopy.setLineSpacing(0, 1.12f);
        hero.addView(heroCopy, marginTop(6));
        hero.addView(text("1 粘贴链接  ·  2 连接站长平台  ·  3 查重提交", 13, Color.rgb(23, 103, 212), true), marginTop(9));
        TextView ownership = text("第三方笔记可提取链接，但不能用你的凭据代替小红书、携程等平台提交。", 12, Color.rgb(138, 90, 18), false);
        ownership.setPadding(dp(10), dp(8), dp(10), dp(8));
        ownership.setBackground(rounded(Color.rgb(255, 247, 230), Color.rgb(242, 211, 155), 8));
        hero.addView(ownership, marginTop(10));
        root.addView(hero, marginBottom(14));

        LinearLayout inputCard = card();
        inputCard.addView(text("批量输入网址或分享文案", 16, TEXT, true));
        input = new EditText(this);
        input.setTextColor(TEXT);
        input.setHintTextColor(Color.rgb(126, 143, 166));
        input.setTextSize(15);
        input.setGravity(Gravity.TOP | Gravity.START);
        input.setHint("每行一个网址，或直接粘贴小红书等平台的整段分享文案…");
        input.setMinLines(8);
        input.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_MULTI_LINE | InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS);
        input.setPadding(dp(14), dp(12), dp(14), dp(12));
        input.setBackground(rounded(FIELD, BORDER, 10));
        inputCard.addView(input, marginTop(10));
        input.addTextChangedListener(new TextWatcher() {
            @Override public void beforeTextChanged(CharSequence s, int start, int count, int after) { }
            @Override public void onTextChanged(CharSequence s, int start, int before, int count) { }
            @Override public void afterTextChanged(Editable editable) { autoExtract(editable.toString()); }
        });

        extractionHint = text("支持 http、https、www 和裸域名；自动去重并清除中文标点", 12, MUTED, false);
        inputCard.addView(extractionHint, marginTop(8));

        LinearLayout inputActions = horizontal();
        Button paste = button("粘贴并提取", true);
        paste.setOnClickListener(v -> pasteFromClipboard());
        Button clear = button("清空", false);
        clear.setOnClickListener(v -> input.setText(""));
        inputActions.addView(paste, new LinearLayout.LayoutParams(0, dp(46), 1));
        LinearLayout.LayoutParams clearParams = new LinearLayout.LayoutParams(0, dp(46), 1);
        clearParams.setMarginStart(dp(10));
        inputActions.addView(clear, clearParams);
        inputCard.addView(inputActions, marginTop(12));
        root.addView(inputCard, marginBottom(14));

        LinearLayout platformCard = card();
        platformCard.addView(text("提交平台", 16, TEXT, true));
        indexNowCheck = check("IndexNow（Bing / Yandex 等）", true);
        baiduCheck = check("百度普通收录", true);
        bingCheck = check("Bing Webmaster API", false);
        yandexCheck = check("Yandex Sitemap API", false);
        platformCard.addView(indexNowCheck);
        platformCard.addView(baiduCheck);
        platformCard.addView(bingCheck);
        platformCard.addView(yandexCheck);
        TextView platformNote = text("站长提交只适用于你拥有、已验证，或能部署验证文件的网站。公开页面会被搜索引擎自然发现，但第三方平台链接不能由本软件强制提交。", 12, MUTED, false);
        platformNote.setPadding(0, dp(8), 0, 0);
        platformCard.addView(platformNote);
        configHint = text("", 13, Color.rgb(23, 103, 212), true);
        configHint.setPadding(dp(12), dp(10), dp(12), dp(10));
        configHint.setBackground(rounded(Color.rgb(234, 244, 255), Color.rgb(156, 200, 247), 9));
        configHint.setOnClickListener(v -> showSettings());
        platformCard.addView(configHint, marginTop(10));
        updateConfigHint();
        root.addView(platformCard, marginBottom(14));

        submitButton = button("查重并开始提交", true);
        submitButton.setTextSize(16);
        submitButton.setOnClickListener(v -> submit());
        root.addView(submitButton, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, dp(52)));

        TextView resultTitle = text("处理结果", 16, TEXT, true);
        root.addView(resultTitle, marginTop(18));
        results = text("等待提交…", 13, MUTED, false);
        results.setTextIsSelectable(true);
        results.setPadding(dp(14), dp(12), dp(14), dp(12));
        results.setBackground(rounded(FIELD, BORDER, 10));
        root.addView(results, marginTop(8));

        LinearLayout historyHeader = horizontal();
        historyHeader.addView(text("提交记录", 18, TEXT, true), new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));
        TextView historyHint = text("● 点亮表示已确认收录", 12, MUTED, false);
        historyHeader.addView(historyHint);
        root.addView(historyHeader, marginTop(20));
        historyContainer = vertical();
        root.addView(historyContainer, marginTop(8));
        renderHistory();
        return scroll;
    }

    private void autoExtract(String raw) {
        if (updatingText || raw.trim().isEmpty()) {
            extractionHint.setText("支持 http、https、www 和裸域名；自动去重并清除中文标点");
            return;
        }
        List<String> urls = UrlExtractor.extract(raw);
        if (urls.isEmpty()) {
            extractionHint.setText("尚未识别到网址");
            return;
        }
        String joined = String.join("\n", urls);
        extractionHint.setText("已识别 " + urls.size() + " 条链接");
        boolean containsShareText = raw.length() > joined.length() + 3 || raw.contains("，") || raw.contains("复制") || raw.contains("打开");
        if (containsShareText && !raw.trim().equals(joined)) {
            updatingText = true;
            input.setText(joined);
            input.setSelection(joined.length());
            updatingText = false;
        }
    }

    private void pasteFromClipboard() {
        ClipboardManager manager = (ClipboardManager) getSystemService(CLIPBOARD_SERVICE);
        ClipData clip = manager == null ? null : manager.getPrimaryClip();
        if (clip == null || clip.getItemCount() == 0) {
            toast("剪贴板中没有文本");
            return;
        }
        CharSequence value = clip.getItemAt(0).coerceToText(this);
        List<String> urls = UrlExtractor.extract(value == null ? "" : value.toString());
        if (urls.isEmpty()) {
            toast("没有识别到链接");
            return;
        }
        input.setText(String.join("\n", urls));
        toast("已提取 " + urls.size() + " 条链接");
    }

    private void handleSharedText(Intent intent) {
        if (intent == null || !Intent.ACTION_SEND.equals(intent.getAction()) || !"text/plain".equals(intent.getType())) {
            return;
        }
        String shared = intent.getStringExtra(Intent.EXTRA_TEXT);
        List<String> urls = UrlExtractor.extract(shared);
        if (!urls.isEmpty()) {
            input.setText(String.join("\n", urls));
            toast("已从分享内容提取 " + urls.size() + " 条链接");
        }
    }

    private void submit() {
        List<String> urls = UrlExtractor.extract(input.getText().toString());
        if (urls.isEmpty()) {
            toast("请先粘贴至少一个有效链接");
            return;
        }
        if (!indexNowCheck.isChecked() && !baiduCheck.isChecked() && !bingCheck.isChecked() && !yandexCheck.isChecked()) {
            toast("请至少选择一个平台");
            return;
        }
        List<String> missing = missingSelectedConfigs();
        if (!missing.isEmpty()) {
            String message = "以下平台还没有完成配置：\n\n• " + String.join("\n• ", missing)
                    + "\n\n站长平台只接受您拥有或已验证站点的链接。请先完成配置，再提交。";
            AlertDialog.Builder builder = new AlertDialog.Builder(this)
                    .setTitle("提交前还差一步")
                    .setMessage(message)
                    .setPositiveButton("去配置", (dialog, which) -> showSettings());
            if (missing.size() < selectedPlatforms().size()) {
                builder.setNegativeButton("仅提交已配置平台", (dialog, which) -> performSubmission(urls));
            } else {
                builder.setNegativeButton("取消", null);
            }
            builder.show();
            return;
        }
        performSubmission(urls);
    }

    private void performSubmission(List<String> urls) {
        submitButton.setEnabled(false);
        refreshButton.setEnabled(false);
        results.setText("正在处理 " + urls.size() + " 条链接…");
        final boolean doIndexNow = indexNowCheck.isChecked();
        final boolean doBaidu = baiduCheck.isChecked();
        final boolean doBing = bingCheck.isChecked();
        final boolean doYandex = yandexCheck.isChecked();
        final Set<String> selectedPlatforms = selectedPlatforms();
        executor.execute(() -> {
            StringBuilder report = new StringBuilder();
            historyStore.recordSubmission(urls, selectedPlatforms);
            if (doIndexNow) submitIndexNow(urls, report);
            if (doBaidu) submitBaidu(urls, report);
            if (doBing) submitBing(urls, report);
            if (doYandex) submitYandex(urls, report);
            runOnUiThread(() -> {
                results.setText(report.length() == 0 ? "没有产生处理结果" : report.toString().trim());
                submitButton.setEnabled(true);
                refreshButton.setEnabled(true);
                renderHistory();
            });
        });
    }

    private List<String> missingSelectedConfigs() {
        List<String> missing = new ArrayList<>();
        if (indexNowCheck.isChecked() && prefs.getString("indexnow_key", "").trim().isEmpty()) {
            missing.add("IndexNow：生成 Key，并把 Key 文件放到网站根目录");
        }
        boolean hasBaidu = !prefs.getString("baidu_token", "").trim().isEmpty()
                || !prefs.getString("baidu_token_map", "").trim().isEmpty();
        if (baiduCheck.isChecked() && !hasBaidu) {
            missing.add("百度：登录搜索资源平台，复制站点 token");
        }
        if (bingCheck.isChecked() && prefs.getString("bing_key", "").trim().isEmpty()) {
            missing.add("Bing：登录 Webmaster Tools，生成 API Key");
        }
        if (yandexCheck.isChecked() && prefs.getString("yandex_token", "").trim().isEmpty()) {
            missing.add("Yandex：完成 OAuth 授权并粘贴 Token");
        }
        return missing;
    }

    private void updateConfigHint() {
        if (configHint == null) return;
        List<String> missing = missingSelectedConfigs();
        if (missing.isEmpty()) {
            configHint.setText("✓ 已选平台配置完成，可以直接提交");
            configHint.setTextColor(Color.rgb(22, 120, 92));
        } else {
            configHint.setText("还差 " + missing.size() + " 项配置 · 点这里按步骤完成");
            configHint.setTextColor(Color.rgb(23, 103, 212));
        }
    }

    private Set<String> selectedPlatforms() {
        Set<String> result = new LinkedHashSet<>();
        if (indexNowCheck.isChecked()) result.add("indexnow");
        if (baiduCheck.isChecked()) result.add("baidu");
        if (bingCheck.isChecked()) result.add("bing");
        if (yandexCheck.isChecked()) result.add("yandex");
        return result;
    }

    private void refreshHistory() {
        List<HistoryStore.Entry> entries = historyStore.list(200);
        if (entries.isEmpty()) {
            toast("暂无提交记录");
            return;
        }
        refreshButton.setEnabled(false);
        submitButton.setEnabled(false);
        results.setText("正在刷新历史收录状态…");
        String bingKey = prefs.getString("bing_key", "").trim();
        executor.execute(() -> {
            int indexed = 0;
            int checked = 0;
            for (HistoryStore.Entry entry : entries) {
                int state = HistoryStore.UNKNOWN;
                if (!bingKey.isEmpty()) {
                    try {
                        String origin = originOf(entry.url);
                        String checkUrl = "https://ssl.bing.com/webmaster/api.svc/json/GetUrlInfo?siteUrl="
                                + encode(origin + "/") + "&url=" + encode(entry.url) + "&apikey=" + encode(bingKey);
                        Response response = request("GET", checkUrl, null, null, null);
                        JSONObject record = response.code == 200 ? new JSONObject(response.body).optJSONObject("d") : null;
                        state = record != null && record.length() > 0 ? HistoryStore.INDEXED : HistoryStore.NOT_INDEXED;
                    } catch (Exception ignored) {
                        state = HistoryStore.UNKNOWN;
                    }
                }
                historyStore.updateIndexStatus(entry.url, "bing", state);
                if (state == HistoryStore.INDEXED) indexed++;
                checked++;
            }
            int finalIndexed = indexed;
            int finalChecked = checked;
            runOnUiThread(() -> {
                renderHistory();
                results.setText("历史刷新完成：检查 " + finalChecked + " 条，Bing 已确认收录 " + finalIndexed + " 条。其他平台需配置可用的官方查询授权。" );
                refreshButton.setEnabled(true);
                submitButton.setEnabled(true);
            });
        });
    }

    private void renderHistory() {
        if (historyContainer == null) return;
        historyContainer.removeAllViews();
        List<HistoryStore.Entry> entries = historyStore.list(100);
        if (entries.isEmpty()) {
            TextView empty = text("暂无记录。完成一次提交后，网址和平台状态会永久保存在这里。", 13, MUTED, false);
            empty.setPadding(dp(14), dp(14), dp(14), dp(14));
            empty.setBackground(rounded(FIELD, BORDER, 10));
            historyContainer.addView(empty);
            return;
        }
        for (HistoryStore.Entry entry : entries) {
            LinearLayout item = card();
            LinearLayout dateRow = horizontal();
            dateRow.addView(text(formatTime(entry.lastSubmitted), 13, MUTED, false), new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));
            dateRow.addView(text("提交 " + entry.submissionCount + " 次", 12, MUTED, false));
            item.addView(dateRow);
            TextView url = text(entry.url, 14, TEXT, true);
            url.setTextIsSelectable(true);
            item.addView(url, marginTop(6));
            LinearLayout badges = horizontal();
            badges.setPadding(0, dp(10), 0, 0);
            addBadge(badges, "G", "google", entry, Color.rgb(66, 133, 244));
            addBadge(badges, "百", "baidu", entry, Color.rgb(78, 110, 242));
            addBadge(badges, "B", "bing", entry, Color.rgb(0, 164, 239));
            addBadge(badges, "Y", "yandex", entry, Color.rgb(255, 75, 75));
            addBadge(badges, "360", "360", entry, Color.rgb(53, 199, 89));
            addBadge(badges, "神", "shenma", entry, Color.rgb(255, 122, 26));
            item.addView(badges);
            String checked = entry.lastChecked == null ? "尚未刷新" : "最近刷新 " + formatTime(entry.lastChecked);
            item.addView(text(checked, 11, MUTED, false), marginTop(8));
            historyContainer.addView(item, marginBottom(10));
        }
    }

    private void addBadge(LinearLayout row, String label, String platform, HistoryStore.Entry entry, int brandColor) {
        int state = entry.indexStatuses.containsKey(platform) ? entry.indexStatuses.get(platform) : HistoryStore.UNKNOWN;
        TextView badge = text(label, label.length() > 1 ? 10 : 13, state == HistoryStore.INDEXED ? Color.WHITE : Color.rgb(100, 116, 139), true);
        badge.setGravity(Gravity.CENTER);
        badge.setContentDescription(platform + (state == HistoryStore.INDEXED ? " 已收录" : " 未确认收录"));
        badge.setBackground(rounded(state == HistoryStore.INDEXED ? brandColor : Color.rgb(241, 245, 249),
                state == HistoryStore.NOT_INDEXED ? Color.rgb(225, 163, 62) : Color.rgb(203, 213, 225), 16));
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(dp(36), dp(32));
        if (row.getChildCount() > 0) params.setMarginStart(dp(8));
        row.addView(badge, params);
    }

    private String formatTime(long timestamp) {
        return new SimpleDateFormat("MM-dd HH:mm", Locale.getDefault()).format(new Date(timestamp));
    }

    private void submitIndexNow(List<String> urls, StringBuilder report) {
        String key = prefs.getString("indexnow_key", "").trim();
        if (key.isEmpty()) {
            line(report, "IndexNow", "跳过：请先配置 Key");
            return;
        }
        Map<String, List<String>> groups = groupByOrigin(urls);
        for (Map.Entry<String, List<String>> entry : groups.entrySet()) {
            try {
                URI origin = URI.create(entry.getKey());
                JSONObject body = new JSONObject();
                body.put("host", origin.getHost());
                body.put("key", key);
                body.put("urlList", new JSONArray(entry.getValue()));
                String location = prefs.getString("indexnow_location", "").trim();
                if (!location.isEmpty()) body.put("keyLocation", location);
                Response response = request("POST", "https://api.indexnow.org/indexnow", body.toString(), "application/json", null);
                String state = response.code == 200 || response.code == 202 ? "成功" : "失败 HTTP " + response.code;
                line(report, "IndexNow · " + origin.getHost(), state + "，" + entry.getValue().size() + " 条 URL");
            } catch (Exception error) {
                line(report, "IndexNow", "失败：" + shortError(error));
            }
        }
    }

    private void submitBaidu(List<String> urls, StringBuilder report) {
        Map<String, List<String>> groups = groupByOrigin(urls);
        Map<String, String> tokenMap = parseTokenMap(prefs.getString("baidu_token_map", ""));
        String defaultToken = prefs.getString("baidu_token", "").trim();
        for (Map.Entry<String, List<String>> entry : groups.entrySet()) {
            try {
                String host = URI.create(entry.getKey()).getHost().toLowerCase(Locale.ROOT);
                String token = tokenMap.containsKey(host) ? tokenMap.get(host) : defaultToken;
                if (token == null || token.isEmpty()) {
                    line(report, "百度 · " + host, "跳过：未配置该站点 token");
                    continue;
                }
                String endpoint = "https://data.zz.baidu.com/urls?site=" + encode(entry.getKey()) + "&token=" + encode(token);
                Response response = request("POST", endpoint, String.join("\n", entry.getValue()), "text/plain", null);
                if (response.code == 200) {
                    JSONObject data = new JSONObject(response.body.isEmpty() ? "{}" : response.body);
                    if (!data.has("error")) {
                        line(report, "百度 · " + host, "成功 " + data.optInt("success", entry.getValue().size()) + " 条，剩余 " + data.optString("remain", "未知"));
                        continue;
                    }
                    line(report, "百度 · " + host, "失败：" + data.optString("message", "API 拒绝请求"));
                } else {
                    line(report, "百度 · " + host, "失败 HTTP " + response.code);
                }
            } catch (Exception error) {
                line(report, "百度", "失败：" + shortError(error));
            }
        }
    }

    private void submitBing(List<String> urls, StringBuilder report) {
        String key = prefs.getString("bing_key", "").trim();
        if (key.isEmpty()) {
            line(report, "Bing", "跳过：请先配置 API Key");
            return;
        }
        Map<String, List<String>> groups = groupByOrigin(urls);
        for (Map.Entry<String, List<String>> entry : groups.entrySet()) {
            List<String> remaining = new ArrayList<>();
            int indexed = 0;
            for (String url : entry.getValue()) {
                try {
                    String checkUrl = "https://ssl.bing.com/webmaster/api.svc/json/GetUrlInfo?siteUrl="
                            + encode(entry.getKey() + "/") + "&url=" + encode(url) + "&apikey=" + encode(key);
                    Response check = request("GET", checkUrl, null, null, null);
                    if (check.code == 200) {
                        JSONObject record = new JSONObject(check.body).optJSONObject("d");
                        if (record != null && record.length() > 0) {
                            indexed++;
                            historyStore.updateIndexStatus(url, "bing", HistoryStore.INDEXED);
                        } else {
                            remaining.add(url);
                            historyStore.updateIndexStatus(url, "bing", HistoryStore.NOT_INDEXED);
                        }
                    } else {
                        remaining.add(url);
                    }
                } catch (Exception ignored) {
                    remaining.add(url);
                }
            }
            if (remaining.isEmpty()) {
                line(report, "Bing · " + hostOf(entry.getKey()), "查重：" + indexed + " 条已存在，无需提交");
                continue;
            }
            try {
                JSONObject body = new JSONObject();
                body.put("siteUrl", entry.getKey() + "/");
                body.put("urlList", new JSONArray(remaining));
                Response response = request("POST", "https://ssl.bing.com/webmaster/api.svc/json/SubmitUrlbatch?apikey=" + encode(key),
                        body.toString(), "application/json", null);
                line(report, "Bing · " + hostOf(entry.getKey()), (response.code == 200 ? "成功" : "失败 HTTP " + response.code)
                        + "；已收录 " + indexed + "，提交 " + remaining.size());
            } catch (Exception error) {
                line(report, "Bing", "失败：" + shortError(error));
            }
        }
    }

    private void submitYandex(List<String> urls, StringBuilder report) {
        String token = prefs.getString("yandex_token", "").trim();
        if (token.isEmpty()) {
            line(report, "Yandex", "跳过：请先配置 OAuth Token");
            return;
        }
        Map<String, String> headers = new LinkedHashMap<>();
        headers.put("Authorization", "OAuth " + token);
        try {
            Response user = request("GET", "https://api.webmaster.yandex.net/v4/user", null, null, headers);
            if (user.code != 200) {
                line(report, "Yandex", "读取用户失败 HTTP " + user.code);
                return;
            }
            long userId = new JSONObject(user.body).getLong("user_id");
            Response hostsResponse = request("GET", "https://api.webmaster.yandex.net/v4/user/" + userId + "/hosts", null, null, headers);
            JSONArray hosts = hostsResponse.code == 200 ? new JSONObject(hostsResponse.body).optJSONArray("hosts") : null;
            for (String origin : groupByOrigin(urls).keySet()) {
                JSONObject matched = null;
                if (hosts != null) {
                    for (int i = 0; i < hosts.length(); i++) {
                        JSONObject item = hosts.optJSONObject(i);
                        if (item != null && origin.equals(stripSlash(item.optString("ascii_host_url")))) {
                            matched = item;
                            break;
                        }
                    }
                }
                if (matched == null) {
                    line(report, "Yandex · " + hostOf(origin), "跳过：站点未验证或协议不匹配");
                    continue;
                }
                String hostId = encode(matched.getString("host_id"));
                String endpoint = "https://api.webmaster.yandex.net/v4/user/" + userId + "/hosts/" + hostId + "/sitemaps";
                JSONObject body = new JSONObject().put("url", origin + "/sitemap.xml");
                Response response = request("POST", endpoint, body.toString(), "application/json", headers);
                line(report, "Yandex · " + hostOf(origin), response.code >= 200 && response.code < 300 ? "Sitemap 提交成功" : "失败 HTTP " + response.code);
            }
        } catch (Exception error) {
            line(report, "Yandex", "失败：" + shortError(error));
        }
    }

    private void showSettings() {
        LinearLayout content = vertical();
        content.setPadding(dp(6), dp(4), dp(6), 0);
        TextView intro = text("不用填写账号密码。能授权的平台会打开官方页面；必须手动获取的 Key/token，请按按钮进入官方平台复制后粘贴。", 13, Color.DKGRAY, false);
        content.addView(intro);
        content.addView(externalLinkButton("查看完整新手配置教程", GUIDE_URL), marginTop(10));

        content.addView(text("IndexNow", 15, Color.DKGRAY, true), marginTop(14));
        content.addView(text("无需登录，但必须在每个自有网站根目录部署 Key 文件。", 12, Color.GRAY, false));
        EditText indexKey = settingField(content, "IndexNow Key", prefs.getString("indexnow_key", ""), true);
        EditText indexLocation = settingField(content, "IndexNow Key 文件 URL（可选）", prefs.getString("indexnow_location", ""), false);
        content.addView(externalLinkButton("打开 IndexNow 官方说明", "https://www.indexnow.org/documentation"), marginTop(6));

        content.addView(text("百度搜索", 15, Color.DKGRAY, true), marginTop(16));
        content.addView(text("百度目前不能由第三方 App 自动换取站点 token，请登录官方平台复制。", 12, Color.GRAY, false));
        EditText baiduToken = settingField(content, "百度默认 token", prefs.getString("baidu_token", ""), true);
        EditText baiduMap = settingField(content, "百度多站映射：域名=token，逗号分隔", prefs.getString("baidu_token_map", ""), true);
        content.addView(externalLinkButton("登录百度搜索资源平台", "https://ziyuan.baidu.com/linksubmit/index"), marginTop(6));

        content.addView(text("Bing", 15, Color.DKGRAY, true), marginTop(16));
        content.addView(text("登录官方站长平台后生成账号级 API Key。", 12, Color.GRAY, false));
        EditText bingKey = settingField(content, "Bing Webmaster API Key", prefs.getString("bing_key", ""), true);
        content.addView(externalLinkButton("登录 Bing Webmaster Tools", "https://www.bing.com/webmasters/home"), marginTop(6));

        content.addView(text("Yandex", 15, Color.DKGRAY, true), marginTop(16));
        content.addView(text("Yandex 支持 OAuth；当前通用版由用户创建授权并粘贴 Token。", 12, Color.GRAY, false));
        EditText yandexToken = settingField(content, "Yandex OAuth Token", prefs.getString("yandex_token", ""), true);
        content.addView(externalLinkButton("打开 Yandex OAuth", "https://oauth.yandex.com/client/new"), marginTop(6));

        content.addView(text("Google", 15, Color.DKGRAY, true), marginTop(16));
        content.addView(text("Google 可实现官方账号登录，但公开移动版需发行方先注册并审核 OAuth 应用。当前请使用桌面版 Google OAuth。", 12, Color.GRAY, false));
        content.addView(externalLinkButton("打开 Google Search Console", "https://search.google.com/search-console"), marginTop(6));

        TextView note = text("所有凭据只保存在本机应用私有空间。软件不会要求或保存平台密码。", 12, Color.DKGRAY, false);
        note.setPadding(0, dp(12), 0, dp(4));
        content.addView(note);

        ScrollView scroll = new ScrollView(this);
        scroll.addView(content);
        AlertDialog dialog = new AlertDialog.Builder(this)
                .setTitle("平台配置")
                .setView(scroll)
                .setNegativeButton("取消", null)
                .setPositiveButton("保存", null)
                .create();
        dialog.setOnShowListener(ignored -> dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(v -> {
            prefs.edit()
                    .putString("indexnow_key", indexKey.getText().toString().trim())
                    .putString("indexnow_location", indexLocation.getText().toString().trim())
                    .putString("baidu_token", baiduToken.getText().toString().trim())
                    .putString("baidu_token_map", baiduMap.getText().toString().trim())
                    .putString("bing_key", bingKey.getText().toString().trim())
                    .putString("yandex_token", yandexToken.getText().toString().trim())
                    .apply();
            toast("配置已保存到本机应用私有空间");
            updateConfigHint();
            dialog.dismiss();
        }));
        dialog.show();
    }

    private Button externalLinkButton(String label, String url) {
        Button button = new Button(this);
        button.setText(label);
        button.setAllCaps(false);
        button.setTextColor(Color.rgb(30, 90, 170));
        button.setOnClickListener(v -> startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(url))));
        return button;
    }

    private void showOnboardingIfNeeded() {
        if (prefs.getBoolean("onboarding_seen", false)) return;
        new AlertDialog.Builder(this)
                .setTitle("三步开始使用")
                .setMessage("1. 复制整段分享文案，粘贴后自动只保留链接。\n\n"
                        + "2. 只能提交您拥有或已验证的网站；第三方笔记链接可以提取，但站长 API 可能拒绝。\n\n"
                        + "3. 点击“账号与平台”，按提示完成 Key/token 配置。软件不会要求平台密码。")
                .setPositiveButton("我知道了", (dialog, which) -> prefs.edit().putBoolean("onboarding_seen", true).apply())
                .setNeutralButton("先看配置教程", (dialog, which) -> {
                    prefs.edit().putBoolean("onboarding_seen", true).apply();
                    startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(GUIDE_URL)));
                })
                .show();
    }

    private EditText settingField(LinearLayout parent, String label, String value, boolean secret) {
        TextView title = text(label, 13, Color.DKGRAY, true);
        parent.addView(title, marginTop(10));
        EditText field = new EditText(this);
        field.setText(value);
        field.setTextSize(14);
        field.setSingleLine(true);
        field.setPadding(dp(10), dp(8), dp(10), dp(8));
        if (secret) field.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_PASSWORD);
        parent.addView(field, marginTop(3));
        return field;
    }

    private Response request(String method, String url, String body, String contentType, Map<String, String> headers) throws Exception {
        HttpURLConnection connection = (HttpURLConnection) new java.net.URL(url).openConnection();
        connection.setRequestMethod(method);
        connection.setConnectTimeout(20_000);
        connection.setReadTimeout(25_000);
        connection.setRequestProperty("User-Agent", "SearchIndexSubmitter-Android/0.1");
        if (headers != null) for (Map.Entry<String, String> header : headers.entrySet()) connection.setRequestProperty(header.getKey(), header.getValue());
        if (body != null) {
            connection.setDoOutput(true);
            connection.setRequestProperty("Content-Type", contentType == null ? "application/json" : contentType);
            try (OutputStream output = connection.getOutputStream()) {
                output.write(body.getBytes(StandardCharsets.UTF_8));
            }
        }
        int code = connection.getResponseCode();
        InputStream stream = code >= 400 ? connection.getErrorStream() : connection.getInputStream();
        String responseBody = readStream(stream);
        connection.disconnect();
        return new Response(code, responseBody);
    }

    private String readStream(InputStream stream) throws Exception {
        if (stream == null) return "";
        ByteArrayOutputStream output = new ByteArrayOutputStream();
        byte[] buffer = new byte[4096];
        int read;
        while ((read = stream.read(buffer)) >= 0) output.write(buffer, 0, read);
        stream.close();
        return output.toString(StandardCharsets.UTF_8.name());
    }

    private Map<String, List<String>> groupByOrigin(List<String> urls) {
        Map<String, List<String>> groups = new LinkedHashMap<>();
        for (String url : urls) {
            try {
                URI uri = URI.create(url);
                String origin = uri.getScheme() + "://" + uri.getHost();
                if (uri.getPort() >= 0) origin += ":" + uri.getPort();
                groups.computeIfAbsent(origin, ignored -> new ArrayList<>()).add(url);
            } catch (Exception ignored) { }
        }
        return groups;
    }

    private Map<String, String> parseTokenMap(String value) {
        Map<String, String> result = new LinkedHashMap<>();
        for (String item : value.split("[\\n,，;；]+")) {
            int position = item.indexOf('=');
            if (position > 0) result.put(item.substring(0, position).trim().toLowerCase(Locale.ROOT), item.substring(position + 1).trim());
        }
        return result;
    }

    private String hostOf(String origin) {
        try { return URI.create(origin).getHost(); } catch (Exception ignored) { return origin; }
    }

    private String originOf(String url) {
        URI uri = URI.create(url);
        String origin = uri.getScheme() + "://" + uri.getHost();
        return uri.getPort() >= 0 ? origin + ":" + uri.getPort() : origin;
    }

    private String stripSlash(String value) {
        while (value.endsWith("/")) value = value.substring(0, value.length() - 1);
        return value;
    }

    private String encode(String value) throws Exception {
        return URLEncoder.encode(value, StandardCharsets.UTF_8.name());
    }

    private String shortError(Exception error) {
        String message = error.getMessage();
        return message == null || message.trim().isEmpty() ? error.getClass().getSimpleName() : message;
    }

    private void line(StringBuilder report, String provider, String message) {
        report.append('[').append(provider).append("] ").append(message).append('\n');
        runOnUiThread(() -> results.setText(report.toString().trim()));
    }

    private LinearLayout vertical() {
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        return layout;
    }

    private LinearLayout horizontal() {
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.HORIZONTAL);
        layout.setGravity(Gravity.CENTER_VERTICAL);
        return layout;
    }

    private LinearLayout card() {
        LinearLayout layout = vertical();
        layout.setPadding(dp(16), dp(14), dp(16), dp(16));
        layout.setBackground(rounded(CARD, BORDER, 14));
        return layout;
    }

    private TextView text(String value, int size, int color, boolean bold) {
        TextView view = new TextView(this);
        view.setText(value);
        view.setTextSize(size);
        view.setTextColor(color);
        if (bold) view.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        return view;
    }

    private Button button(String label, boolean primary) {
        Button button = new Button(this);
        button.setText(label);
        button.setAllCaps(false);
        button.setTextColor(primary ? Color.WHITE : Color.rgb(51, 65, 85));
        button.setBackground(rounded(primary ? BLUE : Color.rgb(238, 244, 251), primary ? BLUE : Color.rgb(203, 216, 232), 9));
        return button;
    }

    private void configureSystemBars() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            getWindow().setDecorFitsSystemWindows(false);
            getWindow().setStatusBarColor(Color.TRANSPARENT);
            getWindow().setNavigationBarColor(Color.TRANSPARENT);
            WindowInsetsController controller = getWindow().getInsetsController();
            if (controller != null) {
                controller.setSystemBarsAppearance(
                        WindowInsetsController.APPEARANCE_LIGHT_STATUS_BARS
                                | WindowInsetsController.APPEARANCE_LIGHT_NAVIGATION_BARS,
                        WindowInsetsController.APPEARANCE_LIGHT_STATUS_BARS
                                | WindowInsetsController.APPEARANCE_LIGHT_NAVIGATION_BARS);
            }
        } else {
            getWindow().setStatusBarColor(BG);
            getWindow().setNavigationBarColor(BG);
            getWindow().getDecorView().setSystemUiVisibility(
                    View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR | View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR);
        }
    }

    private void applySafeAreaInsets(View root) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.R) return;
        final int left = root.getPaddingLeft();
        final int top = root.getPaddingTop();
        final int right = root.getPaddingRight();
        final int bottom = root.getPaddingBottom();
        root.setOnApplyWindowInsetsListener((view, windowInsets) -> {
            android.graphics.Insets bars = windowInsets.getInsets(WindowInsets.Type.systemBars() | WindowInsets.Type.displayCutout());
            view.setPadding(left + bars.left, top + bars.top, right + bars.right, bottom + bars.bottom);
            return windowInsets;
        });
    }

    private CheckBox check(String label, boolean checked) {
        CheckBox box = new CheckBox(this);
        box.setText(label);
        box.setTextColor(TEXT);
        box.setTextSize(14);
        box.setChecked(checked);
        box.setPadding(0, dp(6), 0, dp(4));
        return box;
    }

    private GradientDrawable rounded(int fill, int stroke, int radius) {
        GradientDrawable drawable = new GradientDrawable();
        drawable.setColor(fill);
        drawable.setCornerRadius(dp(radius));
        drawable.setStroke(dp(1), stroke);
        return drawable;
    }

    private LinearLayout.LayoutParams matchWrap() {
        return new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
    }

    private LinearLayout.LayoutParams marginTop(int value) {
        LinearLayout.LayoutParams params = matchWrap();
        params.topMargin = dp(value);
        return params;
    }

    private LinearLayout.LayoutParams marginBottom(int value) {
        LinearLayout.LayoutParams params = matchWrap();
        params.bottomMargin = dp(value);
        return params;
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }

    private void toast(String message) {
        Toast.makeText(this, message, Toast.LENGTH_SHORT).show();
    }

    private static final class Response {
        final int code;
        final String body;

        Response(int code, String body) {
            this.code = code;
            this.body = body;
        }
    }
}
