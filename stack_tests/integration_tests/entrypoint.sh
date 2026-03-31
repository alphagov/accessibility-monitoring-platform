#!/bin/sh
cd /cypress
npm install
cd /
NO_COLOR=1 cypress run
