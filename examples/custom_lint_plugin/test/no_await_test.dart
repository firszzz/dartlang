import 'package:analyzer_testing/analysis_rule/analysis_rule.dart';
import 'package:custom_lint_plugin/src/rules/no_await.dart';
import 'package:test_reflective_loader/test_reflective_loader.dart';

void main() {
  defineReflectiveSuite(() {
    defineReflectiveTests(NoAwaitRuleTest);
  });
}

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

  Future<void> test_no_await() async {
    await assertNoDiagnostics(r'''
Future<void> f(Future<int> p) async {
  // No await.
}
''');
  }
}
