/*
All user to filter checks displayed by type, if check has been tested and WCAG definition name.
*/
const testPage = document.getElementById('id_form-0-check_result_state_0') !== null
const checkStateNameSuffix = testPage ? 'check_result_state' : 'retest_state'

const divElements = document.getElementsByTagName('div')

const checkListElements = Array.from(divElements).filter(divElement => divElement.hasAttribute('data-check-type'))
if (testPage === true) {
  checkListElements.forEach(checkListElement => {
    checkListElement.addEventListener('input', updateNotTestedCounts)
  })
}

const idName = document.querySelector('input[id="id_name"]')
idName.addEventListener('input', updateCheckListFiltering)

const typeRadioButtons = document.querySelectorAll('input[name="type_filter"]')
typeRadioButtons.forEach(typeRadioButton => {
  typeRadioButton.addEventListener('change', updateCheckListFiltering)
})

const stateRadioButtons = document.querySelectorAll('input[name="state_filter"]')
stateRadioButtons.forEach(stateRadioButton => {
  stateRadioButton.addEventListener('change', updateCheckListFiltering)
})

document.getElementById('clear_search_form').addEventListener('click', resetFilterForm)

function updateCheckListFiltering (event) {
  const typeFilterValue = document.querySelector('input[name="type_filter"]:checked').value
  const stateFilterValue = document.querySelector('input[name="state_filter"]:checked').value
  const textFilterValue = document.getElementById('id_name').value
  let errors = 0

  checkListElements.forEach(checkListElement => {
    checkListElement.style.display = 'block'
    if (typeFilterValue !== '' && checkListElement.getAttribute('data-check-type') !== typeFilterValue) {
      checkListElement.style.display = 'none'
    }
    const stateValue = checkListElement.querySelector(`div.govuk-radios [name*="form-"][name*="-${checkStateNameSuffix}"]:checked`).value
    if (stateFilterValue !== '' && stateValue !== stateFilterValue) {
      checkListElement.style.display = 'none'
    }
    if (textFilterValue !== '' && !checkListElement.getAttribute('data-filter-string').toLowerCase().includes(textFilterValue.toLowerCase())) {
      checkListElement.style.display = 'none'
    }

    // Counts the number WCAG tests in list view
    if (checkListElement.style.display === 'block') {
      errors += 1
    }

    document.getElementById('number_of_errors').innerHTML = `Showing ${errors} errors`
  })
}

function updateNotTestedCounts (event) {
  let manualNotTested = 0
  let axeNotTested = 0
  let pdfNotTested = 0
  checkListElements.forEach(checkListElement => {
    const stateValue = checkListElement.querySelector('div.govuk-radios [name*="form-"][name*="-check_result_state"]:checked').value
    const typeValue = checkListElement.getAttribute("data-check-type")

    if (stateValue === 'not-tested') {
      switch (typeValue) {
        case 'manual':
          manualNotTested += 1
          break;
        case 'axe':
          axeNotTested += 1
          break;
        case 'pdf':
          pdfNotTested += 1
      }
    }
  })

  document.querySelector('label[for=id_type_filter_0]').innerHTML = `Manual tests (${manualNotTested} not tested)`
  document.querySelector('label[for=id_type_filter_1]').innerHTML = `Axe tests (${axeNotTested} not tested)`
  document.querySelector('label[for=id_type_filter_2]').innerHTML = `PDF (${pdfNotTested} not tested)`
}

function resetFilterForm (event) {
  event.preventDefault()
  document.getElementById('id_name').value = ''
  document.getElementById('id_type_filter_3').checked = true // Set type filter to all
  document.getElementById('id_state_filter_3').checked = true // Set state filter to all
  updateCheckListFiltering()
}

updateCheckListFiltering()
if (testPage === true) {
  updateNotTestedCounts()
}

module.exports = {
  resetFilterForm,
  updateCheckListFiltering,
  updateNotTestedCounts
}
