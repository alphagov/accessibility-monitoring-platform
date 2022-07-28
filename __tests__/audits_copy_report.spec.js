/**
 * @jest-environment jsdom
 */

document.body.innerHTML = `<div id ="report-text">Report text to copy</div>
<button id="copy-report-to-clipboard">
    Copy report to clipboard
</button>`;

const {
    copyElementToClipboard,
} = require("../accessibility_monitoring_platform/static/js/audits_copy_report");

 describe("test audits copy report functions are present", () => {
    it.each([
        copyElementToClipboard,
    ])("%p is a function", (functionFromModule) => {
        expect(typeof functionFromModule).toBe("function");
    });
});
