package com.jackeycloud.searchindexsubmitter;

import android.content.ContentValues;
import android.content.Context;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.database.sqlite.SQLiteOpenHelper;

import org.json.JSONArray;
import org.json.JSONObject;

import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;

public final class HistoryStore extends SQLiteOpenHelper {
    public static final int UNKNOWN = -1;
    public static final int NOT_INDEXED = 0;
    public static final int INDEXED = 1;
    private static final String DATABASE_NAME = "submission_history.db";
    private static final int DATABASE_VERSION = 1;

    public HistoryStore(Context context) {
        super(context, DATABASE_NAME, null, DATABASE_VERSION);
    }

    @Override
    public void onCreate(SQLiteDatabase database) {
        database.execSQL(
                "CREATE TABLE history (" +
                        "url TEXT PRIMARY KEY," +
                        "first_submitted INTEGER NOT NULL," +
                        "last_submitted INTEGER NOT NULL," +
                        "submission_count INTEGER NOT NULL DEFAULT 1," +
                        "submitted_platforms TEXT NOT NULL DEFAULT '[]'," +
                        "index_statuses TEXT NOT NULL DEFAULT '{}'," +
                        "last_checked INTEGER)"
        );
    }

    @Override
    public void onUpgrade(SQLiteDatabase database, int oldVersion, int newVersion) {
        // Additive migrations will be introduced with future schema versions.
    }

    public synchronized void recordSubmission(List<String> urls, Set<String> platforms) {
        SQLiteDatabase database = getWritableDatabase();
        long now = System.currentTimeMillis();
        database.beginTransaction();
        try {
            for (String url : urls) {
                Entry existing = find(database, url);
                Set<String> merged = new LinkedHashSet<>();
                if (existing != null) merged.addAll(existing.submittedPlatforms);
                merged.addAll(platforms);
                ContentValues values = new ContentValues();
                values.put("url", url);
                values.put("first_submitted", existing == null ? now : existing.firstSubmitted);
                values.put("last_submitted", now);
                values.put("submission_count", existing == null ? 1 : existing.submissionCount + 1);
                values.put("submitted_platforms", new JSONArray(merged).toString());
                values.put("index_statuses", existing == null ? "{}" : toJson(existing.indexStatuses));
                if (existing != null && existing.lastChecked != null) values.put("last_checked", existing.lastChecked);
                database.insertWithOnConflict("history", null, values, SQLiteDatabase.CONFLICT_REPLACE);
            }
            database.setTransactionSuccessful();
        } finally {
            database.endTransaction();
        }
    }

    public synchronized void updateIndexStatus(String url, String platform, int status) {
        SQLiteDatabase database = getWritableDatabase();
        Entry existing = find(database, url);
        if (existing == null) return;
        if (status != UNKNOWN) existing.indexStatuses.put(platform, status);
        ContentValues values = new ContentValues();
        values.put("index_statuses", toJson(existing.indexStatuses));
        values.put("last_checked", System.currentTimeMillis());
        database.update("history", values, "url = ?", new String[]{url});
    }

    public synchronized List<Entry> list(int limit) {
        List<Entry> results = new ArrayList<>();
        try (Cursor cursor = getReadableDatabase().query(
                "history", null, null, null, null, null,
                "last_submitted DESC", Integer.toString(limit))) {
            while (cursor.moveToNext()) results.add(fromCursor(cursor));
        }
        return results;
    }

    private Entry find(SQLiteDatabase database, String url) {
        try (Cursor cursor = database.query("history", null, "url = ?", new String[]{url}, null, null, null, "1")) {
            return cursor.moveToFirst() ? fromCursor(cursor) : null;
        }
    }

    private Entry fromCursor(Cursor cursor) {
        String submittedJson = cursor.getString(cursor.getColumnIndexOrThrow("submitted_platforms"));
        String statusesJson = cursor.getString(cursor.getColumnIndexOrThrow("index_statuses"));
        Set<String> submitted = new LinkedHashSet<>();
        java.util.Map<String, Integer> statuses = new java.util.LinkedHashMap<>();
        try {
            JSONArray array = new JSONArray(submittedJson);
            for (int i = 0; i < array.length(); i++) submitted.add(array.optString(i));
        } catch (Exception ignored) { }
        try {
            JSONObject object = new JSONObject(statusesJson);
            JSONArray names = object.names();
            if (names != null) {
                for (int i = 0; i < names.length(); i++) {
                    String name = names.optString(i);
                    statuses.put(name, object.optInt(name, UNKNOWN));
                }
            }
        } catch (Exception ignored) { }
        int checkedIndex = cursor.getColumnIndexOrThrow("last_checked");
        Long checked = cursor.isNull(checkedIndex) ? null : cursor.getLong(checkedIndex);
        return new Entry(
                cursor.getString(cursor.getColumnIndexOrThrow("url")),
                cursor.getLong(cursor.getColumnIndexOrThrow("first_submitted")),
                cursor.getLong(cursor.getColumnIndexOrThrow("last_submitted")),
                cursor.getInt(cursor.getColumnIndexOrThrow("submission_count")),
                submitted,
                statuses,
                checked
        );
    }

    private String toJson(java.util.Map<String, Integer> statuses) {
        return new JSONObject(statuses).toString();
    }

    public static final class Entry {
        public final String url;
        public final long firstSubmitted;
        public final long lastSubmitted;
        public final int submissionCount;
        public final Set<String> submittedPlatforms;
        public final java.util.Map<String, Integer> indexStatuses;
        public final Long lastChecked;

        Entry(String url, long firstSubmitted, long lastSubmitted, int submissionCount,
              Set<String> submittedPlatforms, java.util.Map<String, Integer> indexStatuses, Long lastChecked) {
            this.url = url;
            this.firstSubmitted = firstSubmitted;
            this.lastSubmitted = lastSubmitted;
            this.submissionCount = submissionCount;
            this.submittedPlatforms = submittedPlatforms;
            this.indexStatuses = indexStatuses;
            this.lastChecked = lastChecked;
        }
    }
}
