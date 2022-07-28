/**
 * @jest-environment jsdom
 */

document.body.innerHTML = `<textarea id="notes-0" hidden>Error text to copy</textarea>
 <span tabIndex="0"
    class="amp-copy-error"
    sourceId="notes-0"
    targetId="notes">
    Click to populate error details
</span>
<textarea id="notes" hidden></textarea>`;

const {
   copyTextToInput,
   keyboardCopyTextToInput,
} = require("../accessibility_monitoring_platform/static/js/audits_copy_error");

describe("test audits copy error functions are present", () => {
    it.each([
        copyTextToInput,
        keyboardCopyTextToInput,
    ])("%p is a function", (functionFromModule) => {
        expect(typeof functionFromModule).toBe("function");
    });
});
