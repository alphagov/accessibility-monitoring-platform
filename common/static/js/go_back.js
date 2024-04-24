/*
Allow user to go back to previous page
*/

function goBack() {
  history.back()
}

const goBackElements = document.getElementsByClassName('amp-go-back')

Array.from(goBackElements).forEach(function(goBackElement) {
  goBackElement.onclick = function() {
    goBack()
  }
})

module.exports = {
  goBack
}
