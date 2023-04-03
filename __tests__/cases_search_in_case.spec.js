/**
 * @jest-environment jsdom
 */

const defaultTargetPageName = 'Default page name'
const defaultTargetLabel = 'Default page label'
const defaultTargetUrl = 'https://example.com'
const extraTargetPageName = 'Extra page name'
const extraTargetLabel = 'Extra page label'
const extraTargetUrl = 'https://example.com/extra'
const rowTargetPageName = 'Row page name'
const rowTargetLabel = 'Row page label'
const rowTargetUrl = 'https://example.com/row'

document.body.innerHTML = `
<input id="id_search_in_case" type="text" name="search_in_case" placeholder="Search"
    class="govuk-input" id="id_search_in_case">
<input id="search-in-case" type="submit" value="Search inside case"
    name="search_inside_case" class="govuk-button" data-module="govuk-button">
<input id="clear-search-in-case" type="submit" value="Clear search"
    name="clear_search_inside_case" class="govuk-button govuk-button--secondary"
    data-module="govuk-button">
<div id="search-results"></div>
<div id="search-scope"
    data-search-target-page-name="${defaultTargetPageName}"
    data-search-target-label="${defaultTargetLabel}"
    data-search-target-url="${defaultTargetUrl}">
    <table>
    <tr id="element-with-target-ancestor"><td>Date one: 1 April 2022</td></tr>
    <tr><td>Note: Updated</td></tr>
    <tr data-search-target-page-name="${rowTargetPageName}"
            data-search-target-label="${rowTargetLabel}"
            data-search-target-url="${rowTargetUrl}"><td>Scope: Everything</td></tr>
        <tr><td>Other: Nothing</td></tr>
    </table>
</div>
<div id="extra" data-search-target-page-name="${extraTargetPageName}"
    data-search-target-label="${extraTargetLabel}"
    data-search-target-url="${extraTargetUrl}">Extra</div>
<div id="element-without-target-ancestor"></div>`

const {
  addClearSearchInCaseListeners,
  addOninputSearchInCaseListener,
  addSearchInCaseListeners,
  findParentElementWithSearchTargetAttributes,
  getSearchableFromElement,
  clearSearchInCase,
  keypressClearSearchInCase,
  keypressSearchInCase,
  searchInCase,
  searchables
} = require('../common/static/js/cases_search_in_case')

beforeEach(() => {
  clearSearchInCase()
})

describe('test cases search in case functions are present', () => {
  it.each([
    addClearSearchInCaseListeners,
    addOninputSearchInCaseListener,
    addSearchInCaseListeners,
    findParentElementWithSearchTargetAttributes,
    getSearchableFromElement,
    clearSearchInCase,
    keypressClearSearchInCase,
    keypressSearchInCase,
    searchInCase
  ])('%p is a function', (functionFromModule) => {
    expect(typeof functionFromModule).toBe('function')
  })
})

describe('test addSearchInCaseListeners', () => {
  test('listeners added to control element', () => {
    const searchControlElement = document.getElementById('search-in-case')
    addSearchInCaseListeners(searchControlElement)
  })
})

describe('test addOninputSearchInCaseListener', () => {
  test('listeners added to control element', () => {
    const searchControlElement = document.getElementById('id_search_in_case')
    addOninputSearchInCaseListener(searchControlElement)
  })
})

describe('test addClearSearchInCaseListeners', () => {
  test('listeners added to control element', () => {
    const clearSearchControlElement = document.getElementById('clear-search-in-case')
    addClearSearchInCaseListeners(clearSearchControlElement)
  })
})

describe('test findParentElementWithSearchTargetAttributes', () => {
  test('element with ancestor containing search target attributes not found', () => {
    const element = document.getElementById('element-without-target-ancestor')
    expect(findParentElementWithSearchTargetAttributes(element)).toBe(null)
  })

  test('returns element with search target attributes not found', () => {
    const element = document.getElementById('element-with-target-ancestor')
    const parent = findParentElementWithSearchTargetAttributes(element)
    expect(parent.dataset.searchTargetUrl).toBe(defaultTargetUrl)
    expect(parent.dataset.searchTargetLabel).toBe(defaultTargetLabel)
    expect(parent.dataset.searchTargetPageName).toBe(defaultTargetPageName)
})
})

describe('test getSearchableFromElement', () => {
  test('searchable data found and stored in object', () => {
    const searchableElement = document.getElementById('extra')
    getSearchableFromElement(searchableElement)
    const result = searchables.slice(-1)[0]
    expect(result).toEqual({
        text: 'Extra',
        html: 'Extra',
        targetUrl: extraTargetUrl,
        targetLabel: extraTargetLabel,
        targetPageName: extraTargetPageName
    })
  })
})

describe('test clearSearchInCase', () => {
  test('clear search text, hide results and show searchable scope', () => {
    document.getElementById('id_search_in_case').value = 'date'
    searchInCase()
    expect(document.getElementById('search-results').style.display).toEqual('block')
    expect(document.getElementById('search-scope').style.display).toEqual('none')
    clearSearchInCase()
    expect(document.getElementById('id_search_in_case').value).toEqual('')
    expect(document.getElementById('search-results').style.display).toEqual('none')
    expect(document.getElementById('search-scope').style.display).toEqual('block')
  })
})

describe('test keypressClearSearchInCase', () => {
  test('clear search text, hide results and show searchable scope', () => {
    document.getElementById('id_search_in_case').value = 'date'
    searchInCase()
    expect(document.getElementById('search-results').style.display).toEqual('block')
    expect(document.getElementById('search-scope').style.display).toEqual('none')
    const mockEvent = { preventDefault: jest.fn, code: 'Space' }
    keypressClearSearchInCase(mockEvent)
    expect(document.getElementById('id_search_in_case').value).toEqual('')
    expect(document.getElementById('search-results').style.display).toEqual('none')
    expect(document.getElementById('search-scope').style.display).toEqual('block')
  })
})

describe('test keypressSearchInCase', () => {
  test('search for text, show results and hide searchable scope', () => {
    document.getElementById('id_search_in_case').value = 'date'
    expect(document.getElementById('search-results').style.display).toEqual('none')
    expect(document.getElementById('search-scope').style.display).toEqual('block')
    const mockEvent = { preventDefault: jest.fn, code: 'Enter' }
    keypressSearchInCase(mockEvent)
    expect(document.getElementById('id_search_in_case').value).toEqual('date')
    expect(document.getElementById('search-results').style.display).toEqual('block')
    expect(document.getElementById('search-scope').style.display).toEqual('none')
  })
})

describe('test search', () => {
  test('search for text, show results and hide searchable scope', () => {
    document.getElementById('id_search_in_case').value = 'date'
    expect(document.getElementById('search-results').style.display).toEqual('none')
    expect(document.getElementById('search-scope').style.display).toEqual('block')
    searchInCase()
    const resultsElement = document.getElementById('search-results')
    expect(document.getElementById('id_search_in_case').value).toEqual('date')
    expect(resultsElement.style.display).toEqual('block')
    expect(document.getElementById('search-scope').style.display).toEqual('none')
    expect(resultsElement.textContent).toContain('Found 2 results for date')
    expect(resultsElement.textContent).toContain(defaultTargetPageName)
    expect(resultsElement.textContent).toContain(defaultTargetLabel)
    expect(resultsElement.innerHTML).toContain(defaultTargetUrl)
    expect(resultsElement.textContent).toContain('Date one: 1 April 2022')
    expect(resultsElement.textContent).toContain('Note: Updated')
  })

  test('search finds element-specific results', () => {
    document.getElementById('id_search_in_case').value = 'scope'
    searchInCase()
    const resultsElement = document.getElementById('search-results')
    expect(resultsElement.textContent).toContain('Found 1 result for scope')
    expect(resultsElement.textContent).toContain(rowTargetPageName)
    expect(resultsElement.textContent).toContain(rowTargetLabel)
    expect(resultsElement.innerHTML).toContain(rowTargetUrl)
    expect(resultsElement.textContent).toContain('Scope: Everything')
  })
})
