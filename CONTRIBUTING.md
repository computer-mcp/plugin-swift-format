# Contributing

Changes belong to the artifact that owns their behavior. Describe the observable
change and include focused regression evidence. Preserve user configuration,
external dependencies and credentials.

## Validation

CI runs these checks; run them before opening a pull request:

```sh
swift package resolve && git diff --exit-code -- Package.resolved
swift format lint --strict --recursive --configuration .swift-format Package.swift Sources Tests
swift test --disable-automatic-resolution
swift build -c release --disable-automatic-resolution
python3 -m unittest discover -s Tests -p 'test_*.py'
python3 Scripts/build_package.py OUTPUT_DIRECTORY
```

CI also repeats the Python tests and package build on Python 3.11, and runs the organization brand check. Exercise help, valid input and invalid input from outside the checkout. Keep command output contracts and generated resources covered by tests.

## Documentation

The [documentation index](Documentation/README.md) links current architecture
and reference material. Agent work routes live in AGENTS.md; public usage lives
in the root README. GitHub collaboration files belong in .github/ and contributor
policy belongs in root governance files.
