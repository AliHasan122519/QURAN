package com.alboheth.quran;

import android.os.Bundle;

import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {
    @Override
    public void onCreate(Bundle savedInstanceState) {
        registerPlugin(ApkInstallerPlugin.class);   // in-app APK update (download + install prompt)
        super.onCreate(savedInstanceState);
    }
}
