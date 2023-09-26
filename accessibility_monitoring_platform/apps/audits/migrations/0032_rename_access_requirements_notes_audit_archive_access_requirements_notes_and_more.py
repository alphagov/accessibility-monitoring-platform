# Generated by Django 4.2.4 on 2023-09-26 14:27

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("audits", "0031_alter_statementcheckresult_options"),
    ]

    operations = [
        migrations.RenameField(
            model_name="audit",
            old_name="access_requirements_notes",
            new_name="archive_access_requirements_notes",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="access_requirements_state",
            new_name="archive_access_requirements_state",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="accessibility_statement_accessible",
            new_name="archive_accessibility_statement_accessible",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="accessibility_statement_deadline_not_complete",
            new_name="archive_accessibility_statement_deadline_not_complete",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="accessibility_statement_deadline_not_complete_wording",
            new_name="archive_accessibility_statement_deadline_not_complete_wording",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="accessibility_statement_deadline_not_sufficient",
            new_name="archive_accessibility_statement_deadline_not_sufficient",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="accessibility_statement_deadline_not_sufficient_wording",
            new_name="archive_accessibility_statement_deadline_not_sufficient_wording",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="accessibility_statement_eass_link",
            new_name="archive_accessibility_statement_eass_link",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="accessibility_statement_missing_accessibility_issues",
            new_name="archive_accessibility_statement_missing_accessibility_issues",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="accessibility_statement_missing_mandatory_wording",
            new_name="archive_accessibility_statement_missing_mandatory_wording",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="accessibility_statement_missing_mandatory_wording_notes",
            new_name="archive_accessibility_statement_missing_mandatory_wording_notes",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="accessibility_statement_needs_more_re_accessibility",
            new_name="archive_accessibility_statement_needs_more_re_accessibility",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="accessibility_statement_needs_more_re_disproportionate",
            new_name="archive_accessibility_statement_needs_more_re_disproportionate",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="accessibility_statement_not_correct_format",
            new_name="archive_accessibility_statement_not_correct_format",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="accessibility_statement_not_specific_enough",
            new_name="archive_accessibility_statement_not_specific_enough",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="accessibility_statement_out_of_date",
            new_name="archive_accessibility_statement_out_of_date",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="accessibility_statement_prominent",
            new_name="archive_accessibility_statement_prominent",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="accessibility_statement_report_text_wording",
            new_name="archive_accessibility_statement_report_text_wording",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="accessibility_statement_state",
            new_name="archive_accessibility_statement_state",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="accessibility_statement_template_update",
            new_name="archive_accessibility_statement_template_update",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="audit_report_options_complete_date",
            new_name="archive_audit_report_options_complete_date",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="audit_report_text_complete_date",
            new_name="archive_audit_report_text_complete_date",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="audit_retest_access_requirements_notes",
            new_name="archive_audit_retest_access_requirements_notes",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="audit_retest_access_requirements_state",
            new_name="archive_audit_retest_access_requirements_state",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="audit_retest_compliance_notes",
            new_name="archive_audit_retest_compliance_notes",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="audit_retest_compliance_state",
            new_name="archive_audit_retest_compliance_state",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="audit_retest_contact_information_notes",
            new_name="archive_audit_retest_contact_information_notes",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="audit_retest_contact_information_state",
            new_name="archive_audit_retest_contact_information_state",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="audit_retest_content_not_in_scope_notes",
            new_name="archive_audit_retest_content_not_in_scope_notes",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="audit_retest_content_not_in_scope_state",
            new_name="archive_audit_retest_content_not_in_scope_state",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="audit_retest_declaration_notes",
            new_name="archive_audit_retest_declaration_notes",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="audit_retest_declaration_state",
            new_name="archive_audit_retest_declaration_state",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="audit_retest_disproportionate_burden_notes",
            new_name="archive_audit_retest_disproportionate_burden_notes",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="audit_retest_disproportionate_burden_state",
            new_name="archive_audit_retest_disproportionate_burden_state",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="audit_retest_enforcement_procedure_notes",
            new_name="archive_audit_retest_enforcement_procedure_notes",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="audit_retest_enforcement_procedure_state",
            new_name="archive_audit_retest_enforcement_procedure_state",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="audit_retest_feedback_notes",
            new_name="archive_audit_retest_feedback_notes",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="audit_retest_feedback_state",
            new_name="archive_audit_retest_feedback_state",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="audit_retest_method_notes",
            new_name="archive_audit_retest_method_notes",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="audit_retest_method_state",
            new_name="archive_audit_retest_method_state",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="audit_retest_non_regulation_notes",
            new_name="archive_audit_retest_non_regulation_notes",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="audit_retest_non_regulation_state",
            new_name="archive_audit_retest_non_regulation_state",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="audit_retest_preparation_date_notes",
            new_name="archive_audit_retest_preparation_date_notes",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="audit_retest_preparation_date_state",
            new_name="archive_audit_retest_preparation_date_state",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="audit_retest_review_notes",
            new_name="archive_audit_retest_review_notes",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="audit_retest_review_state",
            new_name="archive_audit_retest_review_state",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="audit_retest_scope_notes",
            new_name="archive_audit_retest_scope_notes",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="audit_retest_scope_state",
            new_name="archive_audit_retest_scope_state",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="audit_retest_statement_1_complete_date",
            new_name="archive_audit_retest_statement_1_complete_date",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="audit_retest_statement_2_complete_date",
            new_name="archive_audit_retest_statement_2_complete_date",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="audit_statement_1_complete_date",
            new_name="archive_audit_statement_1_complete_date",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="audit_statement_2_complete_date",
            new_name="archive_audit_statement_2_complete_date",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="audit_statement_decision_complete_date",
            new_name="archive_audit_statement_decision_complete_date",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="compliance_notes",
            new_name="archive_compliance_notes",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="compliance_state",
            new_name="archive_compliance_state",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="contact_information_notes",
            new_name="archive_contact_information_notes",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="contact_information_state",
            new_name="archive_contact_information_state",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="content_not_in_scope_notes",
            new_name="archive_content_not_in_scope_notes",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="content_not_in_scope_state",
            new_name="archive_content_not_in_scope_state",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="declaration_notes",
            new_name="archive_declaration_notes",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="declaration_state",
            new_name="archive_declaration_state",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="disproportionate_burden_notes",
            new_name="archive_disproportionate_burden_notes",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="disproportionate_burden_state",
            new_name="archive_disproportionate_burden_state",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="enforcement_procedure_notes",
            new_name="archive_enforcement_procedure_notes",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="enforcement_procedure_state",
            new_name="archive_enforcement_procedure_state",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="feedback_notes",
            new_name="archive_feedback_notes",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="feedback_state",
            new_name="archive_feedback_state",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="method_notes",
            new_name="archive_method_notes",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="method_state",
            new_name="archive_method_state",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="non_regulation_notes",
            new_name="archive_non_regulation_notes",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="non_regulation_state",
            new_name="archive_non_regulation_state",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="preparation_date_notes",
            new_name="archive_preparation_date_notes",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="preparation_date_state",
            new_name="archive_preparation_date_state",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="report_next_change_statement",
            new_name="archive_report_next_change_statement",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="report_next_disproportionate_burden",
            new_name="archive_report_next_disproportionate_burden",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="report_next_no_statement",
            new_name="archive_report_next_no_statement",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="report_next_statement_matches",
            new_name="archive_report_next_statement_matches",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="report_next_statement_not_right",
            new_name="archive_report_next_statement_not_right",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="report_options_next",
            new_name="archive_report_options_next",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="report_options_notes",
            new_name="archive_report_options_notes",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="review_notes",
            new_name="archive_review_notes",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="review_state",
            new_name="archive_review_state",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="scope_notes",
            new_name="archive_scope_notes",
        ),
        migrations.RenameField(
            model_name="audit",
            old_name="scope_state",
            new_name="archive_scope_state",
        ),
    ]
