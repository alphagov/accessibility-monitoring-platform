/**
 * @jest-environment jsdom
 */

const fs = require('fs')
const path = require('path')
const file = path.join(__dirname, './', 'audits_check_filter.html')
const bodyHtml = fs.readFileSync(file, { encoding: 'utf8', flag: 'r' })

document.body.innerHTML = bodyHtml

const {
  bodyListener,
  updateCheckListFiltering,
  updateChecksListener,
  updateNotTestedCounts
} = require('../common/static/js/audits_check_filter')

describe('test audits check filter functions are present', () => {
  it.each([
    bodyListener,
    updateCheckListFiltering,
    updateChecksListener,
    updateNotTestedCounts
  ])('%p is a function', (functionFromModule) => {
    expect(typeof functionFromModule).toBe('function')
  })
})

describe('test updateNotTestedCounts', () => {
  test('check type counts calculated', () => {
    updateNotTestedCounts()
    expect(document.querySelector('label[for=id_type_filter_0]').innerHTML).toEqual('Manual tests (14 not tested)')
    expect(document.querySelector('label[for=id_type_filter_1]').innerHTML).toEqual('Axe tests (54 not tested)')
    expect(document.querySelector('label[for=id_type_filter_2]').innerHTML).toEqual('PDF (4 not tested)')
  })
})
