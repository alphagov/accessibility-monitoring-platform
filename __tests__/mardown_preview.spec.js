/**
 * @jest-environment jsdom
 */

const sourceId = 'id_form-0-notes'
const targetId = 'preview-id_form-0-notes'
const sourceMarkdown = '# Header 1'
const expectedHtml = '<h1 id="header1">Header 1</h1>'

document.body.innerHTML = `<textarea id="${sourceId}">${sourceMarkdown}</textarea>
<div id="${targetId}"></div>`

const {
  previewMarkdown
} = require('../common/static/js/markdown_preview')

describe('test markdown preview functions are present', () => {
  it.each([
    previewMarkdown
  ])('%p is a function', (functionFromModule) => {
    expect(typeof functionFromModule).toBe('function')
  })
})

describe('test previewMarkdown', () => {
  test('html is generated from markdown', () => {
    document.getElementById(targetId).innerHTML = ''
    previewMarkdown(sourceId, targetId)
    expect(document.getElementById(targetId).innerHTML).toEqual(expectedHtml)
  })
})
