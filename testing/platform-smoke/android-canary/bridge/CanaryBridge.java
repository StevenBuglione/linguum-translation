// SPDX-License-Identifier: Apache-2.0
package io.linguum.translation.internal.android;

/** M1-only JNI feasibility bridge. This is not a production Android API. */
public final class CanaryBridge {
    static {
        System.loadLibrary("linguum_translation_jni");
    }

    private CanaryBridge() {}

    public static String runCanary(String modelDirectory, String configurationYaml, int iterations) {
        if (modelDirectory == null || configurationYaml == null) {
            throw new IllegalArgumentException("modelDirectory and configurationYaml are required");
        }
        if (iterations < 1 || iterations > 100) {
            throw new IllegalArgumentException("iterations must be between 1 and 100");
        }
        return nativeRunCanary(modelDirectory, configurationYaml, iterations);
    }

    private static native String nativeRunCanary(
            String modelDirectory,
            String configurationYaml,
            int iterations);
}
