const { defineConfig } = require('cypress')

module.exports = defineConfig({
  e2e: {
    supportFile: false,
    baseUrl: 'http://localhost:8081/',
    specPattern: 'cypress/*.cy.js',
    chromeWebSecurity: false
  }
})
