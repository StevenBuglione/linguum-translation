// SPDX-License-Identifier: Apache-2.0
package io.linguum.translation.canary;

import android.app.Activity;
import android.os.Build;
import android.os.Bundle;
import android.os.Process;
import android.util.Log;
import io.linguum.translation.internal.android.CanaryBridge;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;

/** Headless M1 feasibility consumer that executes the exact native lifecycle. */
public final class CanaryActivity extends Activity {
    private static final String TAG = "LinguumAndroidCanary";
    private static final String START = "LINGUUM_ANDROID_CANARY_START";
    private static final String PASS = "LINGUUM_ANDROID_CANARY_PASS";
    private static final String FAIL = "LINGUUM_ANDROID_CANARY_FAIL";
    private static final String[] MODEL_ASSETS = {
        "model.esen.intgemm.alphas.bin",
        "lex.50.50.esen.s2t.bin",
        "vocab.esen.spm"
    };

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        final int iterations = getIntent().getIntExtra("iterations", 100);
        final String runToken = runToken();
        Log.i(TAG, START + " runToken=" + runToken + " iterations=" + iterations
                + " sdk=" + Build.VERSION.SDK_INT
                + " primaryAbi=" + Build.SUPPORTED_ABIS[0]
                + " osArch=" + System.getProperty("os.arch")
                + " is64Bit=" + Process.is64Bit());
        new Thread(() -> runCanary(iterations, runToken), "linguum-android-canary").start();
    }

    private String runToken() {
        String value = getIntent().getStringExtra("runToken");
        if (value == null) {
            return "test-lab";
        }
        if (!value.matches("[a-f0-9]{32}")) {
            throw new IllegalArgumentException("invalid canary run token");
        }
        return value;
    }

    private void runCanary(int iterations, String runToken) {
        try {
            File modelDirectory = new File(getFilesDir(), "es-en-v2.0");
            if (!modelDirectory.isDirectory() && !modelDirectory.mkdirs()) {
                throw new IOException("could not create model directory");
            }
            for (String asset : MODEL_ASSETS) {
                copyAsset(asset, new File(modelDirectory, asset));
            }
            String configuration = readAsset("es-en.yml");
            String result = CanaryBridge.runCanary(
                    modelDirectory.getAbsolutePath(), configuration, iterations);
            String expected = "canary lifecycle PASS: " + iterations + " iterations, ABI 1.0";
            if (!expected.equals(result)) {
                throw new IllegalStateException("unexpected native canary result: " + result);
            }
            Log.i(TAG, PASS + " runToken=" + runToken + " " + result);
        } catch (Throwable failure) {
            Log.e(TAG, FAIL + " runToken=" + runToken, failure);
        } finally {
            runOnUiThread(this::finish);
        }
    }

    private void copyAsset(String name, File destination) throws IOException {
        try (InputStream input = getAssets().open(name);
             FileOutputStream output = new FileOutputStream(destination, false)) {
            byte[] buffer = new byte[64 * 1024];
            int count;
            while ((count = input.read(buffer)) != -1) {
                output.write(buffer, 0, count);
            }
            output.getFD().sync();
        }
    }

    private String readAsset(String name) throws IOException {
        try (InputStream input = getAssets().open(name)) {
            byte[] buffer = new byte[16 * 1024];
            int length = 0;
            while (length < buffer.length) {
                int count = input.read(buffer, length, buffer.length - length);
                if (count == -1) {
                    return new String(buffer, 0, length, StandardCharsets.UTF_8);
                }
                length += count;
            }
            if (input.read() != -1) {
                throw new IOException("configuration asset is too large");
            }
            return new String(buffer, StandardCharsets.UTF_8);
        }
    }
}
