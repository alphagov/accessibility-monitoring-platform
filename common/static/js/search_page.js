/*
Search text content in UI.
*/

function Searchable({ text, childElements } = {}) {
  this.text = text
  this.childElements = childElements
}

const searchables = []

function getSearchableFromElement(element) {
  if (element.textContent) {
    const textContent = element.textContent.toLowerCase()
    searchables.push(new Searchable({
      text: textContent,
      childElements: Array.from(element.children),
    }))
  }
}

const searchScopeElements = Array.from(
  document.getElementsByClassName('amp-searchable')
)
Array.from(searchScopeElements).forEach(function(searchScopeElement) {
  getSearchableFromElement(searchScopeElement)
})

function searchInCase() {
  const searchInputElement = document.getElementById('id_search_in_case')
  const searchResultsElement = document.getElementById('id_search_results')
  if (searchInputElement.value === '') {
    clearSearchInCase()
  } else {
    const searchString = searchInputElement.value.toLowerCase()
    const notInsideHTMLTagRegex = new RegExp(`(?<!<[^>]*)${searchInputElement.value}`, 'ig')
    let matchingSearchables = searchables.filter(searchable => searchable.text.includes(searchString))
    const numberOfMatches = matchingSearchables.length
    let resultsString = ''
    matchingSearchables.forEach(searchable => {
      let childElementsString = ''
      searchable.childElements.forEach(childElement => childElementsString += `
        <div class="govuk-body amp-margin-bottom-5">
          ${childElement.innerHTML.replaceAll(notInsideHTMLTagRegex, '<b>$&</b>')}
        </div>`
      )
      resultsString += `
        <div class="govuk-grid-row amp-margin-bottom-30">
          <div class="govuk-grid-column-full">
            ${childElementsString}
          </div>
        </div>`
    })
    const resultsLabel = matchingSearchables.length == 1 ? 'result' : 'results'
    searchResultsElement.innerHTML = `
      <p class="govuk-body">
        Found ${numberOfMatches} ${resultsLabel} for <b>${searchInputElement.value}</b>
      </p>
      ${resultsString}<hr class="amp-width-100 amp-margin-bottom-60">`
    searchResultsElement.style.display = 'block'
  }
}

function addOninputSearchInCaseListener(element) {
  element.oninput = function() {
    searchInCase()
  }
}

const searchInputElement = document.getElementById('id_search_in_case');
addOninputSearchInCaseListener(searchInputElement)

function clearSearchInCase() {
  const searchInputElement = document.getElementById('id_search_in_case')
  searchInputElement.value = ''
  const searchResultsElement = document.getElementById('id_search_results')
  searchResultsElement.innerHTML = ''
  searchResultsElement.style.display = 'none'
}

module.exports = {
  addOninputSearchInCaseListener,
  getSearchableFromElement,
  clearSearchInCase,
  searchInCase,
  searchables
}
