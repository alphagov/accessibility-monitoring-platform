/**
 * @jest-environment jsdom
 */

const fs = require('fs')
const path = require('path')
const file = path.join(__dirname, './', 'audits_check_filter.html')
const bodyHtml = fs.readFileSync(file, { encoding: 'utf8', flag: 'r' })

document.body.innerHTML = bodyHtml

const {
  resetFilterForm,
  updateCheckListFiltering
} = require('../common/static/js/audits_check_filter')

describe('test audits check filter functions are present', () => {
  it.each([
    resetFilterForm,
    updateCheckListFiltering,
  ])('%p is a function', (functionFromModule) => {
    expect(typeof functionFromModule).toBe('function')
  })
})

describe('test resetFilterForm', () => {
  test('check filters reset to initial values', () => {
    document.getElementById('id_name').value = 'contrast'
    document.getElementById('id_type_filter_1').checked = true
    document.getElementById('id_state_filter_2').checked = true
    document.getElementById('number_of_errors').innerHTML = ''
    const mockEvent = { preventDefault: jest.fn }
    resetFilterForm(mockEvent)
    expect(document.getElementById('id_name').value).toEqual('')
    expect(document.getElementById('id_type_filter_3').checked).toEqual(true)
    expect(document.getElementById('id_state_filter_3').checked).toEqual(true)
    expect(document.getElementById('number_of_errors').innerHTML).toEqual('Showing 78 errors')
  })
})

describe('test updateCheckListFiltering', () => {
  beforeEach(() => {
    document.getElementById('id_name').value = ''
    document.getElementById('id_type_filter_3').checked = true // Set type filter to all
    document.getElementById('id_state_filter_3').checked = true // Set state filter to all
    document.getElementById('number_of_errors').innerHTML = ''
  })

  test('check total number of errors', () => {
    updateCheckListFiltering()
    expect(document.getElementById('number_of_errors').innerHTML).toEqual('Showing 78 errors')
  })

  test('check number of axe errors', () => {
    document.getElementById('id_type_filter_1').checked = true
    updateCheckListFiltering()
    expect(document.getElementById('number_of_errors').innerHTML).toEqual('Showing 56 errors')
  })

  test('check number of errors not tested', () => {
    document.getElementById('id_state_filter_2').checked = true
    updateCheckListFiltering()
    expect(document.getElementById('number_of_errors').innerHTML).toEqual('Showing 72 errors')
  })

  test('check number of contrast errors', () => {
    document.getElementById('id_name').value = 'contrast'
    updateCheckListFiltering()
    expect(document.getElementById('number_of_errors').innerHTML).toEqual('Showing 3 errors')
  })
})
