const browserify = require('browserify')
const babelify = require('babelify')
const UglifyJS = require('uglify-js')

const myArgs = process.argv.slice(2)

const b = browserify({ entries: myArgs[0], standalone: 'platform' })

const res = b.transform(babelify, { presets: ['@babel/preset-env'] })
res.bundle((err, buffer) => {
  if (err) {
    console.dir(err)
    return
  }
  const res = UglifyJS.minify(buffer.toString())
  console.log(res.code)
})
