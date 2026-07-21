// Triggers the demo `no_await` lint from custom_lint_plugin.
Future<int> fetch() async => 42;

Future<void> main() async {
  // Suppress with pluginName/code:
  var value = await fetch(); // ignore: custom_lint_plugin/no_await
  print(value);

  // This await should be reported once the plugin is enabled and the
  // analysis server has been restarted.
  var again = await fetch();
  print(again);
}
