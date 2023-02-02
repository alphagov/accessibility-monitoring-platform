/*
Allow user to populate Enforcement recommendation notes input field.
*/

const controlId = 'amp-copy-text-control'
const sourceId = 'copy-summary-source'
const targetId = 'id_recommendation_notes'

function copyTextToInput (event) {
  event.preventDefault()
  const sourceValue = document.getElementById(sourceId).value
  const target = document.getElementById(targetId)
  target.value = sourceValue
}

function keyboardCopyTextToInput (event) {
  event.preventDefault()
  if (event.code === 'Enter' || event.code === 'Space') {
    copyTextToInput(event)
  }
}

const copyTextElement = document.getElementById(controlId)
copyTextElement.addEventListener('click', copyTextToInput)
copyTextElement.addEventListener('keypress', keyboardCopyTextToInput)

module.exports = {
  copyTextToInput,
  keyboardCopyTextToInput
}
