package com.alboheth.quran;

import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.content.pm.Signature;
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
                check(ctx, apk);                                  // a file the phone itself cannot read, or one that cannot replace this app, is refused here with its real reason
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

    /** Reads the downloaded APK the way the system installer will (PackageManager) and compares it with the installed app:
     *  invalid_package = the phone cannot parse the file (cut download, wrong file); signature_mismatch = signed with another key; not_newer = not a newer version. */
    private void check(Context ctx, File apk) throws Exception {
        if (apk.length() < 1000000) throw new Exception("invalid_package");
        try (java.io.FileInputStream in = new java.io.FileInputStream(apk)) {
            byte[] m = new byte[4];
            if (in.read(m) != 4 || m[0] != 'P' || m[1] != 'K' || m[2] != 3 || m[3] != 4) throw new Exception("invalid_package");
        }
        PackageManager pm = ctx.getPackageManager();
        boolean p28 = Build.VERSION.SDK_INT >= 28;
        int flags = p28 ? PackageManager.GET_SIGNING_CERTIFICATES : PackageManager.GET_SIGNATURES;
        PackageInfo ni = pm.getPackageArchiveInfo(apk.getAbsolutePath(), flags);
        if (ni == null) throw new Exception("invalid_package");
        if (!ctx.getPackageName().equals(ni.packageName)) throw new Exception("invalid_package");
        PackageInfo cur = pm.getPackageInfo(ctx.getPackageName(), flags);
        long nv = p28 ? ni.getLongVersionCode() : ni.versionCode, cv = p28 ? cur.getLongVersionCode() : cur.versionCode;
        if (nv <= cv) throw new Exception("not_newer");
        Signature[] a = signers(ni, p28), b = signers(cur, p28);
        if (a != null && b != null && a.length > 0 && b.length > 0) {      // only when both are known: never refuse on a doubt
            boolean same = false;
            for (Signature x : a) for (Signature y : b) if (x.equals(y)) same = true;
            if (!same) throw new Exception("signature_mismatch");
        }
    }

    private static Signature[] signers(PackageInfo info, boolean p28) {
        if (p28) return info.signingInfo == null ? null : info.signingInfo.getApkContentsSigners();
        return info.signatures;
    }

    private void download(String urlStr, File out) throws Exception {
        HttpURLConnection c = (HttpURLConnection) new URL(urlStr).openConnection();
        c.setConnectTimeout(20000); c.setReadTimeout(30000); c.setInstanceFollowRedirects(true);
        c.setRequestProperty("Accept-Encoding", "identity");             // the file as it is: no transparent compression that would change the length
        c.setRequestProperty("User-Agent", "AlboheathQuran");
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
