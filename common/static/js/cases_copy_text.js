/*
Allow user to populate input field with text from element.
*/

function copyTextToInput(targetId, sourceText) {
  const target = document.getElementById(targetId)
  target.value = sourceText
}

function keyboardCopyTextToInput(event, targetId, sourceText) {
  if (event.code === 'Enter' || event.code === 'Space') {
    event.preventDefault()
    copyTextToInput(targetId, sourceText)
  }
}

const copyElements = document.getElementsByClassName('amp-copy-text')

Array.from(copyElements).forEach(function(copyElement) {
  const sourceText = copyElement.getAttribute('sourceText')
  const targetId = copyElement.getAttribute('targetId')
  copyElement.onclick = function() {
    copyTextToInput(targetId, sourceText)
  }
  copyElement.onkeypress = function() {
    // eslint-disable-next-line no-undef
    keyboardCopyTextToInput(event, targetId, sourceText)
  }
})

module.exports = {
  copyTextToInput,
  keyboardCopyTextToInput
}
