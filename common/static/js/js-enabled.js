document.body.className = ((document.body.className) ? document.body.className + ' js-enabled' : 'js-enabled')

const printButton = document.getElementById('print-button')
if (printButton) {
  printButton.classList.add('amp-display-block')
}
