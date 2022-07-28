/**
 * @jest-environment jsdom
 */

document.body.innerHTML = `<textarea name="form-0-notes" id="id_form-0-notes"></textarea>
<div id="preview-id_form-0-notes" class="amp-preview govuk-details__text"></div>`;

const {
   previewMarkdown,
} = require("../accessibility_monitoring_platform/static/js/markdown_preview");

 describe("test markdown preview functions are present", () => {
    it.each([
       previewMarkdown,
    ])("%p is a function", (functionFromModule) => {
        expect(typeof functionFromModule).toBe("function");
    });
});
