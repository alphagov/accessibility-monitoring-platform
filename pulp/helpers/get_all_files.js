const path = require('path')
const fs = require('fs')

function getAllFilesInDirAsArray (dir) {
  // Recurses through directory and returns the address for all the files in directory
  const files = []
  function ThroughDirectory (directory) {
    fs.readdirSync(directory).forEach(File => {
      const Absolute = path.join(directory, File)
      if (fs.statSync(Absolute).isDirectory()) {
        ThroughDirectory(Absolute)
      } else {
        return files.push(Absolute)
      }
    })
  }
  ThroughDirectory(dir)
  return files
}

module.exports = getAllFilesInDirAsArray
