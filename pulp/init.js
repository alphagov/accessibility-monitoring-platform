const path = require('path')
const fs = require('fs')
const { exec } = require('child_process')
const watch = require('node-watch')
require('dotenv').config()

const getAllFilesInDir = require('./helpers/get_all_files')
const processScss = require('./helpers/process_scss')
const processJavascript = require('./helpers/process_js')
const copyFolderRecursiveSync = require('./helpers/recursively_copy')
const removeAllFilesInDir = require('./helpers/clean_up.js')

const jsonSettingsPath = process.argv.find(element => element.includes('.json'))
const watchFiles = (process.argv.find(a => a.includes('--nowatch')) === '--nowatch')

const settings = require(jsonSettingsPath)
const toWatch = []
Object.keys(settings).forEach(key => toWatch.push(settings[key].toWatch))

function processStaticFiles (name) {
  console.time('processStaticFiles')

  // Processes CSS files
  if (name.includes(settings.css.toWatch)) {
    console.log('>>> Processing SCSS file')
    removeAllFilesInDir(settings.css.dest)
    processScss(settings.css.access_point, settings.css.dest)
  }

  // // Processes JS files
  if (name.includes(settings.js.toWatch)) {
    console.log(`>>> Processing ${name}`)
    const files = getAllFilesInDir(settings.js.toWatch)
    removeAllFilesInDir(settings.js.dest)
    files.forEach(f => {
      const filename = path.basename(f)
      const additionalDir = f.replace(settings.js.toWatch, '')
        .replace(filename, '')
        .replace('/', '')
      const finalPath = `${settings.js.dest}/${additionalDir}`
      if (!fs.existsSync(finalPath)) {
        fs.mkdirSync(finalPath, { recursive: true })
      }
      processJavascript(f, finalPath)
    })
  }

  // // // Processes gov uk static files
  if (name.includes(settings.static.toWatch)) {
    console.log('>>> Processing static files')
    removeAllFilesInDir(settings.static.dest)
    copyFolderRecursiveSync(settings.static.toWatch, settings.static.dest)
  }

  // // Processes custom image files
  if (name.includes(settings.static_img.toWatch)) {
    console.log('>>> Processing custom image files')
    removeAllFilesInDir(settings.static_img.dest)
    copyFolderRecursiveSync(settings.static_img.toWatch, settings.static_img.dest)
  }
  console.timeEnd('processStaticFiles')
}

function collectStatic () {
  exec('make collect_static', (error, stdout, stderr) => {
    if (error) {
      console.log(`error: ${error.message}`)
      return
    }
    if (stderr) {
      console.log(`stderr: ${stderr}`)
      return
    }
    console.log(`stdout: ${stdout}`)
  })
}

const files = getAllFilesInDir(settings.js.toWatch)
files.push(settings.css.access_point)
files.push(settings.static_img.toWatch)
files.push(settings.static.toWatch)

files.forEach(element => processStaticFiles(element))
collectStatic()

if (watchFiles) {
  console.log('>>> In watch mode')
  watch(toWatch, { recursive: true }, function (evt, name) {
    processStaticFiles(name)
    collectStatic()
  })
}
