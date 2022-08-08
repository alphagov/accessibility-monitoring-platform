/**
 * @jest-environment jsdom
 */

const fs = require("fs");
const path = require("path");
const file = path.join(__dirname, "./", "audits_check_filter.html");
const bodyHtml = fs.readFileSync(file, {encoding:"utf8", flag:"r"});

document.body.innerHTML = bodyHtml;

const audits_check_filter = require("../accessibility_monitoring_platform/static/js/audits_check_filter");
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

describe("test updateUnfinishedManualTestCount", () => {
    test("manual tests count updated", () => {
        document.querySelector('div.govuk-checkboxes__item [for="id_manual"]').innerHTML = "";
        updateUnfinishedManualTestCount();
        expect(document.querySelector('div.govuk-checkboxes__item [for="id_manual"]').innerHTML).toEqual("Manual tests (14)");
    });
});

// If an ES6 module directly exports two functions (not within a class, object, etc., just
// directly exports the functions like in the question) and one directly calls the other,
// then that call cannot be mocked. See https://stackoverflow.com/questions/51269431/jest-mock-inner-function
// The code to be tested would need to be restructured for the following test to work.
// describe("test bodyListener", () => {
//     afterEach(() => {
//         jest.restoreAllMocks();
//     });

//     it.each([
//         ["id_form -check_result_state", 1],
//         ["any", 0],
//     ])("events with id %p update manual test count %p times", (eventId, expectedNumberOfCalls) => {
//         const spy = jest.spyOn(audits_check_filter, "updateUnfinishedManualTestCount");
//         const mockEvent = {preventDefault: jest.fn, target: {id: eventId}};
//         bodyListener(mockEvent);
//         expect(spy).toHaveBeenCalledTimes(expectedNumberOfCalls);
//     });
// });

describe("test checkboxFilter", () => {
    it.each([
        ["preserve", "id-without-key", true, "keyword-class", "keyword-class"],
        ["preserve", "id-with-keyword", true, "keyword-class", "keyword-class"],
        ["remove", "id-without-key", false, "keyword-class", ""],
        ["preserve", "id-with-keyword", false, "keyword-class", "keyword-class"],
        ["add", "id-without-key", true, "other-class", "other-classkeyword-class"],
        ["preserve", "id-with-keyword", true, "other-class", "other-class"],
        ["preserve", "id-without-key", false, "other-class", "other-class"],
        ["preserve", "id-with-keyword", false, "other-class", "other-class"],
    ])("%p class name: %p, %p, %p, %p", (behaviour, divTagId, checked, divTagClass, expectedDivTagClass) => {
        const keyword = "keyword"
        const className = "keyword-class"
        const divTag = {id: divTagId, className: divTagClass};
        checkboxFilter(divTag, checked, keyword, className);
        expect(divTag.className).toEqual(expectedDivTagClass);
    });
});

describe("test errorFoundFilter", () => {
    it.each([
        ["remove", "error", true, "keyword-class", ""],
        ["remove", "other", true, "keyword-class", ""],
        ["remove", "error", false, "keyword-class", ""],
        ["remove", "other", false, "keyword-class", ""],
        ["add", "error", true, "other-class", "other-classkeyword-class"],
        ["add", "other", true, "other-class", "other-classkeyword-class"],
        ["preserve", "error", false, "other-class", "other-class"],
        ["preserve", "other", false, "other-class", "other-class"],
    ])("%p class name: %p, %p, %p, %p", (behaviour, value, checked, divTagClass, expectedDivTagClass) => {
        const className = "keyword-class"
        const mockquerySelector = jest.fn();
        mockquerySelector.mockReturnValueOnce(value)
        const divTag = {
            className: divTagClass,
            querySelector: mockquerySelector
        };
        errorFoundFilter(divTag, checked, className);
        expect(divTag.className).toEqual(expectedDivTagClass);
    });
});

describe("test noIssueFilter", () => {
    it.each([
        ["remove", "no-error", true, "keyword-class", ""],
        ["remove", "other", true, "keyword-class", ""],
        ["remove", "no-error", false, "keyword-class", ""],
        ["remove", "other", false, "keyword-class", ""],
        ["add", "no-error", true, "other-class", "other-classkeyword-class"],
        ["add", "other", true, "other-class", "other-classkeyword-class"],
        ["preserve", "no-error", false, "other-class", "other-class"],
        ["preserve", "other", false, "other-class", "other-class"],
    ])("%p class name: %p, %p, %p, %p", (behaviour, value, checked, divTagClass, expectedDivTagClass) => {
        const className = "keyword-class"
        const mockquerySelector = jest.fn();
        mockquerySelector.mockReturnValueOnce(value)
        const divTag = {
            className: divTagClass,
            querySelector: mockquerySelector
        };
        noIssueFilter(divTag, checked, className);
        expect(divTag.className).toEqual(expectedDivTagClass);
    });
});

describe("test notTestedFilter", () => {
    it.each([
        ["remove", "not-tested", true, "keyword-class", ""],
        ["remove", "other", true, "keyword-class", ""],
        ["remove", "not-tested", false, "keyword-class", ""],
        ["remove", "other", false, "keyword-class", ""],
        ["add", "not-tested", true, "other-class", "other-classkeyword-class"],
        ["add", "other", true, "other-class", "other-classkeyword-class"],
        ["preserve", "not-tested", false, "other-class", "other-class"],
        ["preserve", "other", false, "other-class", "other-class"],
    ])("%p class name: %p, %p, %p, %p", (behaviour, value, checked, divTagClass, expectedDivTagClass) => {
        const className = "keyword-class"
        const mockquerySelector = jest.fn();
        mockquerySelector.mockReturnValueOnce(value)
        const divTag = {
            className: divTagClass,
            querySelector: mockquerySelector
        };
        notTestedFilter(divTag, checked, className);
        expect(divTag.className).toEqual(expectedDivTagClass);
    });
});

describe("test textFilter", () => {
    let spy;

    beforeAll(() => {
        spy = jest.spyOn(document, 'getElementById');
    });

    it.each([
        ["preserve", "keyword", "no-matching-key", "other-class text-filter", "other-class text-filter"],
        ["remove", "", "no-matching-key", "other-class text-filter", "other-class"],
        ["remove", "keyword", "matching-keyword", "other-class text-filter", "other-class"],
        ["remove", "", "matching-keyword", "other-class text-filter", "other-class"],
        ["add", "keyword", "no-matching-key", "other-class", "other-class text-filter"],
        ["no", "", "no-matching-key", "other-class", "other-class"],
        ["no", "keyword", "matching-keyword", "other-class", "other-class"],
        ["no", "", "matching-keyword", "other-class", "other-class"],
    ])("%p text-filter class: %p, %p, %p, %p", (behaviour, keyword, divTagId, divTagClass, expectedDivTagClass) => {
        spy.mockReturnValue({value: keyword});
        const divTag = {
            id: divTagId,
            className: divTagClass,
        };
        textFilter(divTag, keyword);
        expect(divTag.className).toEqual(expectedDivTagClass);
    });
});

describe("test updateWcagList", () => {
    test("error count updated", () => {
        document.getElementById('number_of_errors').innerHTML = "";
        updateWcagList();
        expect(document.getElementById('number_of_errors').innerHTML).toEqual("Showing 77 errors");
    });
});

describe("test updateValue", () => {
    test("error count updated", () => {
        document.getElementById('number_of_errors').innerHTML = "";
        const mockEvent = {};
        updateValue(mockEvent);
        expect(document.getElementById('number_of_errors').innerHTML).toEqual("Showing 77 errors");
    });
});
