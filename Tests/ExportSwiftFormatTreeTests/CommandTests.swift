import Testing

@testable import ExportSwiftFormatTree

struct CommandTests {
  @Test(arguments: [
    ["--output", "/tmp/tree with spaces.json", "--executable-version", "6.3.1"],
    ["--executable-version=6.3.1", "--output=/tmp/tree with spaces.json"],
  ])
  func parsesNamedOptionsIndependentlyOfOrder(arguments: [String]) throws {
    let command = try ExportCommand.parse(arguments)
    #expect(command.executableVersion == "6.3.1")
    #expect(command.output == "/tmp/tree with spaces.json")
  }

  @Test(arguments: [
    [], ["--output", "tree.json"], ["--executable-version", "6.3.1"], ["--unknown"],
    ["--executable-version", "6.3.1", "--output", ""],
  ])
  func invalidArgumentsFailBeforeReadingInput(arguments: [String]) {
    #expect(throws: (any Error).self) { try ExportCommand.parse(arguments) }
  }

  @Test func generatedHelpDescribesInputAndOutput() {
    let help = ExportCommand.helpMessage()
    #expect(help.contains("stdin"))
    #expect(help.contains("--executable-version"))
    #expect(help.contains("--output"))
  }
}
