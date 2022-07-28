/*
Hide retest_of_audit input field unless type of audit being created is retest.
*/

const formGroups = document.getElementsByClassName('govuk-form-group')

const retestForm = Array.from(formGroups).filter((formSet) => formSet.innerHTML.includes('retesting'))[0]

const radio0 = document.querySelector('input[id="id_type_0"]')
radio0.addEventListener('input', updateValue)

const radio1 = document.querySelector('input[id="id_type_1"]')
radio1.addEventListener('input', updateValue)

function hideFormSet (hide = true) {
  if (hide) {
    retestForm.className += ' hide-retest-options'
  } else {
    retestForm.className = retestForm.className.replace(' hide-retest-options', '')
  }
}

function updateValue (e) {
  if (e.target.value === 'retest') {
    hideFormSet(false)
  } else {
    hideFormSet(true)
  }
}

hideFormSet()

module.exports = {
  hideFormSet,
  updateValue,
}
