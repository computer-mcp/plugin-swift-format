// swift-tools-version: 6.2

import PackageDescription

let package = Package(
  name: "swift-format-plugin",
  platforms: [.macOS(.v14)],
  products: [.executable(name: "export-swift-format-tree", targets: ["ExportSwiftFormatTree"])],
  dependencies: [
    .package(url: "https://github.com/apple/swift-argument-parser", exact: "1.8.2")
  ],
  targets: [
    .executableTarget(
      name: "ExportSwiftFormatTree",
      dependencies: [
        .product(name: "ArgumentParser", package: "swift-argument-parser")
      ]),
    .testTarget(
      name: "ExportSwiftFormatTreeTests", dependencies: ["ExportSwiftFormatTree"],
      resources: [.copy("Fixtures")]),
  ])
