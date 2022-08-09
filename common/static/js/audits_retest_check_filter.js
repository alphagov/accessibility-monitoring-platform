/*
All user to filter checks displayed by type, if check has been tested and WCAG definition name.
*/
const divElements = document.getElementsByTagName('div')

const wcagInputs = Array.from(divElements).filter(chapter => chapter.id.includes('testlist'))

const idName = document.querySelector('input[id="id_name"]')
idName.addEventListener('input', updateValue)

const idFixed = document.querySelector('input[id="id_fixed"]')
idFixed.addEventListener('input', updateValue)

const idNotFixed = document.querySelector('input[id="id_not_fixed"]')
idNotFixed.addEventListener('input', updateValue)

const idNotRetested = document.querySelector('input[id="id_not_retested"]')
idNotRetested.addEventListener('input', updateValue)

function fixedFilter (divTag, checked, className) {
  const val = divTag.querySelector('div.govuk-radios [name*="form-"][name*="-retest_state"]:checked').value
  if (checked && val !== 'fixed' && !divTag.className.includes(className)) {
    divTag.className += className
  } else {
    divTag.className = divTag.className.replace(className, '')
  }
}

function brokenFilter (divTag, checked, className) {
  const val = divTag.querySelector('div.govuk-radios [name*="form-"][name*="-retest_state"]:checked').value
  if (checked && val !== 'not-fixed' && !divTag.className.includes(className)) {
    divTag.className += className
  } else {
    divTag.className = divTag.className.replace(className, '')
  }
}

function notRetestedFilter (divTag, checked, className) {
  const val = divTag.querySelector('div.govuk-radios [name*="form-"][name*="-retest_state"]:checked').value
  if (checked && val !== 'not-tested' && !divTag.className.includes(className)) {
    divTag.className += className
  } else {
    divTag.className = divTag.className.replace(className, '')
  }
}

function textFilter (divTag, keyword) {
  if (document.getElementById('id_name').value === '') {
    divTag.className = divTag.className.replace(' text-filter', '')
    return
  }
  if (!divTag.id.toLowerCase().includes(keyword.toLowerCase()) && !divTag.className.includes(' text-filter')) { // If id includes keyword, and does not include filter-div: Add filter-div
    divTag.className += ' text-filter'
  } else if (divTag.id.toLowerCase().includes(keyword.toLowerCase())) { // If id includes keyword, and does include filter-div: Remove filter-div
    divTag.className = divTag.className.replace(' text-filter', '')
  }
}

function updateWcagList () {
  let errors = 0
  for (let i = 0; i < wcagInputs.length; i++) {
    fixedFilter(wcagInputs[i], idFixed.checked, ' filter-div-fixed')
    brokenFilter(wcagInputs[i], idNotFixed.checked, ' filter-div-broken')
    notRetestedFilter(wcagInputs[i], idNotRetested.checked, ' filter-div-not-retested')
    textFilter(wcagInputs[i], document.getElementById('id_name').value)

    // Counts the number WCAG tests in list view
    if (
      !wcagInputs[i].className.includes('filter-div') &&
      !wcagInputs[i].className.includes('text-filter')
    ) {
      errors += 1
    }

    document.getElementById('number_of_errors').innerHTML = `Showing ${errors} errors`
  }
}

function updateValue (e) {
  updateWcagList()
}

document.getElementById('clear_search_form').addEventListener('click', function (event) {
  event.preventDefault()
  document.getElementById('id_fixed').checked = false
  document.getElementById('id_not_fixed').checked = false
  document.getElementById('id_not_retested').checked = false
  document.getElementById('id_name').value = ''

  updateWcagList()
})

updateWcagList()

module.exports = {
  fixedFilter,
  brokenFilter,
  notRetestedFilter,
  textFilter,
  updateWcagList,
  updateValue,
}
