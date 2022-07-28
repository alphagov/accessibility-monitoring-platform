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
<input id="id_manual">
<h2 id="number_of_errors">Showing 77 errors</h2>
<input id="id_form-0-check_result_state_2" checked>`;

const {
    updateUnfinishedManualTestCount,
    bodyListener,
    checkboxFilter,
    errorFoundFilter,
    noIssueFilter,
    notTestedFilter,
    textFilter,
    updateWcagList,
    updateValue,
} = require("../accessibility_monitoring_platform/static/js/audits_check_filter");

describe("test audits check filter functions are present", () => {
    it.each([
        updateUnfinishedManualTestCount,
        bodyListener,
        checkboxFilter,
        errorFoundFilter,
        noIssueFilter,
        notTestedFilter,
        textFilter,
        updateWcagList,
        updateValue,
    ])("%p is a function", (functionFromModule) => {
        expect(typeof functionFromModule).toBe("function");
    });
});
