'use strict'

const puppeteer = require('puppeteer')
const lighthouse = require('lighthouse')
const fs = require('fs')

// This port will be used by Lighthouse later. The specific port is arbitrary.
const PORT = 8042
const baseUrl = 'http://localhost:8081'

// Collects links whilst authenticated in JS object below
let authLinks = {
  pagesToVisit: [],
  pagesVisited: []
}

// Collects links whilst not authenticated in JS object below
let noAuthLinks = {
  pagesToVisit: [],
  pagesVisited: []
}

/**
* @param {import('puppeteer').Browser} browser
* @param {string} origin
*/
async function login (page, origin) {
  await page.goto(origin)
  await page.waitForSelector('input[type="password"]', {
    visible: true,
    timeout: 2000
  })

  // Fill in and submit login form.
  const emailInput = await page.$('input[type="text"]')
  await emailInput.type('admin@email.com')
  const passwordInput = await page.$('input[type="password"]')
  await passwordInput.type('secret')
  await Promise.all([
    page.$eval('.login-form', form => form.submit()),
    page.waitForNavigation()
  ])
}

/**
* @param {puppeteer.Browser} browser
* @param {string} origin
*/
async function logout (page, origin) {
  await page.goto(`${origin}/accounts/logout`)
}

// Imports text file as array
function importTextFileAsArray (path) {
  const text = fs.readFileSync(path).toString('utf-8')
  return text.split('\n').filter(item => item !== '')
}

// Writes object as Json
function writeJson (filepath, data) {
  fs.writeFile(
    filepath,
    JSON.stringify(data, null, 2),
    function (err) { if (err) console.log(err) }
  )
}

// Crawls the web app and collects hyperlinks
async function crawlWebsite (page, loggedIn) {
  const linkLogger = (loggedIn) ? authLinks : noAuthLinks
  while (true) {
    let e = null
    for (let i = 0; i < linkLogger.pagesToVisit.length; i++) {
      e = linkLogger.pagesToVisit[i]

      console.log('>>> Processing', e)

      try {
        if (loggedIn) {
          await login(page, baseUrl)
        } else {
          await logout(page, baseUrl)
        }
      } catch (err) {
        console.log(err)
      }

      await page.goto(e)

      const hrefs = await page.$$eval('a', as => as.map(a => a.href))
      const localHrefs = hrefs.filter(word => word.includes(baseUrl))

      // Remove links that are in toVisit
      let hrefsRemoved = localHrefs.filter(el => !linkLogger.pagesToVisit.includes(el))

      // Remove links that are in visited
      hrefsRemoved = hrefsRemoved.filter(el => !linkLogger.pagesVisited.includes(el))

      // Removes duplicates
      hrefsRemoved = [...new Set(hrefsRemoved)]

      // Add links to toVisit
      linkLogger.pagesToVisit.push(...hrefsRemoved)

      // Delete page from toVisit
      linkLogger.pagesToVisit = linkLogger.pagesToVisit.filter(item => item !== e)

      // Add page to visited
      linkLogger.pagesVisited.push(e)
    }

    if (linkLogger.pagesToVisit.length === 0) {
      if (loggedIn) {
        authLinks = linkLogger
      } else {
        noAuthLinks = linkLogger
      }
      return
    }
  }
}

// main function
async function main () {
  // Direct Puppeteer to open Chrome with a specific debugging port.
  const browser = await puppeteer.launch({
    args: [`--remote-debugging-port=${PORT}`],
    headless: true,
    slowMo: 50
  })
  const page = await browser.newPage()

  noAuthLinks.pagesToVisit.push(baseUrl)
  authLinks.pagesToVisit.push(baseUrl)

  console.log('>>> Crawling with auth')
  await crawlWebsite(page, true)

  console.log('>>> Crawling without auth')
  await crawlWebsite(page, false)

  const textByLine = importTextFileAsArray('./lighthouse-tests/specific-domains.txt')
  for (let i = textByLine.length; i--;) textByLine[i] = baseUrl + textByLine[i]
  noAuthLinks.pagesVisited.push(...textByLine)
  authLinks.pagesVisited.push(...textByLine)

  // Iterates through the auth hyperlinks and audits in Lighthouse
  console.log('>>> Logged in audit')
  let results = {}
  for (let i = 0; i < authLinks.pagesVisited.length; i++) {
    const url = authLinks.pagesVisited[i]
    console.log('>>> Auditing ' + url)
    try {
      await page.goto(url)
      await login(page, 'http://localhost:8081')
    } catch (error) {
      console.log('Did not defer to login')
    }
    const result = await lighthouse(url, { port: PORT, disableStorageReset: false })
    results[url] = {
      performance: result.lhr.categories.performance.score,
      accessibility: result.lhr.categories.accessibility.score,
      'best-practices': result.lhr.categories['best-practices'].score,
      seo: result.lhr.categories.seo.score,
      pwa: result.lhr.categories.pwa.score
    }
  }
  writeJson('lighthouse-tests/results_auth.json', results)

  // Iterates through the no auth hyperlinks and audits in Lighthouse
  console.log('>>> Logged out audit')
  results = {}
  for (let i = 0; i < noAuthLinks.pagesVisited.length; i++) {
    const url = noAuthLinks.pagesVisited[i]
    console.log('>>> Auditing ' + url)
    await logout(page, baseUrl)
    const result = await lighthouse(url, { port: PORT, disableStorageReset: false })
    results[url] = {
      performance: result.lhr.categories.performance.score,
      accessibility: result.lhr.categories.accessibility.score,
      'best-practices': result.lhr.categories['best-practices'].score,
      seo: result.lhr.categories.seo.score,
      pwa: result.lhr.categories.pwa.score
    }
  }
  writeJson('lighthouse-tests/results_noAuth.json', results)

  await browser.close()
}

if (require.main === module) {
  main()
} else {
  module.exports = {
    login,
    logout
  }
}
