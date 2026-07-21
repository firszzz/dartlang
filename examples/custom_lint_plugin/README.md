# Custom lint rules with `analysis_server_plugin`

This example shows how to build an analyzer plugin that reports **custom lint
rules** (and an optional quick fix) using
[`package:analysis_server_plugin`](https://pub.dev/packages/analysis_server_plugin).

Requires **Dart 3.10+** (Flutter 3.38+). Official docs:

- [Analyzer plugins overview](https://dart.dev/tools/analyzer-plugins)
- [Writing a plugin](https://github.com/dart-lang/sdk/blob/main/pkg/analysis_server_plugin/doc/writing_a_plugin.md)
- [Writing rules](https://github.com/dart-lang/sdk/blob/main/pkg/analysis_server_plugin/doc/writing_rules.md)
- [Writing fixes](https://github.com/dart-lang/sdk/blob/main/pkg/analysis_server_plugin/doc/writing_fixes.md)
- [Using plugins](https://github.com/dart-lang/sdk/blob/main/pkg/analysis_server_plugin/doc/using_plugins.md)
- [Testing rules](https://github.com/dart-lang/sdk/blob/main/pkg/analysis_server_plugin/doc/testing_rules.md)

## What you get in this package

| Path | Role |
| --- | --- |
| `lib/main.dart` | Plugin entry point (`final plugin = ...`) |
| `lib/src/rules/no_await.dart` | Demo lint: report every `await` in `lib/` |
| `lib/src/fixes/remove_await.dart` | Quick fix that deletes the `await` keyword |
| `test/no_await_test.dart` | Rule tests via `analyzer_testing` |
| `example/` | Consumer package that enables the plugin |

## 1. Create a plugin package

`pubspec.yaml`:

```yaml
name: custom_lint_plugin
environment:
  sdk: ^3.10.0

dependencies:
  analysis_server_plugin: ^0.3.20
  analyzer: ^14.1.0
  analyzer_plugin: ^0.14.14
```

> These packages move lockstep with the Dart SDK. Match versions to your SDK
> release (see the `analysis_server_plugin` changelog / SDK pins).


The analysis server loads **`lib/main.dart`** and expects a top-level variable
named `plugin`:

```dart
import 'package:analysis_server_plugin/plugin.dart';
import 'package:analysis_server_plugin/registry.dart';

final plugin = CustomLintPlugin();

class CustomLintPlugin extends Plugin {
  @override
  String get name => 'custom_lint_plugin';

  @override
  void register(PluginRegistry registry) {
    registry.registerLintRule(NoAwaitRule());
    registry.registerFixForRule(NoAwaitRule.code, RemoveAwait.new);
  }
}
```

- `registerLintRule` — off by default; enable under `plugins.*.diagnostics`
- `registerWarningRule` — on by default (like analyzer warnings)

## 2. Write a lint rule

A rule is two classes:

1. **`AnalysisRule`** — name, `LintCode`, and which AST nodes to visit
2. **`SimpleAstVisitor`** — inspect nodes and call `rule.reportAtNode(...)`

```dart
class NoAwaitRule extends AnalysisRule {
  static const LintCode code = LintCode(
    'no_await',
    "Don't use await expressions.",
    correctionMessage: "Try removing 'await'.",
  );

  NoAwaitRule()
      : super(name: 'no_await', description: 'Avoid await expressions.');

  @override
  DiagnosticCode get diagnosticCode => code;

  @override
  void registerNodeProcessors(
    RuleVisitorRegistry registry,
    RuleContext context,
  ) {
    registry.addAwaitExpression(this, _Visitor(this, context));
  }
}

class _Visitor extends SimpleAstVisitor<void> {
  final AnalysisRule rule;
  final RuleContext context;

  _Visitor(this.rule, this.context);

  @override
  void visitAwaitExpression(AwaitExpression node) {
    if (context.isInLibDir) {
      rule.reportAtNode(node);
    }
  }
}
```

Important details:

- Keep `LintCode` as a **`static const`** so `// ignore:` matching works.
- Prefer `SimpleAstVisitor` (not a recursive visitor) for rule performance.
- Register only the node kinds you need via `RuleVisitorRegistry.add*`.
- For multiple messages, extend `MultiAnalysisRule` and implement
  `diagnosticCodes`.

## 3. (Optional) Attach a quick fix

Subclass `ResolvedCorrectionProducer`, implement `compute`, then register the
**constructor tear-off** (instances are short-lived):

```dart
registry.registerFixForRule(NoAwaitRule.code, RemoveAwait.new);
```

See `lib/src/fixes/remove_await.dart` for a full deletion-based fix.

## 4. Enable the plugin in a consumer package

In the **root** `analysis_options.yaml` of the package or workspace (not a
nested options file):

```yaml
plugins:
  custom_lint_plugin:
    path: /absolute/or/relative/path/to/custom_lint_plugin
    diagnostics:
      no_await: true
```

Or from pub.dev:

```yaml
plugins:
  some_published_plugin: ^1.0.0
```

Then **restart the Dart Analysis Server**. Diagnostics also show up with
`dart analyze` / `flutter analyze`.

Suppress with the `pluginName/code` form:

```dart
// ignore: custom_lint_plugin/no_await
await future;

// ignore_for_file: custom_lint_plugin/no_await
```

## 5. Test rules

Use [`analyzer_testing`](https://pub.dev/packages/analyzer_testing) +
`test_reflective_loader`:

```dart
@reflectiveTest
class NoAwaitRuleTest extends AnalysisRuleTest {
  @override
  void setUp() {
    rule = NoAwaitRule();
    super.setUp();
  }

  Future<void> test_has_await() async {
    await assertDiagnostics(
      r'''
Future<void> f(Future<int> p) async {
  await p;
}
''',
      [lint(40, 7)],
    );
  }
}
```

Run:

```bash
cd examples/custom_lint_plugin
dart pub get
dart test
```

## Debugging tips

- Open the [analyzer diagnostics pages](https://github.com/dart-lang/sdk/blob/main/pkg/analysis_server/doc/tutorial/instrumentation.md#open-the-analyzer-diagnostics-pages); crashed plugins appear on the **plugins** screen.
- `print` from plugin code does not show in your IDE console — write to a log file instead.
- Keep `analysis_server_plugin` / `analyzer` versions compatible with your Dart SDK (Dart pins a constraint on the plugin package when resolving plugins).

## Suggested next steps

1. Replace `NoAwaitRule` with a domain-specific check (forbidden API, naming, package boundaries).
2. Browse shipped lints for patterns:
   [`pkg/linter/lib/src/rules`](https://github.com/dart-lang/sdk/tree/main/pkg/linter/lib/src/rules).
3. Add assists via `registerAssist` when you want refactors that are not tied to a diagnostic.
