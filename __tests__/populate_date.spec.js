/**
 * @jest-environment jsdom
 */

const dayId = 'id_report_sent_date_0'
const monthId = 'id_report_sent_date_1'
const yearId = 'id_report_sent_date_2'

const today = new Date()
const day = today.getDate().toString()
const month = (today.getMonth() + 1).toString()
const year = today.getFullYear().toString()

document.body.innerHTML = `
<input type="number" name="report_sent_date_0" value="31" pattern="[0-9]*" inputmode="numeric" id="${dayId}">
<input type="number" name="report_sent_date_1" value="3" pattern="[0-9]*" inputmode="numeric" id="${monthId}">
<input type="number" name="report_sent_date_2" value="2022" pattern="[0-9]*" inputmode="numeric" id="${yearId}">
<span id="control-id" class="amp-populate-date-today" tabindex="0" dayfieldid="${dayId}" monthfieldid="${monthId}" yearfieldid="${yearId}">
    Populate with today's date
</span>`

const {
  populateWithDate,
  keypressPopulateWithDate,
  addPopulateDateListeners
} = require('../common/static/js/populate_date')

beforeEach(() => {
  document.getElementById(dayId).value = ''
  document.getElementById(monthId).value = ''
  document.getElementById(yearId).value = ''
})

describe('test populate date functions are present', () => {
  it.each([
    populateWithDate,
    keypressPopulateWithDate,
    addPopulateDateListeners
  ])('%p is a function', (functionFromModule) => {
    expect(typeof functionFromModule).toBe('function')
  })
})

describe('test populateWithDate', () => {
  test('date populated (on click)', () => {
    populateWithDate(dayId, monthId, yearId)
    expect(document.getElementById(dayId).value).toEqual(day)
    expect(document.getElementById(monthId).value).toEqual(month)
    expect(document.getElementById(yearId).value).toEqual(year)
  })
})

describe('test keypressPopulateWithDate', () => {
  it.each([
    'Enter',
    'Space'
  ])('date populated when %p key pressed', (eventCode) => {
    const mockEvent = { preventDefault: jest.fn, code: eventCode }
    keypressPopulateWithDate(mockEvent, dayId, monthId, yearId)
    expect(document.getElementById(dayId).value).toEqual(day)
    expect(document.getElementById(monthId).value).toEqual(month)
    expect(document.getElementById(yearId).value).toEqual(year)
  })

  test('date not populated when neither enter nor space key pressed', () => {
    const mockEvent = { preventDefault: jest.fn, code: '' }
    keypressPopulateWithDate(mockEvent, dayId, monthId, yearId)
    expect(document.getElementById(dayId).value).toEqual('')
    expect(document.getElementById(monthId).value).toEqual('')
    expect(document.getElementById(yearId).value).toEqual('')
  })
})

describe('test addPopulateDateListeners', () => {
  test('listeners added to control element', () => {
    const populateDateWithTodayElement = document.getElementById('control-id')
    addPopulateDateListeners(populateDateWithTodayElement)
  })
})
