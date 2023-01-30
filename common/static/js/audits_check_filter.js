/*
All user to filter checks displayed by type, if check has been tested and WCAG definition name.
*/
const divElements = document.getElementsByTagName('div')

const checkListElements = Array.from(divElements).filter(divElement => divElement.hasAttribute('data-check-type'))

const body = document.querySelector('body')
body.addEventListener('input', bodyListener)

const idName = document.querySelector('input[id="id_name"]')
idName.addEventListener('input', updateChecksListener)

const typeRadioButtons = document.querySelectorAll('input[name="type_filter"]')
typeRadioButtons.forEach(typeRadioButton => {
  typeRadioButton.addEventListener('change', updateChecksListener)
})

const stateRadioButtons = document.querySelectorAll('input[name="state_filter"]')
stateRadioButtons.forEach(stateRadioButton => {
  stateRadioButton.addEventListener('change', updateChecksListener)
})

function updateNotTestedCounts () {
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

function bodyListener (e) {
  if (e.target.id.includes('id_form') && e.target.id.includes('-check_result_state')) {
    updateNotTestedCounts()
  }
}

function updateCheckListFiltering () {
  const typeFilterValue = document.querySelector('input[name="type_filter"]:checked').value
  const stateFilterValue = document.querySelector('input[name="state_filter"]:checked').value
  const textFilterValue = document.getElementById('id_name').value
  let errors = 0

  checkListElements.forEach(checkListElement => {
    checkListElement.style.display = 'block'
    if (typeFilterValue && checkListElement.getAttribute('data-check-type') !== typeFilterValue) {
      checkListElement.style.display = 'none'
    }
    const stateValue = checkListElement.querySelector('div.govuk-radios [name*="form-"][name*="-check_result_state"]:checked').value
    if (stateFilterValue && stateValue !== stateFilterValue) {
      checkListElement.style.display = 'none'
    }
    if (textFilterValue && !checkListElement.getAttribute('data-filter-string').toLowerCase().includes(textFilterValue.toLowerCase())) {
      checkListElement.style.display = 'none'
    }

    // Counts the number WCAG tests in list view
    if (checkListElement.style.display === 'block') {
      errors += 1
    }

    document.getElementById('number_of_errors').innerHTML = `Showing ${errors} errors`
  })
}

function updateChecksListener (e) {
  updateCheckListFiltering()
}

document.getElementById('clear_search_form').addEventListener('click', function (event) {
  event.preventDefault()
  document.getElementById('id_name').value = ''
  document.getElementById('id_type_filter_3').checked = true
  document.getElementById('id_state_filter_3').checked = true

  updateCheckListFiltering()
})

updateCheckListFiltering()
updateNotTestedCounts()

module.exports = {
  bodyListener,
  updateCheckListFiltering,
  updateChecksListener,
  updateNotTestedCounts
}
