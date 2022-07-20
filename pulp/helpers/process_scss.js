const sass = require('sass')
const postcss = require('postcss')
const cssnano = require('cssnano')
const autoprefixer = require('autoprefixer')
const fs = require('fs')

const processScss = async (scssFilePath, destPath) => {
  const css = sass.renderSync({ file: scssFilePath })
  const output = await postcss([cssnano, autoprefixer]).process(css.css.toString())
  const finalCss = output.css.replaceAll('/assets/', '/static/assets/')
  const destFile = `${destPath}init.css`
  if (!fs.existsSync(destPath)) {
    fs.mkdirSync(destPath, { recursive: true })
  }
  fs.writeFile(destFile, finalCss, err => {
    if (err) console.error(err)
  })
}

module.exports = processScss
