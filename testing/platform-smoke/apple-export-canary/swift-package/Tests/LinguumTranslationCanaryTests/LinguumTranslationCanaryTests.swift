// SPDX-License-Identifier: Apache-2.0
import Foundation
import LinguumTranslation
import XCTest

final class LinguumTranslationCanaryTests: XCTestCase {
    private static let iterations = 100
    private static let input = "¿Qué estás haciendo?"
    private static let expected = "What are you doing?"

    func testAsyncTranslationCanary() async throws {
        let fixtures = try XCTUnwrap(Bundle.module.resourceURL)
            .appendingPathComponent("Fixtures", isDirectory: true)
        let profile = try String(
            contentsOf: fixtures.appendingPathComponent("profile.txt"),
            encoding: .utf8
        ).trimmingCharacters(in: .whitespacesAndNewlines)
        emit(
            "LINGUUM_SWIFT_CANARY_START profile=\(profile) "
                + "iterations=\(Self.iterations) async=true"
        )
        let service = try await LinguumTranslationService.create(
            configuration: LinguumTranslationConfiguration(
                modelDirectory: fixtures.appendingPathComponent("Models").path,
                configurationPath: fixtures.appendingPathComponent("es-en.yml").path
            )
        )
        let pair = try LanguagePair(source: "es", target: "en")
        let translator = try await service.translator(pair: pair)
        for _ in 0..<Self.iterations {
            let result = try await translator.translate(text: Self.input)
            XCTAssertEqual(Self.expected, result.text)
        }
        service.close()
        service.close()
        do {
            _ = try await translator.translate(text: Self.input)
            XCTFail("translation after close must fail")
        } catch LinguumTranslationError.serviceClosed {
            // Expected typed error mapping.
        }
        emit(
            "LINGUUM_SWIFT_CANARY_PASS profile=\(profile) "
                + "iterations=\(Self.iterations) async=true abi=1.0"
        )
    }

    private func emit(_ value: String) {
        FileHandle.standardError.write(Data("\(value)\n".utf8))
    }
}
