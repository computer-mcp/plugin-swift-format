import CryptoKit
import Foundation

enum ExportError: String, Error {
  case unsupportedVersion = "Unsupported executable version; verify and update the plugin baseline."
  case interfaceChanged =
    "Native interface differs from the verified baseline; no tree was produced."
  case invalidInterface = "Native interface cannot be mapped to the CLI Tree contract."
  case invalidArguments =
    "Use --executable-version VERSION --output PATH with native JSON on stdin."
}

enum TreeExport {
  static let executableVersion = "6.3.1"
  static let nativeSHA256 = "afce7a2f8c5b0825b90ce7061c6508eb5545b07b1414ed853c23a0fb6ab8c14e"
  static let maximumInputBytes = 4_194_304

  /// The pinned native export owns command/argument inventory. Source-verified
  /// supplements below supply semantics that ArgumentParser does not serialize.
  static func generate(native data: Data, version: String) throws -> Data {
    guard version == executableVersion else { throw ExportError.unsupportedVersion }
    guard data.count <= maximumInputBytes,
      SHA256.hash(data: data).map({ String(format: "%02x", $0) }).joined() == nativeSHA256
    else { throw ExportError.interfaceChanged }
    let native = try JSONDecoder().decode(NativeInterface.self, from: data)
    guard native.serializationVersion == 0, native.command.commandName == "swift-format",
      let format = native.command.subcommands?.first(where: { $0.commandName == "format" })
    else { throw ExportError.invalidInterface }

    var commands: [[String: Any]] = []
    // SwiftFormatCommand.configuration declares Format as the default subcommand.
    let rootNames = Set((native.command.arguments ?? []).map(\.valueName))
    let rootArguments =
      (native.command.arguments ?? [])
      + (format.arguments ?? []).filter { !rootNames.contains($0.valueName) }
    commands.append(
      try node(native.command, path: [], arguments: rootArguments, acceptsInput: true))
    func append(_ command: NativeCommand, path: [String]) throws {
      commands.append(
        try node(
          command, path: path, arguments: command.arguments ?? [],
          acceptsInput: path == ["format"] || path == ["lint"]))
      for child in command.subcommands ?? [] {
        try append(child, path: path + [child.commandName])
      }
    }
    for child in native.command.subcommands ?? [] {
      try append(child, path: [child.commandName])
    }
    let document: [String: Any] = [
      "format_version": 1,
      "source":
        "swiftlang/swift-format swift-6.3.1-RELEASE; native --experimental-dump-help sha256:\(nativeSHA256)",
      "executable_version": version,
      "executable_checks": [
        ["args": ["--version"], "stdout": "\(executableVersion)\n"],
        ["args": ["--experimental-dump-help"], "stdout_sha256": nativeSHA256],
      ],
      "coverage": "partial",
      "omissions": [
        "Every node and argument in the pinned native export is mapped. ArgumentParser's experimental introspection/completion control flags are not exposed as formatting tools.",
        "Equivalent short aliases and repeated scalar flag spellings are normalized to one canonical input. Upstream value-dependent validation (offset ranges, stdin/path combinations and configuration) remains in swift-format.",
      ],
      "commands": commands,
    ]
    return try JSONSerialization.data(
      withJSONObject: document, options: [.sortedKeys, .prettyPrinted, .withoutEscapingSlashes])
      + Data("\n".utf8)
  }

  private static func node(
    _ command: NativeCommand, path: [String], arguments: [NativeArgument], acceptsInput: Bool
  ) throws -> [String: Any] {
    var parameters: [[String: Any]] = []
    var options: [[String: Any]] = path.map { ["kind": "literal", "value": $0] }
    var positions: [[String: Any]] = []
    for argument in arguments {
      // LintFormatOptions.colorDiagnostics is one optional Boolean with prefixedNo inversion.
      if acceptsInput && argument.valueName == "no-color-diagnostics" { continue }
      guard argument.parsingStrategy == "default" else { throw ExportError.invalidInterface }
      let name = argument.valueName.replacingOccurrences(of: "-", with: "_")
      let inverse = acceptsInput && argument.valueName == "color-diagnostics"
      var schema: [String: Any] = ["type": argument.kind == "flag" ? "boolean" : "string"]
      if argument.isRepeating {
        guard argument.kind != "flag" else { throw ExportError.invalidInterface }
        schema = ["type": "array", "items": schema]
      }
      var parameter: [String: Any] = [
        "name": name, "schema": schema, "required": !argument.isOptional,
      ]
      if let description = argument.abstract { parameter["description"] = description }
      if argument.isOptional && argument.isRepeating { parameter["default"] = [String]() }
      if argument.kind == "flag" && !inverse { parameter["default"] = false }
      if path == ["dump-configuration"] && name == "configuration" {
        parameter["requires"] = ["effective"]
      }
      parameters.append(parameter)
      switch argument.kind {
      case "positional":
        positions.append(["kind": "positional", "parameter": name])
      case "flag", "option":
        guard let preferred = argument.preferredName,
          ["short", "long", "longWithSingleDash"].contains(preferred.kind)
        else { throw ExportError.invalidInterface }
        var token: [String: Any] = [
          "kind": argument.kind, "parameter": name, "flag": preferred.flag,
        ]
        if argument.kind == "option" { token["style"] = "equals" }
        if inverse { token["inverse"] = "--no-color-diagnostics" }
        options.append(token)
      default: throw ExportError.invalidInterface
      }
    }
    if !positions.isEmpty {
      options.append(["kind": "literal", "value": "--"])
      options.append(contentsOf: positions)
    }
    let description = [command.abstract, command.discussion].compactMap { $0 }.joined(
      separator: "\n")
    var result: [String: Any] = [
      "id": path.isEmpty
        ? "root" : path.joined(separator: "_").replacingOccurrences(of: "-", with: "_"),
      "path": path,
      "description": description.isEmpty ? "Swift Format \(command.commandName)" : description,
      "executable": true, "argv": options, "stdout": "text", "help_argv": path + ["--help"],
    ]
    if acceptsInput {
      parameters.append([
        "name": "source", "schema": ["type": "string"], "required": false,
        "description":
          "UTF-8 Swift source on stdin. Omit paths or use paths [\"-\"] to read stdin. Omission closes input without bytes.",
      ])
      result["stdin"] = ["parameter": "source", "encoding": "utf8"]
    }
    result["parameters"] = parameters
    return result
  }
}
