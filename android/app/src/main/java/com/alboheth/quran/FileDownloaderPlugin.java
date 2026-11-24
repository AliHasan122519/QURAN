package com.alboheth.quran;

import android.app.DownloadManager;
import android.content.ContentResolver;
import android.content.ContentValues;
import android.content.Context;
import android.net.Uri;
import android.os.Build;
import android.os.Environment;
import android.provider.MediaStore;

import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;

import java.io.File;
import java.io.FileOutputStream;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;

/**
 * Saves a book on the phone from inside the app: `download` hands a file to Android's DownloadManager (it downloads in the background, shows a notification and puts the file in
 * «Downloads»), `saveText` writes a text the app made (the text of a book) into «Downloads». Nothing opens in a browser. From Android 10 no permission is needed;
 * before that the file goes to the app's own Downloads folder (also without a permission).
 */
@CapacitorPlugin(name = "FileDownloader")
public class FileDownloaderPlugin extends Plugin {

    /** a safe file name: no path separators or characters the file systems refuse */
    private static String safe(String name, String fallback) {
        if (name == null) return fallback;
        String n = name.replaceAll("[\\\\/:*?\"<>|\\r\\n]", " ").replaceAll("\\s+", " ").trim();
        if (n.length() > 120) n = n.substring(0, 120).trim();
        return n.isEmpty() ? fallback : n;
    }

    @PluginMethod
    public void download(final PluginCall call) {
        final String url = call.getString("url");
        if (url == null || !url.startsWith("https://")) { call.reject("invalid url"); return; }
        final String name = safe(call.getString("filename"), "book.pdf");
        try {
            Context ctx = getContext();
            DownloadManager dm = (DownloadManager) ctx.getSystemService(Context.DOWNLOAD_SERVICE);
            if (dm == null) { call.reject("no download manager"); return; }
            DownloadManager.Request r = new DownloadManager.Request(Uri.parse(url));
            r.setTitle(name);
            r.setDescription("الباحث القرآني");
            r.setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED);
            r.setAllowedOverMetered(true);
            r.setAllowedOverRoaming(true);
            String mime = call.getString("mime");
            if (mime != null && !mime.isEmpty()) r.setMimeType(mime);
            if (Build.VERSION.SDK_INT >= 29) r.setDestinationInExternalPublicDir(Environment.DIRECTORY_DOWNLOADS, name);
            else r.setDestinationInExternalFilesDir(ctx, Environment.DIRECTORY_DOWNLOADS, name);
            long id = dm.enqueue(r);
            JSObject o = new JSObject();
            o.put("status", "started");
            o.put("id", id);
            o.put("where", Build.VERSION.SDK_INT >= 29 ? "downloads" : "app");
            call.resolve(o);
        } catch (Exception e) {
            call.reject(String.valueOf(e.getMessage()));
        }
    }

    @PluginMethod
    public void saveText(final PluginCall call) {
        final String text = call.getString("text");
        if (text == null) { call.reject("no text"); return; }
        final String name = safe(call.getString("filename"), "book.txt");
        new Thread(() -> {
            try {
                byte[] bytes = text.getBytes(StandardCharsets.UTF_8);
                Context ctx = getContext();
                String where;
                if (Build.VERSION.SDK_INT >= 29) {
                    ContentResolver cr = ctx.getContentResolver();
                    ContentValues v = new ContentValues();
                    v.put(MediaStore.MediaColumns.DISPLAY_NAME, name);
                    v.put(MediaStore.MediaColumns.MIME_TYPE, "text/plain");
                    v.put(MediaStore.MediaColumns.RELATIVE_PATH, Environment.DIRECTORY_DOWNLOADS);
                    Uri u = cr.insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, v);
                    if (u == null) throw new Exception("cannot create the file");
                    try (OutputStream os = cr.openOutputStream(u)) {
                        if (os == null) throw new Exception("cannot open the file");
                        os.write(bytes);
                    }
                    where = "downloads";
                } else {
                    File dir = ctx.getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS);
                    if (dir == null) dir = ctx.getFilesDir();
                    if (!dir.exists() && !dir.mkdirs()) throw new Exception("cannot create the folder");
                    try (FileOutputStream fo = new FileOutputStream(new File(dir, name))) { fo.write(bytes); }
                    where = "app";
                }
                JSObject o = new JSObject();
                o.put("status", "saved");
                o.put("where", where);
                call.resolve(o);
            } catch (Exception e) {
                call.reject(String.valueOf(e.getMessage()));
            }
        }, "save-text").start();
    }
}
