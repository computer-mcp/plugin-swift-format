import ArgumentParser
import Darwin
import Foundation

@main
struct ExportCommand: ParsableCommand {
  static let configuration = CommandConfiguration(
    commandName: "export-swift-format-tree",
    abstract: "Export a verified Swift Format CLI Tree from native JSON on stdin.",
    discussion:
      "Supports Swift Format 6.3.1. Writes atomically after validation. Does not execute or install swift-format. Failures are JSON on stderr."
  )

  @Option(name: .long, help: "Version reported by the source swift-format executable.")
  var executableVersion: String

  @Option(name: .long, help: "Destination CLI Tree JSON file.")
  var output: String

  mutating func validate() throws {
    guard !output.isEmpty else { throw ValidationError("--output must not be empty.") }
  }

  mutating func run() throws {
    var data = Data()
    while data.count <= TreeExport.maximumInputBytes {
      let chunk =
        try FileHandle.standardInput.read(
          upToCount: min(65_536, TreeExport.maximumInputBytes + 1 - data.count)) ?? Data()
      if chunk.isEmpty { break }
      data.append(chunk)
    }
    let tree = try TreeExport.generate(native: data, version: executableVersion)
    try tree.write(to: URL(fileURLWithPath: output), options: .atomic)
  }

  static func main() {
    var command: any ParsableCommand
    do {
      command = try parseAsRoot()
    } catch {
      if exitCode(for: error) == .success { exit(withError: error) }
      fail(ExportError.invalidArguments)
    }
    do { try command.run() } catch {
      if exitCode(for: error) == .success { exit(withError: error) }
      fail(error)
    }
  }

  private static func fail(_ error: any Error) -> Never {
    let message = (error as? ExportError)?.rawValue ?? "Could not read input or write the tree."
    let failure: [String: Any] = ["ok": false, "error": ["message": message]]
    if let data = try? JSONSerialization.data(withJSONObject: failure, options: [.sortedKeys]) {
      try? FileHandle.standardError.write(contentsOf: data + Data("\n".utf8))
    }
    Darwin.exit(1)
  }
}
