const fs = require('fs')

function removeAllFilesInDir (directory) {
  // Removes all files inside given directory
  if (fs.existsSync(directory)) {
    fs.rmSync(directory, { recursive: true, force: true })
  }
}

module.exports = removeAllFilesInDir
