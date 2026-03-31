/**
 * @jest-environment jsdom
 */

const { applyMiddleEllipsis } = require('../common/static/js/middle_ellipsis')

describe('applyMiddleEllipsis', () => {
    function applyMiddleEllipsis(element, maxLength = 30) {
        if (!element) return;

        const text = element.innerText.trim();

        if (text.length <= maxLength) return;

        const ellipsis = '…';
        const charsToShow = maxLength - ellipsis.length;

        const frontChars = Math.ceil(charsToShow / 2);
        const backChars = Math.floor(charsToShow / 2);

        const truncated =
            text.substring(0, frontChars) +
            ellipsis +
            text.substring(text.length - backChars);

        element.innerText = truncated;
    }

    it('does nothing when element is null', () => {
        expect(() => applyMiddleEllipsis(null)).not.toThrow();
    });

    it('does nothing when text length is shorter than maxLength', () => {
        const element = { innerText: 'short.txt' };

        applyMiddleEllipsis(element, 20);

        expect(element.innerText).toBe('short.txt');
    });

    it('does nothing when text length is exactly maxLength', () => {
        const element = { innerText: '1234567890' };

        applyMiddleEllipsis(element, 10);

        expect(element.innerText).toBe('1234567890');
    });

    it('truncates long text with a middle ellipsis', () => {
        const element = { innerText: 'verylongfilename.pdf' };

        applyMiddleEllipsis(element, 10);

        expect(element.innerText).toBe('veryl….pdf');
    });

    it('trims whitespace before calculating truncation', () => {
        const element = { innerText: '   verylongfilename.pdf   ' };

        applyMiddleEllipsis(element, 10);

        expect(element.innerText).toBe('veryl….pdf');
    });

    it('uses the default maxLength of 30 when not provided', () => {
        const element = {
            innerText: 'abcdefghijklmnopqrstuvwxyz1234567890'
        };

        applyMiddleEllipsis(element);

        expect(element.innerText.length).toBeLessThanOrEqual(30);
        expect(element.innerText).toContain('…');
    });

    it('keeps one more character at the front when split is uneven', () => {
        const element = { innerText: 'abcdefghijklmno' };

        applyMiddleEllipsis(element, 8);

        // charsToShow = 7, so front = 4, back = 3
        expect(element.innerText).toBe('abcd…mno');
    });

    it('replaces innerText with the truncated value', () => {
        const element = { innerText: 'thisisaverylongfilenameindeed.txt' };

        applyMiddleEllipsis(element, 12);

        expect(element.innerText).not.toBe('thisisaverylongfilenameindeed.txt');
        expect(element.innerText).toContain('…');
    });
});