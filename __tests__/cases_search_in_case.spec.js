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
<input type="text" name="search_in_case" placeholder="Search"
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
    <tr><td>Date one: 1 April 2022</td></tr>
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
`

const {
  addClearSearchListeners,
  addSearchListeners,
  buildSearchStructure,
  clearSearch,
  keypressClearSearch,
  keypressSearch,
  search,
  searchStructure
} = require('../common/static/js/cases_search_in_case')

describe('test cases search in case functions are present', () => {
  it.each([
    addClearSearchListeners,
    addSearchListeners,
    buildSearchStructure,
    clearSearch,
    keypressClearSearch,
    keypressSearch,
    search
  ])('%p is a function', (functionFromModule) => {
    expect(typeof functionFromModule).toBe('function')
  })
})

beforeEach(() => {
    clearSearch()
})

describe('test addSearchListeners', () => {
  test('listeners added to control element', () => {
    const searchControlElement = document.getElementById('search-in-case')
    addSearchListeners(searchControlElement)
  })
})

describe('test addClearSearchListeners', () => {
  test('listeners added to control element', () => {
    const clearSearchControlElement = document.getElementById('clear-search-in-case')
    addClearSearchListeners(clearSearchControlElement)
  })
})

describe('test buildSearchStructure', () => {
  test('searchable data found and stored in object', () => {
    const searchableElement = document.getElementById('extra')
    buildSearchStructure(searchableElement)
    const result = searchStructure.slice(-1)[0]
    expect(result).toEqual({
        text: 'Extra',
        html: 'Extra',
        targetUrl: extraTargetUrl,
        targetLabel: extraTargetLabel,
        targetPageName: extraTargetPageName
    })
  })
})

describe('test clearSearch', () => {
  test('clear search text, hide results and show searchable scope', () => {
    document.getElementById('id_search_in_case').value = 'date'
    search()
    expect(document.getElementById('search-results').hidden).toEqual(false)
    expect(document.getElementById('search-scope').hidden).toEqual(true)
    clearSearch()
    expect(document.getElementById('id_search_in_case').value).toEqual('')
    expect(document.getElementById('search-results').hidden).toEqual(true)
    expect(document.getElementById('search-scope').hidden).toEqual(false)
  })
})

describe('test keypressClearSearch', () => {
  test('clear search text, hide results and show searchable scope', () => {
    document.getElementById('id_search_in_case').value = 'date'
    search()
    expect(document.getElementById('search-results').hidden).toEqual(false)
    expect(document.getElementById('search-scope').hidden).toEqual(true)
    const mockEvent = { preventDefault: jest.fn, code: 'Space' }
    keypressClearSearch(mockEvent)
    expect(document.getElementById('id_search_in_case').value).toEqual('')
    expect(document.getElementById('search-results').hidden).toEqual(true)
    expect(document.getElementById('search-scope').hidden).toEqual(false)
  })
})

describe('test keypressSearch', () => {
  test('search for text, show results and hide searchable scope', () => {
    document.getElementById('id_search_in_case').value = 'date'
    expect(document.getElementById('search-results').hidden).toEqual(true)
    expect(document.getElementById('search-scope').hidden).toEqual(false)
    const mockEvent = { preventDefault: jest.fn, code: 'Enter' }
    keypressSearch(mockEvent)
    expect(document.getElementById('id_search_in_case').value).toEqual('date')
    expect(document.getElementById('search-results').hidden).toEqual(false)
    expect(document.getElementById('search-scope').hidden).toEqual(true)
  })
})

describe('test search', () => {
  test('search for text, show results and hide searchable scope', () => {
    document.getElementById('id_search_in_case').value = 'date'
    expect(document.getElementById('search-results').hidden).toEqual(true)
    expect(document.getElementById('search-scope').hidden).toEqual(false)
    search()
    const resultsElement = document.getElementById('search-results')
    expect(document.getElementById('id_search_in_case').value).toEqual('date')
    expect(resultsElement.hidden).toEqual(false)
    expect(document.getElementById('search-scope').hidden).toEqual(true)
    expect(resultsElement.textContent).toContain('Found 2 results for date')
    expect(resultsElement.textContent).toContain(`${defaultTargetPageName} | ${defaultTargetLabel}`)
    expect(resultsElement.innerHTML).toContain(defaultTargetUrl)
    expect(resultsElement.textContent).toContain('Date one: 1 April 2022')
    expect(resultsElement.textContent).toContain('Note: Updated')
  })

  test('search finds element-specific results', () => {
    document.getElementById('id_search_in_case').value = 'scope'
    search()
    const resultsElement = document.getElementById('search-results')
    expect(resultsElement.textContent).toContain('Found 1 result for scope')
    expect(resultsElement.textContent).toContain(`${rowTargetPageName} | ${rowTargetLabel}`)
    expect(resultsElement.innerHTML).toContain(rowTargetUrl)
    expect(resultsElement.textContent).toContain('Scope: Everything')
  })
})
