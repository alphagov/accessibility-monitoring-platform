/* global cy */

const username = 'auditor@email.com'
const password = 'secret'

describe('Login', () => {
  it('Can login through the UI', function () {
    cy.visit('/account/login/')
    cy.get('input[name="auth-username"]').type(username)
    cy.get('input[name="auth-password"]').type(password)
    cy.get('form').submit()
    cy.getCookie('sessionid').should('exist')
  })
})

// describe('Login', () => {
//   it('Can login through the UI', function () {
//     cy.visit('/account/login/')

//     cy.get('[name=csrfmiddlewaretoken]')
//       .should('exist')
//       .should('have.attr', 'value')
//       .as('csrfToken')

//     cy.get('@csrfToken').then((token) => {
//       cy.request({
//         method: 'POST',
//         url: '/account/login/',
//         form: true,
//         body: {
//           username: username,
//           password: password,
//           csrfmiddlewaretoken: token
//         }
//       })
//     })

//     cy.getCookie('sessionid').should('exist')
//   })
// })
