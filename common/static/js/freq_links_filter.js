/*
Allow user to filter frequently used links by case type.
*/
const caseTypeRadioButtons = document.querySelectorAll('input[name="case_type_filter"]')
caseTypeRadioButtons.forEach(typeRadioButton => {
  typeRadioButton.addEventListener('change', updateFreqLinkFiltering)
})

const trElements = document.getElementsByTagName('tr')
const freqLinkElements = Array.from(trElements).filter(divElement => divElement.hasAttribute('data-case-type'))

function updateFreqLinkFiltering (event) {
  const caseTypeFilterValue = document.querySelector('input[name="case_type_filter"]:checked').value
  let numberFreqLinksDisplayed = 0

  freqLinkElements.forEach(freqLinkElement => {
    freqLinkElement.style.display = 'block'
    if (caseTypeFilterValue !== 'none' && freqLinkElement.getAttribute('data-case-type') !== 'all' && freqLinkElement.getAttribute('data-case-type') !== caseTypeFilterValue) {
      freqLinkElement.style.display = 'none'
    }

    if (freqLinkElement.style.display === 'block') {
      numberFreqLinksDisplayed += 1
    }

    const summarySuffix = numberFreqLinksDisplayed === 1 ? 'link' : 'links'
    document.getElementById('filter_summary').innerHTML = `Showing ${numberFreqLinksDisplayed} ${summarySuffix}`
  })
}

updateFreqLinkFiltering()

module.exports = {
  updateFreqLinkFiltering
}
