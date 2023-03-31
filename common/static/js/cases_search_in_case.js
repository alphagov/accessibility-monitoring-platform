/*
Search for lables and text inside case UI.
*/
let searchStructure = []

function search() {
  const searchElement = document.getElementById('id_search_in_case')
  if (searchElement.value !== '') {
    const regex = new RegExp(searchElement.value, 'ig')
    const notInsideHTMLTagRegex = new RegExp(`(?<!<[^>]*)${searchElement.value}`, 'ig')
    const matches = searchStructure.filter(item => regex.test(item.text))
    let results = ''
    matches.forEach(result => results += `<div class="govuk-grid-row">
      <div class="govuk-grid-column-full">
        <p class="govuk-body">
          <b>${result.targetPageName}</b> | <a href="${result.targetUrl}" class="govuk-link govuk-link--no-visited-state">${result.targetLabel}</a>
        </p>
        <table class="govuk-table"><tbody class="govuk-table__body">
        ${result.html.replaceAll(notInsideHTMLTagRegex, '<b>$&</b>')}
        </tbody></table>
      </div>
    </div>`)
    const resultsElement = document.getElementById('search-results')
    const pluralResults = matches.length == 1 ? '' : 's'
    resultsElement.innerHTML = `
      <p class="govuk-body">Found ${matches.length} result${pluralResults} for <b>${searchElement.value}</b></p>
      ${results}`
    resultsElement.hidden = false
  } else {
    const resultsElement = document.getElementById('search-results')
    resultsElement.innerHTML = `<p class="govuk-body">No search string entered</p>`
    resultsElement.hidden = false
  }
  const scopeElement = document.getElementById('search-scope')
  scopeElement.hidden = true
}

function keypressSearch (event) {
  if (event.code === 'Enter' || event.code === 'Space') {
    event.preventDefault()
    search()
  }
}

function addSearchListeners(element) {
  element.onclick = function () {
    search()
  }
  element.onkeypress = function () {
    // eslint-disable-next-line no-undef
    keypressSearch(event)
  }
}

const searchElement = document.getElementById('search-in-case')
addSearchListeners(searchElement)

const searchInput = document.getElementById('id_search_in_case');
searchInput.addEventListener("keypress", function(event) {
  if (event.key === "Enter") {
    event.preventDefault();
    search()
  }
});

function clearSearch() {
  const searchElement = document.getElementById('id_search_in_case')
  searchElement.value = ''
  const resultsElement = document.getElementById('search-results')
  resultsElement.hidden = true
  resultsElement.innerHTML = ''
  const scopeElement = document.getElementById('search-scope')
  scopeElement.hidden = false
}

function keypressClearSearch(event) {
  if (event.code === 'Enter' || event.code === 'Space') {
    event.preventDefault()
    clearSearch()
  }
}

function addClearSearchListeners(element) {
  element.onclick = function () {
    clearSearch()
  }
  element.onkeypress = function () {
    // eslint-disable-next-line no-undef
    keypressClearSearch(event)
  }
}

const clearSearchElement = document.getElementById('clear-search-in-case')
addClearSearchListeners(clearSearchElement)

function buildSearchStructure(element) {
  if (element.textContent) {
    const textContent = element.textContent
    const innerHTML = element.innerHTML
    if (element.dataset.searchTargetUrl !== undefined) {
      searchStructure.push({
        text: textContent,
        html: innerHTML,
        targetUrl: element.dataset.searchTargetUrl,
        targetLabel: element.dataset.searchTargetLabel,
        targetPageName: element.dataset.searchTargetPageName
      })
    } else {
      let parentElement = element.parentElement
      while (parentElement) {
        if (parentElement.dataset.searchTargetUrl !== undefined) {
          break
        }
        parentElement = parentElement.parentElement
      }
      if (parentElement) {
        const searchTargetUrl = parentElement.dataset.searchTargetUrl
        searchStructure.push({
          text: textContent,
          html: innerHTML,
          targetUrl: parentElement.dataset.searchTargetUrl,
          targetLabel: parentElement.dataset.searchTargetLabel,
          targetPageName: parentElement.dataset.searchTargetPageName
        })
      } else {
        console.log('Target URL not found', element.textContent, element)
      }
    }
  } else {
    console.log('No textContent', element.textContent, element)
  }
}

const searchScopeElements = Array.from(document.getElementById('search-scope').getElementsByTagName('TR'))
Array.from(searchScopeElements).forEach(function (searchScopeElement) {
  buildSearchStructure(searchScopeElement)
})
console.log('searchStructure', searchStructure)

module.exports = {
  addClearSearchListeners,
  addSearchListeners,
  buildSearchStructure,
  clearSearch,
  keypressClearSearch,
  keypressSearch,
  search,
  searchStructure
}
