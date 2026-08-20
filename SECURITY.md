# Security policy

## Reporting a vulnerability

Please report vulnerabilities privately through [GitHub private vulnerability reporting](https://github.com/StevenBuglione/linguum-translation/security/advisories/new). Do not open a public issue for suspected vulnerabilities, model-integrity failures, native memory-safety findings, or release credential exposure.

Include the affected commit/version, platform and architecture, reproduction steps, expected and observed behavior, and whether translation content or secrets may have been exposed. Never attach real user translation text, credentials, signing material, or private model URLs.

## Supported versions

No production version has been released. Security support begins with the first published release candidate and will be documented here before publication.

## Response principles

- Triage and coordinate disclosure privately.
- Preserve a safe regression input when appropriate.
- Never weaken sanitizer, fuzz, integrity, source-identity, or provenance gates to ship a fix.
- Use the protected Firefox compatibility workflow for upstream changes.
- Publish advisories and signed replacement artifacts only after required verification.
