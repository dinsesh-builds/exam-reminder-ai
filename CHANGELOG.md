# Changelog

All notable changes to this project are documented here.

## [Unreleased]

### Added
- Paper, Ink and Slate themes built on one semantic token set.
- Copy questions, Export for Anki (TSV) and Print or save as PDF.
- Answer span, source phrase and Bloom level on each question.
- Scanned PDF OCR fallback and strict upload validation.

### Fixed
- Escaped all rendered note text, closing a stored XSS path.
- Replaced the false AI claim with an accurate rule based description.
- Bad input now returns 400 instead of 500.
