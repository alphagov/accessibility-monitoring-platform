/*
Search for labels and text content in case UI.
*/

function Searchable({text, html, targetUrl, targetLabel, targetPageName} = {}) {
  this.text = text
  this.html = html
  this.targetUrl = targetUrl
  this.targetLabel = targetLabel
  this.targetPageName = targetPageName
}

let searchables = []

function findParentElementWithSearchTargetAttributes(element) {
  let parentElement = element.parentElement
  while (parentElement) {
    if (parentElement.dataset.searchTargetUrl !== undefined) {
      break
    }
    parentElement = parentElement.parentElement
  }
  return parentElement
}

function getSearchableFromElement(element) {
  if (element.textContent) {
    const textContent = element.textContent
    const innerHTML = element.innerHTML
    if (element.dataset.searchTargetUrl !== undefined) {
      searchables.push(new Searchable({
        text: textContent,
        html: innerHTML,
        targetUrl: element.dataset.searchTargetUrl,
        targetLabel: element.dataset.searchTargetLabel,
        targetPageName: element.dataset.searchTargetPageName
      }))
    } else {
      let parentElement = findParentElementWithSearchTargetAttributes(element)
      if (parentElement !== null && parentElement !== undefined) {
        const searchTargetUrl = parentElement.dataset.searchTargetUrl
        searchables.push(new Searchable({
          text: textContent,
          html: innerHTML,
          targetUrl: parentElement.dataset.searchTargetUrl,
          targetLabel: parentElement.dataset.searchTargetLabel,
          targetPageName: parentElement.dataset.searchTargetPageName
        }))
      }
    }
  }
}

const searchScopeElements = Array.from(
  document.getElementById('search-scope').getElementsByTagName('TR')
)
Array.from(searchScopeElements).forEach(function (searchScopeElement) {
  getSearchableFromElement(searchScopeElement)
})

function searchInCase() {
  const searchInputElement = document.getElementById('id_search_in_case')
  const searchResultsElement = document.getElementById('search-results')
  if (searchInputElement.value !== '') {
    const textRegex = new RegExp(searchInputElement.value, 'ig')
    const notInsideHTMLTagRegex = new RegExp(`(?<!<[^>]*)${searchInputElement.value}`, 'ig')
    const matchingSearchables = searchables.filter(searchable => textRegex.test(searchable.text))
    let resultsString = ''
    matchingSearchables.forEach(searchable => resultsString += `
    <div class="govuk-grid-row">
      <div class="govuk-grid-column-full">
        <p class="govuk-body">
          <b>${searchable.targetPageName}</b> |
          <a href="${searchable.targetUrl}" class="govuk-link govuk-link--no-visited-state">
            ${searchable.targetLabel}
          </a>
        </p>
        <table class="govuk-table">
          <tbody class="govuk-table__body">
            ${searchable.html.replaceAll(notInsideHTMLTagRegex, '<b>$&</b>')}
          </tbody>
        </table>
      </div>
    </div>`)
    const resultsLabel = matchingSearchables.length == 1 ? 'result' : 'results'
    searchResultsElement.innerHTML = `
      <p class="govuk-body">
        Found ${matchingSearchables.length} ${resultsLabel} for <b>${searchInputElement.value}</b>
      </p>
      ${resultsString}`
  } else {
    searchResultsElement.innerHTML = `<p class="govuk-body">No search string entered</p>`
  }
  searchResultsElement.hidden = false
  const searchScopeElement = document.getElementById('search-scope')
  searchScopeElement.hidden = true
}

const searchInCaseInput = document.getElementById('id_search_in_case');
searchInCaseInput.addEventListener("keypress", function(event) {
  if (event.key === "Enter") {
    event.preventDefault();
    searchInCase()
  }
});

function keypressSearchInCase (event) {
  if (event.code === 'Enter' || event.code === 'Space') {
    event.preventDefault()
    searchInCase()
  }
}

function addSearchInCaseListeners(element) {
  element.onclick = function () {
    searchInCase()
  }
  element.onkeypress = function () {
    // eslint-disable-next-line no-undef
    keypressSearchInCase(event)
  }
}

const searchInCaseButtonElement = document.getElementById('search-in-case')
addSearchInCaseListeners(searchInCaseButtonElement)

function clearSearchInCase() {
  const searchInputElement = document.getElementById('id_search_in_case')
  searchInputElement.value = ''
  const searchResultsElement = document.getElementById('search-results')
  searchResultsElement.hidden = true
  searchResultsElement.innerHTML = ''
  const searchScopeElement = document.getElementById('search-scope')
  searchScopeElement.hidden = false
}

function keypressClearSearchInCase(event) {
  if (event.code === 'Enter' || event.code === 'Space') {
    event.preventDefault()
    clearSearchInCase()
  }
}

function addClearSearchInCaseListeners(element) {
  element.onclick = function () {
    clearSearchInCase()
  }
  element.onkeypress = function () {
    // eslint-disable-next-line no-undef
    keypressClearSearchInCase(event)
  }
}

const clearSearchButtonElement = document.getElementById('clear-search-in-case')
addClearSearchInCaseListeners(clearSearchButtonElement)

module.exports = {
  addClearSearchInCaseListeners,
  addSearchInCaseListeners,
  findParentElementWithSearchTargetAttributes,
  getSearchableFromElement,
  clearSearchInCase,
  keypressClearSearchInCase,
  keypressSearchInCase,
  searchInCase,
  searchables
}
