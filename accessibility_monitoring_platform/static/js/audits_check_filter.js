/*
All user to filter checks displayed by type, if check has been tested and WCAG definition name.
*/
const divElements = document.getElementsByTagName('div')

const wcagInputs = Array.from(divElements).filter(chapter => chapter.id.includes('testlist'))

const body = document.querySelector('body')
body.addEventListener('input', bodyListener)

const idName = document.querySelector('input[id="id_name"]')
idName.addEventListener('input', updateValue)

const idManual = document.querySelector('input[id="id_manual"]')
idManual.addEventListener('input', updateValue)

const idAxe = document.querySelector('input[id="id_axe"]')
idAxe.addEventListener('input', updateValue)

const idPDF = document.querySelector('input[id="id_pdf"]')
idPDF.addEventListener('input', updateValue)

const idErrorFound = document.querySelector('input[id="id_error_found"]')
idErrorFound.addEventListener('input', updateValue)

const idNoIssue = document.querySelector('input[id="id_no_issue"]')
idNoIssue.addEventListener('input', updateValue)

const idNotTested = document.querySelector('input[id="id_not_tested"]')
idNotTested.addEventListener('input', updateValue)

function updateUnfinishedManualTestCount () {
  let manualTestsNotTested = 0
  for (let i = 0; i < wcagInputs.length; i++) {
    const val = wcagInputs[i].querySelector('div.govuk-radios [name*="form-"][name*="-check_result_state"]:checked').value

    if (
      val === 'not-tested' &&
      wcagInputs[i].id.includes('manual')
    ) {
      manualTestsNotTested += 1
    }
    document.querySelector('div.govuk-checkboxes__item [for="id_manual"]').innerHTML = `Manual tests (${manualTestsNotTested})`
  }
}

function bodyListener (e) {
  if (e.target.id.includes('id_form') && e.target.id.includes('-check_result_state')) {
    updateUnfinishedManualTestCount()
  }
}

function checkboxFilter (divTag, checked, keyword, className) {
  if (checked && !divTag.id.includes(keyword) && !divTag.className.includes(className)) { // If box is checked, includes keyword, and does not include filter-div: Add filter-div
    divTag.className += className
  } else if (!checked && !divTag.id.includes(keyword) && divTag.className.includes(className)) { // If box is not checked, includes keyword, and does include filter-div: Remove filter-div
    divTag.className = divTag.className.replace(className, '')
  }
}

function errorFoundFilter (divTag, checked, className) {
  const val = divTag.querySelector('div.govuk-radios [name*="form-"][name*="-check_result_state"]:checked').value
  if (checked && val !== 'error' && !divTag.className.includes(className)) {
    divTag.className += className
  } else {
    divTag.className = divTag.className.replace(className, '')
  }
}

function noIssueFilter (divTag, checked, className) {
  const val = divTag.querySelector('div.govuk-radios [name*="form-"][name*="-check_result_state"]:checked').value
  if (checked && val !== 'no-error' && !divTag.className.includes(className)) {
    divTag.className += className
  } else {
    divTag.className = divTag.className.replace(className, '')
  }
}

function notTestedFilter (divTag, checked, className) {
  const val = divTag.querySelector('div.govuk-radios [name*="form-"][name*="-check_result_state"]:checked').value
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
    checkboxFilter(wcagInputs[i], idManual.checked, 'manual', ' filter-div-manual')
    checkboxFilter(wcagInputs[i], idPDF.checked, 'pdf', ' filter-div-pdf')
    checkboxFilter(wcagInputs[i], idAxe.checked, 'axe', ' filter-div-axe')
    errorFoundFilter(wcagInputs[i], idErrorFound.checked, ' filter-div-error-found')
    noIssueFilter(wcagInputs[i], idNoIssue.checked, ' filter-div-no-issue')
    notTestedFilter(wcagInputs[i], idNotTested.checked, ' filter-div-not-tested')
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
  document.getElementById('id_manual').checked = false
  document.getElementById('id_axe').checked = false
  document.getElementById('id_pdf').checked = false
  document.getElementById('id_error_found').checked = false
  document.getElementById('id_no_issue').checked = false
  document.getElementById('id_not_tested').checked = false
  document.getElementById('id_name').value = ''

  updateWcagList()
})

updateWcagList()
updateUnfinishedManualTestCount()
