/*
Search for text and target url.
*/
let searchStructure = []

function search() {
  const searchElement = document.getElementById('id_search_in_case')
  const regex = new RegExp(searchElement.value, 'ig')
  const matches = searchStructure.filter(item => regex.test(item.text))
  let results = ''
  matches.forEach(result => results += `<tr class="govuk-table__row">
      <td class="govuk-table__cell">
        <b>${searchElement.value}</b> found in <a href="${result.target}">${result.target}</a>
        <br><br>
        <pre>${result.text.trim().replaceAll(regex, '<b>$&</b>')}</pre>
      </td>
    </tr>`)
  const resultsElement = document.getElementById('search-results')
  resultsElement.innerHTML = `
    <p class="govuk-body">Found ${matches.length} results for <b>${searchElement.value}</b></p>
    <table class="govuk-table"><tbody class="govuk-table__body">${results}</tbody></table>`
  resultsElement.hidden = false
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

const searchElement = document.getElementById('inside-search')
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
  const scopeElement = document.getElementById('search-scope')
  scopeElement.hidden = false
}

function keypressClearSearch() {
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

const clearSearchElement = document.getElementById('clear-inside-search')
addClearSearchListeners(clearSearchElement)

function buildSearchStructure(element) {
  if (element.textContent) {
    const textContent = element.textContent
    let parentElement = element.parentElement
    while (parentElement) {
      if (parentElement.dataset.searchTarget !== undefined) {
        break
      }
      parentElement = parentElement.parentElement
    }
    if (parentElement) {
      const searchTarget = parentElement.dataset.searchTarget
      searchStructure.push({text: textContent, target: searchTarget})
    } else {
      console.log('Target URL not found', element.textContent, element)
    }
  } else {
    console.log('No textContent', element.textContent, element)
  }
}

const searchScopeElements = Array.from(document.getElementById('search-scope').getElementsByTagName('*')).filter(
  element => ['H2', 'H3', 'TH', 'TD', 'P'].includes(element.tagName)
)
Array.from(searchScopeElements).forEach(function (searchScopeElement) {
  buildSearchStructure(searchScopeElement)
})
console.log('searchStructure', searchStructure)

module.exports = {
  search,
  clearSearchElement,
  addSearchListeners
}
