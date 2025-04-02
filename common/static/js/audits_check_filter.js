/*
All user to filter checks displayed by type, if check has been tested and WCAG definition name.
*/
const testPage = document.getElementById('id_form-0-check_result_state_0') !== null
const checkStateNameSuffix = testPage ? 'check_result_state' : 'retest_state'

const textFilterInput = document.querySelector('input[id="id_name"]')
textFilterInput.addEventListener('input', updateCheckListFiltering)

const typeRadioButtons = document.querySelectorAll('input[name="type_filter"]')
typeRadioButtons.forEach(typeRadioButton => {
  typeRadioButton.addEventListener('change', updateCheckListFiltering)
})

const stateRadioButtons = document.querySelectorAll('input[name="state_filter"]')
stateRadioButtons.forEach(stateRadioButton => {
  stateRadioButton.addEventListener('change', updateCheckListFiltering)
})

// document.getElementById('clear_search_form').addEventListener('click', resetFilterForm)

const divElements = document.getElementsByTagName('div')
const checkListElements = Array.from(divElements).filter(divElement => divElement.hasAttribute('data-check-type'))

function resetFilterForm (event) {
  event.preventDefault()
  document.getElementById('id_name').value = ''
  document.getElementById('id_type_filter_3').checked = true // Set type filter to all
  document.getElementById('id_state_filter_3').checked = true // Set state filter to all
  updateCheckListFiltering()
}

function updateCheckListFiltering (event) {
  const typeFilterValue = document.querySelector('input[name="type_filter"]:checked').value
  const stateFilterValue = document.querySelector('input[name="state_filter"]:checked').value
  const textFilterValue = document.getElementById('id_name').value
  let numberChecksDisplayed = 0

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

    if (checkListElement.style.display === 'block') {
      numberChecksDisplayed += 1
    }

    const errorSuffix = numberChecksDisplayed === 1 ? 'error' : 'errors'
    document.getElementById('number_of_errors').innerHTML = `Showing ${numberChecksDisplayed} ${errorSuffix}`
  })
}

updateCheckListFiltering()

module.exports = {
  resetFilterForm,
  updateCheckListFiltering
}
