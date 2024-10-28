/*
Search for labels and text content in case UI.
*/

function Searchable({ text, childElements, targetUrl, targetLabel, targetPageName } = {}) {
  this.text = text
  this.childElements = childElements
  this.targetUrl = targetUrl
  this.targetLabel = targetLabel
  this.targetPageName = targetPageName
}

const searchables = []

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
    if (element.dataset.searchTargetUrl !== undefined) {
      searchables.push(new Searchable({
        text: textContent,
        childElements: Array.from(element.children),
        targetUrl: element.dataset.searchTargetUrl,
        targetLabel: element.dataset.searchTargetLabel,
        targetPageName: element.dataset.searchTargetPageName
      }))
    } else {
      const parentElement = findParentElementWithSearchTargetAttributes(element)
      if (parentElement !== null && parentElement !== undefined) {
        const searchTargetUrl = parentElement.dataset.searchTargetUrl
        searchables.push(new Searchable({
          text: textContent,
          childElements: Array.from(element.children),
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
Array.from(searchScopeElements).forEach(function(searchScopeElement) {
  getSearchableFromElement(searchScopeElement)
})

function searchInCase() {
  const searchInputElement = document.getElementById('id_search_in_case')
  const searchResultsElement = document.getElementById('search-results')
  if (searchInputElement.value === '') {
    clearSearchInCase()
  } else {
    const textRegex = new RegExp(searchInputElement.value, 'ig')
    const notInsideHTMLTagRegex = new RegExp(`(?<!<[^>]*)${searchInputElement.value}`, 'ig')
    const matchingSearchables = searchables.filter(searchable => textRegex.test(searchable.text))
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
            <p class="govuk-body amp-margin-bottom-5">
              <b>${searchable.targetPageName}</b> |
              <a href="${searchable.targetUrl}" class="govuk-link govuk-link--no-visited-state">
                ${searchable.targetLabel}
              </a>
            </p>
            ${childElementsString}
          </div>
        </div>`
    })
    const resultsLabel = matchingSearchables.length == 1 ? 'result' : 'results'
    searchResultsElement.innerHTML = `
      <p class="govuk-body">
        Found ${matchingSearchables.length} ${resultsLabel} for <b>${searchInputElement.value}</b>
      </p>
      ${resultsString}`
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
  const searchResultsElement = document.getElementById('search-results')
  searchResultsElement.innerHTML = ''
  searchResultsElement.style.display = 'none'
}

module.exports = {
  addOninputSearchInCaseListener,
  findParentElementWithSearchTargetAttributes,
  getSearchableFromElement,
  clearSearchInCase,
  searchInCase,
  searchables
}
