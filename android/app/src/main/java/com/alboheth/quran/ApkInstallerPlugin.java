package com.alboheth.quran;

import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.os.Build;
import android.provider.Settings;

import androidx.core.content.FileProvider;

import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;

import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;

/**
 * Downloads the newest APK inside the app (with progress) and opens Android's installer for it.
 * The new APK is installed OVER the current app (same package, same signing key, higher versionCode), keeping the app's data.
 */
@CapacitorPlugin(name = "ApkInstaller")
public class ApkInstallerPlugin extends Plugin {
    private volatile boolean busy = false;

    @PluginMethod
    public void install(final PluginCall call) {
        final String url = call.getString("url");
        if (url == null || !url.startsWith("https://")) { call.reject("invalid url"); return; }
        if (busy) { call.reject("busy"); return; }
        busy = true;
        new Thread(() -> {
            try {
                File dir = new File(getContext().getCacheDir(), "apk");
                if (!dir.exists() && !dir.mkdirs()) throw new Exception("cannot create cache dir");
                File apk = new File(dir, "update.apk");
                download(url, apk);
                Context ctx = getContext();
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O && !ctx.getPackageManager().canRequestPackageInstalls()) {
                    // Android asks the user once to allow this app to install updates; the file stays downloaded
                    Intent s = new Intent(Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES, Uri.parse("package:" + ctx.getPackageName()));
                    s.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                    ctx.startActivity(s);
                    JSObject r = new JSObject(); r.put("status", "needs_permission"); call.resolve(r);
                    return;
                }
                Uri uri = FileProvider.getUriForFile(ctx, ctx.getPackageName() + ".fileprovider", apk);
                Intent i = new Intent(Intent.ACTION_VIEW);
                i.setDataAndType(uri, "application/vnd.android.package-archive");
                i.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_ACTIVITY_NEW_TASK);
                ctx.startActivity(i);
                JSObject r = new JSObject(); r.put("status", "installing"); call.resolve(r);
            } catch (Exception e) {
                call.reject(String.valueOf(e.getMessage()));
            } finally {
                busy = false;
            }
        }, "apk-download").start();
    }

    private void download(String urlStr, File out) throws Exception {
        HttpURLConnection c = (HttpURLConnection) new URL(urlStr).openConnection();
        c.setConnectTimeout(20000); c.setReadTimeout(30000); c.setInstanceFollowRedirects(true);
        try {
            int code = c.getResponseCode();
            if (code != 200) throw new Exception("download failed: HTTP " + code);
            long total = c.getContentLengthLong(), done = 0; int last = -1;
            File tmp = new File(out.getPath() + ".part");
            try (InputStream in = c.getInputStream(); FileOutputStream fo = new FileOutputStream(tmp)) {
                byte[] buf = new byte[64 * 1024]; int n;
                while ((n = in.read(buf)) > 0) {
                    fo.write(buf, 0, n); done += n;
                    if (total > 0) { int p = (int) (done * 100 / total); if (p != last) { last = p; JSObject e = new JSObject(); e.put("percent", p); notifyListeners("progress", e); } }
                }
            }
            if (total > 0 && tmp.length() != total) throw new Exception("incomplete download");
            if (out.exists() && !out.delete()) throw new Exception("cannot replace old file");
            if (!tmp.renameTo(out)) throw new Exception("cannot finish file");
        } finally { c.disconnect(); }
    }
}
