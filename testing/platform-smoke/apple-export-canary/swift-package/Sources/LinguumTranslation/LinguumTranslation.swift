// SPDX-License-Identifier: Apache-2.0
import Foundation
import LinguumTranslationCore

public enum LinguumTranslationError: Error, Equatable, Sendable {
    case invalidConfiguration
    case unsupportedLanguagePair
    case serviceClosed
    case translationFailed(String)
}

public struct LinguumTranslationConfiguration: Equatable, Sendable {
    public let modelDirectory: String
    public let configurationPath: String

    public init(modelDirectory: String, configurationPath: String) {
        self.modelDirectory = modelDirectory
        self.configurationPath = configurationPath
    }
}

public struct LanguagePair: Equatable, Sendable {
    public let source: String
    public let target: String

    public init(source: String, target: String) throws {
        guard !source.isEmpty, !target.isEmpty, source != target else {
            throw LinguumTranslationError.unsupportedLanguagePair
        }
        self.source = source
        self.target = target
    }
}

public struct TranslationResult: Equatable, Sendable {
    public let text: String

    public init(text: String) {
        self.text = text
    }
}

public final class LinguumTranslationService: @unchecked Sendable {
    private let core: LinguumTranslationCoreService
    private var closed = false

    private init(core: LinguumTranslationCoreService) {
        self.core = core
    }

    public static func create(
        configuration: LinguumTranslationConfiguration
    ) async throws -> LinguumTranslationService {
        guard !configuration.modelDirectory.isEmpty,
              !configuration.configurationPath.isEmpty else {
            throw LinguumTranslationError.invalidConfiguration
        }
        let core = LinguumTranslationCoreService(
            modelDirectory: configuration.modelDirectory,
            configurationPath: configuration.configurationPath
        )
        return LinguumTranslationService(core: core)
    }

    public func translator(pair: LanguagePair) async throws -> Translator {
        guard !closed else {
            throw LinguumTranslationError.serviceClosed
        }
        guard core.supportsLanguagePair(source: pair.source, target: pair.target) else {
            throw LinguumTranslationError.unsupportedLanguagePair
        }
        return Translator(core: core)
    }

    public func close() {
        if !closed {
            closed = true
            core.close()
        }
    }
}

public final class Translator: @unchecked Sendable {
    private let core: LinguumTranslationCoreService

    fileprivate init(core: LinguumTranslationCoreService) {
        self.core = core
    }

    public func translate(text: String) async throws -> TranslationResult {
        try Task.checkCancellation()
        return try await withCheckedThrowingContinuation { continuation in
            let outcome = core.translateText(text: text)
            switch Int(outcome.errorCode) {
            case 0:
                if let translated = outcome.text {
                    continuation.resume(returning: TranslationResult(text: translated))
                } else {
                    continuation.resume(
                        throwing: LinguumTranslationError.translationFailed("missing result")
                    )
                }
            case 1:
                continuation.resume(throwing: LinguumTranslationError.serviceClosed)
            default:
                continuation.resume(
                    throwing: LinguumTranslationError.translationFailed(
                        outcome.errorMessage ?? "translation failed"
                    )
                )
            }
        }
    }
}
