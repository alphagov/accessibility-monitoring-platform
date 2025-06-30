/**
 * @jest-environment jsdom
 */

const searchString = 'search target'
const searchTarget = 'Search target'

document.body.innerHTML = `
<input id="id_search_in_case" type="text" name="search_in_case" placeholder="Search"
    class="govuk-input" id="id_search_in_case">
<div id="id_search_results"></div>
<div class="amp-searchable">
    <table>
        <tr><td>One: ${searchTarget}</td></tr>
        <tr><td>Two: ${searchTarget}</td></tr>
        <tr><td>First searchable element</td></tr>
    </table>
</div>
<div class="amp-searchable">
    <table>
        <tr><td>One: ${searchTarget}</td></tr>
        <tr><td>Second searchable element</td></tr>
    </table>
</div>
<div class="amp-searchable">
    <p>Third searchable element</p>
</div>`

const {
  addOninputSearchInCaseListener,
  getSearchableFromElement,
  clearSearchInCase,
  searchInCase,
  searchables
} = require('../common/static/js/search_page')

beforeEach(() => {
  clearSearchInCase()
})

describe('test cases search in case functions are present', () => {
  it.each([
    addOninputSearchInCaseListener,
    getSearchableFromElement,
    clearSearchInCase,
    searchInCase
  ])('%p is a function', (functionFromModule) => {
    expect(typeof functionFromModule).toBe('function')
  })
})

describe('test addOninputSearchInCaseListener', () => {
  test('listeners added to control element', () => {
    const searchControlElement = document.getElementById('id_search_in_case')
    addOninputSearchInCaseListener(searchControlElement)
  })
})

describe('test clearSearchInCase', () => {
  test('clear search text and hide results', () => {
    document.getElementById('id_search_in_case').value = searchString
    searchInCase()
    expect(document.getElementById('id_search_results').style.display).toEqual('block')
    clearSearchInCase()
    expect(document.getElementById('id_search_in_case').value).toEqual('')
    expect(document.getElementById('id_search_results').style.display).toEqual('none')
  })
})

describe('test search', () => {
  test('search for text and show results', () => {
    document.getElementById('id_search_in_case').value = searchString
    expect(document.getElementById('id_search_results').style.display).toEqual('none')
    searchInCase()
    expect(document.getElementById('id_search_results').style.display).toEqual('block')
    const resultsElement = document.getElementById('id_search_results')
    expect(document.getElementById('id_search_in_case').value).toEqual(searchString)
    expect(resultsElement.textContent).toContain(`Found 2 results for ${searchString}`)
    expect(resultsElement.textContent).toContain('First searchable element')
    expect(resultsElement.textContent).toContain('Second searchable element')
    expect(resultsElement.textContent).not.toContain('Third searchable element')
  })
})
