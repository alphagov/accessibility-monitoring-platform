/**
 * @jest-environment jsdom
 */

const fs = require('fs')
const path = require('path')
const file = path.join(__dirname, './', 'audits_retest_check_filter.html')
const bodyHtml = fs.readFileSync(file, { encoding: 'utf8', flag: 'r' })

document.body.innerHTML = bodyHtml

const {
  fixedFilter,
  brokenFilter,
  notRetestedFilter,
  textFilter,
  updateWcagList,
  updateValue
} = require('../common/static/js/audits_retest_check_filter')

describe('test audits retest check filter functions are present', () => {
  it.each([
    fixedFilter,
    brokenFilter,
    notRetestedFilter,
    textFilter,
    updateWcagList,
    updateValue
  ])('%p is a function', (functionFromModule) => {
    expect(typeof functionFromModule).toBe('function')
  })
})

describe('test fixedFilter', () => {
  it.each([
    ['remove', 'fixed', true, 'keyword-class', ''],
    ['remove', 'other', true, 'keyword-class', ''],
    ['remove', 'fixed', false, 'keyword-class', ''],
    ['remove', 'other', false, 'keyword-class', ''],
    ['add', 'fixed', true, 'other-class', 'other-classkeyword-class'],
    ['add', 'other', true, 'other-class', 'other-classkeyword-class'],
    ['preserve', 'fixed', false, 'other-class', 'other-class'],
    ['preserve', 'other', false, 'other-class', 'other-class']
  ])('%p class name: %p, %p, %p, %p', (behaviour, value, checked, divTagClass, expectedDivTagClass) => {
    const className = 'keyword-class'
    const mockquerySelector = jest.fn()
    mockquerySelector.mockReturnValueOnce(value)
    const divTag = {
      className: divTagClass,
      querySelector: mockquerySelector
    }
    fixedFilter(divTag, checked, className)
    expect(divTag.className).toEqual(expectedDivTagClass)
  })
})

describe('test brokenFilter', () => {
  it.each([
    ['remove', 'not-fixed', true, 'keyword-class', ''],
    ['remove', 'other', true, 'keyword-class', ''],
    ['remove', 'not-fixed', false, 'keyword-class', ''],
    ['remove', 'other', false, 'keyword-class', ''],
    ['add', 'not-fixed', true, 'other-class', 'other-classkeyword-class'],
    ['add', 'other', true, 'other-class', 'other-classkeyword-class'],
    ['preserve', 'not-fixed', false, 'other-class', 'other-class'],
    ['preserve', 'other', false, 'other-class', 'other-class']
  ])('%p class name: %p, %p, %p, %p', (behaviour, value, checked, divTagClass, expectedDivTagClass) => {
    const className = 'keyword-class'
    const mockquerySelector = jest.fn()
    mockquerySelector.mockReturnValueOnce(value)
    const divTag = {
      className: divTagClass,
      querySelector: mockquerySelector
    }
    brokenFilter(divTag, checked, className)
    expect(divTag.className).toEqual(expectedDivTagClass)
  })
})

describe('test notRetestedFilter', () => {
  it.each([
    ['remove', 'not-retested', true, 'keyword-class', ''],
    ['remove', 'other', true, 'keyword-class', ''],
    ['remove', 'not-retested', false, 'keyword-class', ''],
    ['remove', 'other', false, 'keyword-class', ''],
    ['add', 'not-retested', true, 'other-class', 'other-classkeyword-class'],
    ['add', 'other', true, 'other-class', 'other-classkeyword-class'],
    ['preserve', 'not-retested', false, 'other-class', 'other-class'],
    ['preserve', 'other', false, 'other-class', 'other-class']
  ])('%p class name: %p, %p, %p, %p', (behaviour, value, checked, divTagClass, expectedDivTagClass) => {
    const className = 'keyword-class'
    const mockquerySelector = jest.fn()
    mockquerySelector.mockReturnValueOnce(value)
    const divTag = {
      className: divTagClass,
      querySelector: mockquerySelector
    }
    notRetestedFilter(divTag, checked, className)
    expect(divTag.className).toEqual(expectedDivTagClass)
  })
})

describe('test textFilter', () => {
  let spy

  beforeAll(() => {
    spy = jest.spyOn(document, 'getElementById')
  })

  it.each([
    ['preserve', 'keyword', 'no-matching-key', 'other-class text-filter', 'other-class text-filter'],
    ['remove', '', 'no-matching-key', 'other-class text-filter', 'other-class'],
    ['remove', 'keyword', 'matching-keyword', 'other-class text-filter', 'other-class'],
    ['remove', '', 'matching-keyword', 'other-class text-filter', 'other-class'],
    ['add', 'keyword', 'no-matching-key', 'other-class', 'other-class text-filter'],
    ['no', '', 'no-matching-key', 'other-class', 'other-class'],
    ['no', 'keyword', 'matching-keyword', 'other-class', 'other-class'],
    ['no', '', 'matching-keyword', 'other-class', 'other-class']
  ])('%p text-filter class: %p, %p, %p, %p', (behaviour, keyword, divTagId, divTagClass, expectedDivTagClass) => {
    spy.mockReturnValue({ value: keyword })
    const divTag = {
      id: divTagId,
      className: divTagClass
    }
    textFilter(divTag, keyword)
    expect(divTag.className).toEqual(expectedDivTagClass)
  })
})

describe('test updateWcagList', () => {
  test('error count updated', () => {
    document.getElementById('number_of_errors').innerHTML = ''
    updateWcagList()
    expect(document.getElementById('number_of_errors').innerHTML).toEqual('Showing 4 errors')
  })
})

describe('test updateValue', () => {
  test('error count updated', () => {
    document.getElementById('number_of_errors').innerHTML = ''
    const mockEvent = {}
    updateValue(mockEvent)
    expect(document.getElementById('number_of_errors').innerHTML).toEqual('Showing 4 errors')
  })
})
