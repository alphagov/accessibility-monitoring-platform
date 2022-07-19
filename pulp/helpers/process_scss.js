const sass = require('sass')
const postcss = require('postcss')
const cssnano = require('cssnano')
const autoprefixer = require('autoprefixer')
const fs = require('fs')
const path = require('path')

const processScss = async (scssFilePath, destFile) => {
  const parentFile = path.dirname(destFile)
  if (!fs.existsSync(parentFile)) {
    fs.mkdirSync(parentFile, { recursive: true })
  }

  const css = sass.renderSync({ file: scssFilePath })
  const output = await postcss([cssnano, autoprefixer]).process(css.css.toString())
  const finalCss = output.css.replaceAll('/assets/', '/static/assets/')
  fs.writeFile(destFile, finalCss, err => {
    if (err) console.error(err)
  })
}

module.exports = processScss
