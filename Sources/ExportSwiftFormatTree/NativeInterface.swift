import Foundation

struct NativeInterface: Decodable {
  let serializationVersion: Int
  let command: NativeCommand
}

struct NativeCommand: Decodable {
  let commandName: String
  let abstract: String?
  let discussion: String?
  let arguments: [NativeArgument]?
  let subcommands: [NativeCommand]?
}

struct NativeArgument: Decodable {
  struct Name: Decodable {
    let kind: String
    let name: String

    var flag: String { (kind == "long" ? "--" : "-") + name }
  }

  let kind: String
  let valueName: String
  let abstract: String?
  let preferredName: Name?
  let isOptional: Bool
  let isRepeating: Bool
  let parsingStrategy: String
}
