import 'package:analysis_server_plugin/plugin.dart';
import 'package:analysis_server_plugin/registry.dart';
import 'package:custom_lint_plugin/src/fixes/remove_await.dart';
import 'package:custom_lint_plugin/src/rules/no_await.dart';

/// Entry point discovered by the Dart Analysis Server.
///
/// The generated plugin host isolate imports this library and reads [plugin].
final plugin = CustomLintPlugin();

class CustomLintPlugin extends Plugin {
  @override
  String get name => 'custom_lint_plugin';

  @override
  void register(PluginRegistry registry) {
    // Lint rules are off by default and must be enabled under
    // plugins.<name>.diagnostics in analysis_options.yaml.
    // Use registerWarningRule(...) instead if the diagnostic should be on
    // by default.
    registry.registerLintRule(NoAwaitRule());

    // Associate a quick fix with the rule's LintCode.
    registry.registerFixForRule(NoAwaitRule.code, RemoveAwait.new);
  }
}
