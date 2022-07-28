/**
 * @jest-environment jsdom
 */

document.body.innerHTML = `<input id="id_name">
<input id="id_fixed">
<input id="id_not_fixed">
<input id="id_not_retested">
<input id="id_axe">
<input id="id_pdf">
<input id="id_error_found">
<input id="id_no_issue">
<input id="id_not_tested">
<input id="clear_search_form">
<h2 class="govuk-heading-m" id="number_of_errors">Showing 77 errors</h2>`;

const {
    fixedFilter,
    brokenFilter,
    notRetestedFilter,
    textFilter,
    updateWcagList,
    updateValue,
 } = require("../accessibility_monitoring_platform/static/js/audits_retest_check_filter");

describe("test audits retest check filter functions are present", () => {
    it.each([
        fixedFilter,
        brokenFilter,
        notRetestedFilter,
        textFilter,
        updateWcagList,
        updateValue,
    ])("%p is a function", (functionFromModule) => {
        expect(typeof functionFromModule).toBe("function");
    });
 });
