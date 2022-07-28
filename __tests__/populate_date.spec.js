/**
 * @jest-environment jsdom
 */

document.body.innerHTML = `
<div class="govuk-date-input">
    <div class="govuk-date-input__item">
        <div class="govuk-form-group">
            <label class="govuk-label govuk-date-input__label" for="id_report_sent_date_0">
                Day
            </label>
            <input class="govuk-input govuk-date-input__input govuk-input--width-2" type="number" name="report_sent_date_0" value="31" pattern="[0-9]*" inputmode="numeric" id="id_report_sent_date_0">
        </div>
    </div>
    <div class="govuk-date-input__item">
        <div class="govuk-form-group">
            <label class="govuk-label govuk-date-input__label" for="id_report_sent_date_1">
                Month
            </label>
            <input class="govuk-input govuk-date-input__input govuk-input--width-2" type="number" name="report_sent_date_1" value="3" pattern="[0-9]*" inputmode="numeric" id="id_report_sent_date_1">
        </div>
    </div>
    <div class="govuk-date-input__item">
        <div class="govuk-form-group">
            <label class="govuk-label govuk-date-input__label" for="id_report_sent_date_2">
                Year
            </label>
            <input class="govuk-input govuk-date-input__input govuk-input--width-4" type="number" name="report_sent_date_2" value="2022" pattern="[0-9]*" inputmode="numeric" id="id_report_sent_date_2">
        </div>
    </div>
</div>
<span class="amp-control amp-populate-date" tabindex="0" dayfieldid="id_report_sent_date_0" monthfieldid="id_report_sent_date_1" yearfieldid="id_report_sent_date_2">
    Populate with today's date
</span>`;

const {
    populateWithTodaysDate,
    keypressPopulateWithTodaysDate,
} = require("../accessibility_monitoring_platform/static/js/populate_date");

 describe("test populate date functions are present", () => {
    it.each([
        populateWithTodaysDate,
        keypressPopulateWithTodaysDate,
    ])("%p is a function", (functionFromModule) => {
        expect(typeof functionFromModule).toBe("function");
    });
});
