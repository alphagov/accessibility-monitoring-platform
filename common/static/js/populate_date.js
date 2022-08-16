/*
Populate date field with today.
*/

function populateWithTodaysDate (dayId, monthId, yearId) {
  const today = new Date()
  document.getElementById(dayId).value = today.getDate()
  document.getElementById(monthId).value = today.getMonth() + 1 // January is 0!
  document.getElementById(yearId).value = today.getFullYear()
}

function keypressPopulateWithTodaysDate (event, dayId, monthId, yearId) {
  if (event.code === 'Enter' || event.code === 'Space') {
    event.preventDefault()
    populateWithTodaysDate(dayId, monthId, yearId)
  }
}

const populateDateElements = document.getElementsByClassName('amp-populate-date')

Array.from(populateDateElements).forEach(function (populateDateElement) {
  const dayFieldId = populateDateElement.getAttribute('dayFieldId')
  const monthFieldId = populateDateElement.getAttribute('monthFieldId')
  const yearFieldId = populateDateElement.getAttribute('yearFieldId')
  populateDateElement.onclick = function () {
    populateWithTodaysDate(dayFieldId, monthFieldId, yearFieldId)
  }
  populateDateElement.onkeypress = function () {
    keypressPopulateWithTodaysDate(event, dayFieldId, monthFieldId, yearFieldId)
  }
})

module.exports = {
  populateWithTodaysDate,
  keypressPopulateWithTodaysDate
}
