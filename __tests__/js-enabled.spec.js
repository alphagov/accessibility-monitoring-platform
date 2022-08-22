/* Check that print button is made visible when Javascript is enabled */

const { JSDOM } = require('jsdom')

const html = `<button id="print-button">Print</button>
<script src="../common/static/js/js-enabled.js"></script>`

describe('test js-enabled', () => {
  test('print button is visible when Javascript is enabled', () => {
    const dom = new JSDOM(html, { runScripts: 'dangerously', resources: 'usable' })
    dom.onload = () => {
      expect(dom.window.getElementById('print-button').classList).toEqual(['amp-display-block'])
    }
  })
})
