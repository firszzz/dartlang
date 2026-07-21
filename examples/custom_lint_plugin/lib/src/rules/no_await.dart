import 'package:analyzer/analysis_rule/analysis_rule.dart';
import 'package:analyzer/analysis_rule/rule_context.dart';
import 'package:analyzer/analysis_rule/rule_visitor_registry.dart';
import 'package:analyzer/dart/ast/ast.dart';
import 'package:analyzer/dart/ast/visitor.dart';
import 'package:analyzer/error/error.dart';

/// Reports every `await` expression found in `lib/` sources.
///
/// This is intentionally simple so the shape of an [AnalysisRule] + visitor
/// pair is easy to follow. Real rules usually add more conditions before
/// calling [AnalysisRule.reportAtNode].
class NoAwaitRule extends AnalysisRule {
  /// Must be a single shared instance (`static const`) so ignore comments and
  /// analysis-server matching work correctly.
  static const LintCode code = LintCode(
    'no_await',
    "Don't use await expressions.",
    correctionMessage: "Try removing 'await'.",
  );

  NoAwaitRule()
      : super(
          name: 'no_await',
          description: 'Avoid await expressions (demo rule).',
        );

  @override
  DiagnosticCode get diagnosticCode => code;

  @override
  void registerNodeProcessors(
    RuleVisitorRegistry registry,
    RuleContext context,
  ) {
    var visitor = _Visitor(this, context);
    // Each visit* method on SimpleAstVisitor has a matching add* method.
    registry.addAwaitExpression(this, visitor);
  }
}

class _Visitor extends SimpleAstVisitor<void> {
  final AnalysisRule rule;
  final RuleContext context;

  _Visitor(this.rule, this.context);

  @override
  void visitAwaitExpression(AwaitExpression node) {
    // RuleContext exposes library/file facts such as isInLibDir.
    if (!context.isInLibDir) {
      return;
    }
    rule.reportAtNode(node);
  }
}
