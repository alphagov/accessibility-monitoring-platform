/*
Allow user to populate error text from existing matching issue.
*/

function copyTextToInput (targetId, sourceId) {
  const sourceValue = document.getElementById(sourceId).value
  const target = document.getElementById(targetId)
  target.value = sourceValue
  const event = new Event('input')
  target.dispatchEvent(event)
}

function keyboardCopyTextToInput (event, targetId, sourceId) {
  if (event.code === 'Enter' || event.code === 'Space') {
    event.preventDefault()
    copyTextToInput(targetId, sourceId)
  }
}

const copyErrorElements = document.getElementsByClassName('amp-copy-error')

Array.from(copyErrorElements).forEach(function (copyErrorElement) {
  const sourceId = copyErrorElement.getAttribute('sourceId')
  const targetId = copyErrorElement.getAttribute('targetId')
  copyErrorElement.onclick = function () {
    copyTextToInput(targetId, sourceId)
  }
  copyErrorElement.onkeypress = function () {
    // eslint-disable-next-line no-undef
    keyboardCopyTextToInput(event, targetId, sourceId)
  }
})

module.exports = {
  copyTextToInput,
  keyboardCopyTextToInput
}
