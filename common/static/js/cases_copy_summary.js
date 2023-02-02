/*
Allow user to populate Enforcement recommendation notes input field.
*/

function copyTextToInput (sourceId, targetId) {
  const sourceValue = document.getElementById(sourceId).value
  const target = document.getElementById(targetId)
  target.value = sourceValue
}

function keyboardCopyTextToInput (event, sourceId, targetId) {
  if (event.code === 'Enter' || event.code === 'Space') {
    copyTextToInput(sourceId, targetId)
  }
}

const copyTextLink = document.getElementById('amp-copy-text-link')
const sourceId = 'copy-summary-source'
const targetId = 'id_recommendation_notes'

copyTextLink.onclick = function () {
  event.preventDefault()
  copyTextToInput(sourceId, targetId)
}
copyTextLink.onkeypress = function () {
  event.preventDefault()
  keyboardCopyTextToInput(event, sourceId, targetId)
}

module.exports = {
  copyTextToInput,
  keyboardCopyTextToInput
}
