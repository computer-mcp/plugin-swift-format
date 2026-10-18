import Foundation
import Testing

@testable import ExportSwiftFormatTree

struct TreeExportTests {
  @Test
  func completeObservedInventoryAndExplicitCoverage() throws {
    let tree = try document()
    #expect(tree["coverage"] as? String == "partial")
    #expect(tree["executable_version"] as? String == "6.3.1")
    let checks = try #require(tree["executable_checks"] as? [[String: Any]])
    #expect(checks.count == 2)
    #expect(checks[0]["args"] as? [String] == ["--version"])
    #expect(checks[0]["stdout"] as? String == "6.3.1\n")
    #expect(checks[1]["args"] as? [String] == ["--experimental-dump-help"])
    #expect(checks[1]["stdout_sha256"] as? String == TreeExport.nativeSHA256)
    let nodes = try #require(tree["commands"] as? [[String: Any]])
    #expect(
      nodes.compactMap { $0["id"] as? String } == [
        "root", "dump_configuration", "format", "lint", "help",
      ])
    #expect(
      nodes.compactMap { $0["path"] as? [String] } == [
        [], ["dump-configuration"], ["format"], ["lint"], ["help"],
      ])
    #expect(
      try TreeExport.generate(native: fixture(), version: "6.3.1")
        == TreeExport.generate(native: fixture(), version: "6.3.1"))
  }

  @Test(arguments: ["root", "format", "lint"])
  func sourceAndInverseFlagHaveOneMapping(_ id: String) throws {
    let node = try node(id)
    let parameters = try #require(node["parameters"] as? [[String: Any]])
    let argv = try #require(node["argv"] as? [[String: Any]])
    #expect(parameters.filter { $0["name"] as? String == "color_diagnostics" }.count == 1)
    #expect(parameters.allSatisfy { $0["name"] as? String != "no_color_diagnostics" })
    let color = try #require(parameters.first { $0["name"] as? String == "color_diagnostics" })
    #expect(color["default"] == nil)
    #expect(
      argv.first { $0["parameter"] as? String == "color_diagnostics" }?["inverse"] as? String
        == "--no-color-diagnostics")
    #expect((node["stdin"] as? [String: String]) == ["parameter": "source", "encoding": "utf8"])
    #expect(argv.suffix(2).first?["value"] as? String == "--")
    #expect(argv.last?["parameter"] as? String == "paths")
    #expect(Set(parameters.compactMap { $0["name"] as? String }).count == parameters.count)
  }

  @Test(arguments: ["root", "format", "lint"])
  func allNativeArgumentsAreAccountedFor(_ id: String) throws {
    let native = try JSONDecoder().decode(NativeInterface.self, from: fixture())
    let command = try #require(
      native.command.subcommands?.first { $0.commandName == (id == "root" ? "format" : id) })
    let parameters = try #require(node(id)["parameters"] as? [[String: Any]])
    var expected = Set(
      (command.arguments ?? []).map { $0.valueName.replacingOccurrences(of: "-", with: "_") })
    expected.remove("no_color_diagnostics")
    expected.insert("source")
    if id == "root" { expected.insert("version") }
    #expect(Set(parameters.compactMap { $0["name"] as? String }) == expected)
    #expect(parameters.contains { $0["name"] as? String == "debug_disable_pretty_print" })
    #expect(parameters.contains { $0["name"] as? String == "debug_dump_token_stream" })
  }

  @Test
  func repeatedOptionsAndConfigurationDependency() throws {
    let format = try node("format")
    let parameters = try #require(format["parameters"] as? [[String: Any]])
    let offsets = try #require(parameters.first { $0["name"] as? String == "offsets" })
    #expect((offsets["schema"] as? [String: Any])?["type"] as? String == "array")
    #expect(offsets["default"] as? [String] == [])
    #expect(
      (format["argv"] as? [[String: Any]])?.first { $0["parameter"] as? String == "offsets" }?[
        "style"] as? String == "equals")
    let dump = try node("dump_configuration")
    #expect(
      (dump["parameters"] as? [[String: Any]])?.first { $0["name"] as? String == "configuration" }?[
        "requires"] as? [String] == ["effective"])
    #expect(dump["output_schema"] == nil)
    #expect(dump["dry_run_parameter"] == nil)
  }

  @Test(arguments: ["", "6.3", "6.3.2", "6.4.0", "credential-must-not-echo"])
  func unknownVersionsFailClosed(_ version: String) throws {
    #expect(throws: ExportError.unsupportedVersion) {
      try TreeExport.generate(native: fixture(), version: version)
    }
  }

  @Test(arguments: ["empty", "truncated", "modified", "oversized"])
  func driftDoesNotGenerateAPlausibleTree(_ kind: String) throws {
    let data: Data
    switch kind {
    case "empty": data = Data()
    case "truncated": data = try fixture().dropLast()
    case "modified": data = try fixture() + Data(" ".utf8)
    default: data = Data(repeating: 32, count: TreeExport.maximumInputBytes + 1)
    }
    #expect(throws: ExportError.interfaceChanged) {
      try TreeExport.generate(native: data, version: "6.3.1")
    }
  }

  private func fixture() throws -> Data {
    let url = try #require(
      Bundle.module.url(forResource: "native-help", withExtension: "json", subdirectory: "Fixtures")
    )
    return try Data(contentsOf: url)
  }

  private func document() throws -> [String: Any] {
    try #require(
      JSONSerialization.jsonObject(with: TreeExport.generate(native: fixture(), version: "6.3.1"))
        as? [String: Any])
  }

  private func node(_ id: String) throws -> [String: Any] {
    let nodes = try #require(document()["commands"] as? [[String: Any]])
    return try #require(nodes.first { $0["id"] as? String == id })
  }
}
