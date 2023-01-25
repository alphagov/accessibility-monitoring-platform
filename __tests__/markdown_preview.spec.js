/**
 * @jest-environment jsdom
 */

const specialChars = '&<>"\'_'
const escapedSpecialChars = '&amp;&lt;&gt;&quot;&apos;&#95;'
const doubleEscapedSpecialChars = '&amp;amp;&amp;lt;&amp;gt;&amp;quot;&amp;apos;&amp;#95;'
const sourceId = 'id_form-0-notes'
const targetId = 'preview-id_form-0-notes'
const sourceMarkdown = '# Header 1 <span>spanning</span>'
const expectedHtml = '<h1>Header 1 &lt;span&gt;spanning&lt;/span&gt;</h1>'

document.body.innerHTML = `<textarea id="${sourceId}">${sourceMarkdown}</textarea>
<div id="${targetId}"></div>`

const {
  escapeSpecialChars,
  undoubleEscape,
  previewMarkdown
} = require('../common/static/js/markdown_preview')

describe('test markdown preview functions are present', () => {
  it.each([
    escapeSpecialChars,
    undoubleEscape,
    previewMarkdown
  ])('%p is a function', (functionFromModule) => {
    expect(typeof functionFromModule).toBe('function')
  })
})

describe('test escapeSpecialChars', () => {
  test('special characters are escaped', () => {
    expect(escapeSpecialChars(specialChars)).toEqual(escapedSpecialChars)
  })
})

describe('test undoubleEscape', () => {
  test('double escaped special characters are unescaped', () => {
    expect(undoubleEscape(doubleEscapedSpecialChars)).toEqual(escapedSpecialChars)
  })
})

describe('test previewMarkdown', () => {
  test('html is generated from markdown', () => {
    document.getElementById(targetId).innerHTML = ''
    previewMarkdown(sourceId, targetId)
    expect(document.getElementById(targetId).innerHTML).toEqual(expectedHtml)
  })
})
