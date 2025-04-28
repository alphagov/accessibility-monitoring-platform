/**
 * @jest-environment jsdom
 */

Object.defineProperty(navigator, "clipboard", {
  value: {
    writeText: async () => {},
  },
});

const textToCopy = 'Text to copy'

document.body.innerHTML = `
<span class='amp-copy-text-to-clipboard' data-text-to-copy="${textToCopy}" tabindex="0">
    Icon
</span>`

const {
  copyTextToClipboard,
  keyboardCopyTextToClipboard
} = require('../common/static/js/copy_text_to_clipboard')

describe('test cases copy text functions are present', () => {
  it.each([
    copyTextToClipboard,
    keyboardCopyTextToClipboard
  ])('%p is a function', (functionFromModule) => {
    expect(typeof functionFromModule).toBe('function')
  })
})

describe('test copyTextToClipboard', () => {
  test('copy text happens (on click)', () => {
    const writeTextMock = jest.spyOn(navigator.clipboard, 'writeText').mockResolvedValue();
    copyTextToClipboard(textToCopy)
    expect(writeTextMock).toHaveBeenCalledWith(textToCopy)
    jest.clearAllMocks();
  })
})

describe('test keyboardCopyTextToKeyboard', () => {
  test("copy text doesn't happen when neither enter nor space key pressed", () => {
     const mockEvent = { preventDefault: jest.fn, code: '' }
     const writeTextMock = jest.spyOn(navigator.clipboard, 'writeText').mockResolvedValue();
     keyboardCopyTextToClipboard(mockEvent, textToCopy)
     expect(writeTextMock).not.toHaveBeenCalled()
     jest.clearAllMocks();
   })

  it.each([
    'Enter',
    'Space'
  ])('copy text happens when %p key pressed', (eventCode) => {
    const mockEvent = { preventDefault: jest.fn, code: eventCode }
    const writeTextMock = jest.spyOn(navigator.clipboard, 'writeText').mockResolvedValue();
    keyboardCopyTextToClipboard(mockEvent, textToCopy)
    expect(writeTextMock).toHaveBeenCalledWith(textToCopy)
    jest.clearAllMocks();
  })
})
