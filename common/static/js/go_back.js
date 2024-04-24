/*
Allow user to go back to previous page
*/

function goBack() {
  history.back()
}

function keyboardGoBack(event) {
  if (event.code === 'Enter' || event.code === 'Space') {
    event.preventDefault()
    goBack()
  }
}

const goBackElements = document.getElementsByClassName('amp-go-back')

Array.from(goBackElements).forEach(function(goBackElement) {
  goBackElement.onclick = function() {
    goBack()
  }
  goBackElement.onkeypress = function() {
    // eslint-disable-next-line no-undef
    keyboardGoBack(event)
  }
})

module.exports = {
  goBack,
  keyboardGoBack
}
