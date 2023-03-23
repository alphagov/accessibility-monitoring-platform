/*
Populate date field with today.
*/
const oneWeekInDays = 7
const fourWeeksInDays = oneWeekInDays * 4
const twelveWeeksInDays = oneWeekInDays * 12

function populateWithDate (dayId, monthId, yearId, daysOffset=0) {
  const targetDate = new Date()
  targetDate.setDate(targetDate.getDate() + daysOffset);
  document.getElementById(dayId).value = targetDate.getDate()
  document.getElementById(monthId).value = targetDate.getMonth() + 1 // January is 0!
  document.getElementById(yearId).value = targetDate.getFullYear()
}

function keypressPopulateWithDate (event, dayId, monthId, yearId, daysOffset=0) {
  if (event.code === 'Enter' || event.code === 'Space') {
    event.preventDefault()
    populateWithDate(dayId, monthId, yearId, daysOffset)
  }
}

function addEvents (dateElement, daysOffset=0) {
  const dayFieldId = dateElement.getAttribute('dayFieldId')
  const monthFieldId = dateElement.getAttribute('monthFieldId')
  const yearFieldId = dateElement.getAttribute('yearFieldId')
  dateElement.onclick = function () {
    populateWithDate(dayFieldId, monthFieldId, yearFieldId, daysOffset)
  }
  dateElement.onkeypress = function () {
    // eslint-disable-next-line no-undef
    keypressPopulateWithDate(event, dayFieldId, monthFieldId, yearFieldId, daysOffset)
  }
}

const populateDateWithTodayElements = document.getElementsByClassName('amp-populate-date-today')

Array.from(populateDateWithTodayElements).forEach(function (populateDateElement) {
  addEvents(populateDateElement)
})

const populateDateWithOneWeekElements = document.getElementsByClassName('amp-populate-date-1-week')

Array.from(populateDateWithOneWeekElements).forEach(function (populateDateElement) {
  const daysOffset = oneWeekInDays
  addEvents(populateDateElement, daysOffset)
})

const populateDateWithFourWeeksElements = document.getElementsByClassName('amp-populate-date-4-weeks')

Array.from(populateDateWithFourWeeksElements).forEach(function (populateDateElement) {
  const daysOffset = fourWeeksInDays
  addEvents(populateDateElement, daysOffset)
})

const populateDateWithTwelveWeeksElements = document.getElementsByClassName('amp-populate-date-12-weeks')

Array.from(populateDateWithTwelveWeeksElements).forEach(function (populateDateElement) {
  const daysOffset = twelveWeeksInDays
  addEvents(populateDateElement, daysOffset)
})

module.exports = {
  populateWithDate,
  keypressPopulateWithDate
}
