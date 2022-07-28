/**
 * @jest-environment jsdom
 */

document.body.innerHTML = `
<div class="govuk-form-group">
    <input id="id_type_0">
    <input id="id_type_1">
    retesting
</div>`;

const {
    hideFormSet,
    updateValue,
} = require("../accessibility_monitoring_platform/static/js/audits_create_audit");

describe("test audits create audit functions are present", () => {
    it.each([
        hideFormSet,
        updateValue,
    ])("%p is a function", (functionFromModule) => {
        expect(typeof functionFromModule).toBe("function");
    });
});
