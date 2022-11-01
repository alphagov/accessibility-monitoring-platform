#!/bin/sh
npm install --no-optional --prefix /cypress/support/ axe-core@4.5.0 cypress-axe@1.0.0
cypress run
