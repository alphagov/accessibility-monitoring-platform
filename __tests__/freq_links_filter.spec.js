/**
 * @jest-environment jsdom
 */

const fs = require('fs')
const path = require('path')
const file = path.join(__dirname, './', 'freq_links_filter.html')
const bodyHtml = fs.readFileSync(file, { encoding: 'utf8', flag: 'r' })

document.body.innerHTML = bodyHtml

const {
  updateFreqLinkFiltering
} = require('../common/static/js/freq_links_filter')

describe('test audits check filter functions are present', () => {
  it.each([
    updateFreqLinkFiltering
  ])('%p is a function', (functionFromModule) => {
    expect(typeof functionFromModule).toBe('function')
  })
})

describe('test updateFreqLinkFiltering', () => {
  beforeEach(() => {
    document.getElementById('id_case_type_filter_3').checked = true // Set state filter to all
    document.getElementById('filter_summary').innerHTML = ''
  })

  test('check number of links', () => {
    updateFreqLinkFiltering()
    expect(document.getElementById('filter_summary').innerHTML).toEqual('Showing 8 links')
  })

  test('check number of simplified links', () => {
    document.getElementById('id_case_type_filter_0').checked = true
    updateFreqLinkFiltering()
    expect(document.getElementById('filter_summary').innerHTML).toEqual('Showing 5 links')
  })

  test('check number of detailed links', () => {
    document.getElementById('id_case_type_filter_1').checked = true
    updateFreqLinkFiltering()
    expect(document.getElementById('filter_summary').innerHTML).toEqual('Showing 3 links')
  })

  test('check number of mobile links', () => {
    document.getElementById('id_case_type_filter_2').checked = true
    updateFreqLinkFiltering()
    expect(document.getElementById('filter_summary').innerHTML).toEqual('Showing 2 links')
  })
})
