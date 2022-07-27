/**
 * @jest-environment jsdom
 */

document.body.innerHTML = `<input id="id_name">
<input id="id_axe">
<input id="id_pdf">
<input id="id_error_found">
<input id="id_no_issue">
<input id="id_not_tested">
<input id="clear_search_form">
<div class="govuk-checkboxes__item">
    <input
        class="govuk-checkboxes__input"
        type="checkbox"
        name="manual"
        id="id_manual"
    >
    <label class="govuk-label govuk-checkboxes__label" for="id_manual">
        Manual tests
    </label>
</div>
<h2 class="govuk-heading-m" id="number_of_errors">Showing 77 errors</h2>
<div class="govuk-grid-row" id="testlist pdf WCAG 1.4.3 Contrast (Minimum) ">
    <div class="govuk-grid-column-full">
        <input type="hidden" name="form-0-wcag_definition" value="1" id="id_form-0-wcag_definition">
        <div class="govuk-form-group">
            <fieldset class="govuk-fieldset">
                <legend class="govuk-fieldset__legend govuk-fieldset__legend--l">
                    <label id="id_form-0-check_result_state-label" class="govuk-label"><b>WCAG 1.4.3 Contrast (Minimum)</b></label>
                </legend>
                <div class="govuk-radios" style="display:flex">
                    <div class="govuk-radios__item">
                        <input
                            class="govuk-radios__input"
                            type="radio"
                            name="form-0-check_result_state"
                            value="error"
                            horizontal
                            id="id_form-0-check_result_state_0"
                        >
                        <label class="govuk-label govuk-radios__label" for="id_form-0-check_result_state_0">
                            Error found
                        </label>
                    </div>
                    <div class="govuk-radios__item">
                        <input
                            class="govuk-radios__input"
                            type="radio"
                            name="form-0-check_result_state"
                            value="no-error"
                            horizontal
                            id="id_form-0-check_result_state_1"
                        >
                        <label class="govuk-label govuk-radios__label" for="id_form-0-check_result_state_1">
                            No issue
                        </label>
                    </div>
                    <div class="govuk-radios__item">
                        <input
                            class="govuk-radios__input"
                            type="radio"
                            name="form-0-check_result_state"
                            value="not-tested"
                            horizontal
                            id="id_form-0-check_result_state_2"
                            checked
                        >
                        <label class="govuk-label govuk-radios__label" for="id_form-0-check_result_state_2">
                            Not tested
                        </label>
                    </div>
                </div>
            </fieldset>
        </div>
        <div class="govuk-form-group">
            <label id="id_form-0-notes-label" class="govuk-label" for="id_form-0-notes"><b>Error details</b></label>
            <textarea name="form-0-notes" cols="40" rows="4" class="govuk-textarea" id="id_form-0-notes">
            </textarea>
        </div>
        <details class="govuk-details" data-module="govuk-details">
            <summary class="govuk-details__summary">
                <span class="govuk-details__summary-text">Preview</span>
            </summary>
            <div id="preview-id_form-0-notes" class="amp-preview govuk-details__text"></div>
        </details>
    </div>
</div>`;

const { updateUnfinishedManualTestCount } = require("../accessibility_monitoring_platform/static/js/audits_check_filter");

describe("test updateUnfinishedManualTestCount", () => {
    test("updateUnfinishedManualTestCount is a function", () => {
        expect(typeof updateUnfinishedManualTestCount).toBe("function");
    });
});
