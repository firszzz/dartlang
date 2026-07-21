import 'package:analysis_server_plugin/edit/dart/correction_producer.dart';
import 'package:analysis_server_plugin/edit/dart/dart_fix_kind_priority.dart';
import 'package:analyzer/dart/ast/ast.dart';
import 'package:analyzer_plugin/utilities/change_builder/change_builder_core.dart';
import 'package:analyzer_plugin/utilities/fixes/fixes.dart';
import 'package:analyzer_plugin/utilities/range_factory.dart';

/// Quick fix that deletes the `await` keyword for [NoAwaitRule].
class RemoveAwait extends ResolvedCorrectionProducer {
  static const _removeAwaitKind = FixKind(
    'custom_lint_plugin.fix.removeAwait',
    DartFixKindPriority.standard,
    "Remove the 'await' keyword",
  );

  RemoveAwait({required super.context});

  @override
  CorrectionApplicability get applicability =>
      CorrectionApplicability.singleLocation;

  @override
  FixKind get fixKind => _removeAwaitKind;

  @override
  Future<void> compute(ChangeBuilder builder) async {
    var awaitExpression = node;
    if (awaitExpression is! AwaitExpression) {
      return;
    }

    var awaitToken = awaitExpression.awaitKeyword;
    await builder.addDartFileEdit(file, (builder) {
      builder.addDeletion(range.startStart(awaitToken, awaitToken.next!));
    });
  }
}
