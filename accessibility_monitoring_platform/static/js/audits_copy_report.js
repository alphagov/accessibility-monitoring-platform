/*
Copy report text and structure to clipboard.
*/

function copyElementToClipboard () {
  const range = document.createRange()
  range.selectNode(document.getElementById('report-text'))
  window.getSelection().removeAllRanges()
  window.getSelection().addRange(range)
  document.execCommand('copy')
  window.getSelection().removeAllRanges()
}

const copyReportButton = document.getElementById('copy-report-to-clipboard')
copyReportButton.addEventListener('click', copyElementToClipboard)

module.exports = {
  copyElementToClipboard,
}
