/*
Allow user to copy text to the clipboard
*/

function copyTextToClipboard(textToCopy) {
  navigator.clipboard.writeText(textToCopy)
}

function keyboardCopyTextToClipboard(event, textToCopy) {
  if (event.code === 'Enter' || event.code === 'Space') {
    event.preventDefault()
    copyTextToClipboard(textToCopy)
  }
}
const copyElements = document.getElementsByClassName('amp-copy-text-to-clipboard')

Array.from(copyElements).forEach(function(copyElement) {
  const textToCopy = copyElement.dataset.textToCopy
  copyElement.onclick = function() {
    copyTextToClipboard(textToCopy)
  }
  copyElement.onkeypress = function() {
    keyboardCopyTextToClipboard(event, textToCopy)
  }
})

module.exports = {
  copyTextToClipboard,
  keyboardCopyTextToClipboard
}
