/*
Allow user to open link entered in URL field using dynamic link
*/

function updateOpenLinkControl(openLinkControlId, value) {
  const openLinkControlElement = document.getElementById(openLinkControlId)
  const placeholderElement = openLinkControlElement.nextElementSibling
  if (value.includes('https://') === false && value.includes('http://') === false) {
    openLinkControlElement.style.display = "none"
    placeholderElement.style.display = "block"
  } else {
    openLinkControlElement.style.display = "block"
    placeholderElement.style.display = "none"
    openLinkControlElement.setAttribute('href', value)
    openLinkControlElement.setAttribute('target', '_blank')
  }
}

const openLinkControlElements = document.getElementsByClassName('amp-open-link-control')

Array.from(openLinkControlElements).forEach(function(openLinkControlElement) {
  const openLinkControlId = openLinkControlElement.getAttribute('id')
  const inputFieldId = openLinkControlElement.dataset.inputFieldId
  const inputFieldElement = document.getElementById(inputFieldId)
  updateOpenLinkControl(openLinkControlId, inputFieldElement.value)
  inputFieldElement.addEventListener(
    'input', (event) => updateOpenLinkControl(openLinkControlId, event.target.value)
  )
})

module.exports = {
  updateOpenLinkControl
}
