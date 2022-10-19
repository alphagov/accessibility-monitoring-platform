/*
Copy email text and structure to clipboard.
*/

function copyElementToClipboard () {
  const range = document.createRange()
  range.selectNode(document.getElementById('email-text'))
  window.getSelection().removeAllRanges()
  window.getSelection().addRange(range)
  document.execCommand('copy')
  window.getSelection().removeAllRanges()
}

const copyEmailButtons = document.getElementsByClassName('copy-email-to-clipboard')
Array.from(copyEmailButtons).forEach(function (copyEmailButton) {
  copyEmailButton.addEventListener('click', copyElementToClipboard)
})

module.exports = {
  copyElementToClipboard
}
