// swift-tools-version: 6.0
// SPDX-License-Identifier: Apache-2.0
import PackageDescription

let package = Package(
    name: "LinguumTranslationFeasibility",
    platforms: [
        .iOS(.v15),
    ],
    products: [
        .library(name: "LinguumTranslation", targets: ["LinguumTranslation"]),
    ],
    targets: [
        .binaryTarget(
            name: "LinguumTranslationCore",
            path: "Binary/LinguumTranslation.xcframework"
        ),
        .target(
            name: "LinguumTranslation",
            dependencies: ["LinguumTranslationCore"],
            linkerSettings: [
                .linkedLibrary("iconv"),
            ]
        ),
        .testTarget(
            name: "LinguumTranslationCanaryTests",
            dependencies: ["LinguumTranslation"],
            resources: [.copy("Fixtures")]
        ),
    ],
    swiftLanguageModes: [.v5]
)
