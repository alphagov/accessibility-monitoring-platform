const gulp = require('gulp')
const source = require('vinyl-source-stream')
const browserify = require('browserify')
const buffer = require('vinyl-buffer')
const sourcemaps = require('gulp-sourcemaps')
const babelify = require('babelify')
const uglify = require('gulp-uglify')
const rename = require('gulp-rename')
const fs = require('fs')

function prodMode (fileSrc, fileDest) {
  browserify(fileSrc, { debug: true })
    .transform(babelify, { presets: ['@babel/preset-env'] })
    .bundle()
    .pipe(source(fileSrc))
    .pipe(buffer())
    .pipe(uglify())
    .pipe(rename({ dirname: '' }))
    .pipe(gulp.dest(fileDest, { sourcemaps: false, overwrite: true }))
}

function debugMode (fileSrc, fileDest) {
  browserify(fileSrc, { debug: true })
    .transform(babelify, { presets: ['@babel/preset-env'] })
    .bundle()
    .pipe(source(fileSrc))
    .pipe(buffer())
    .pipe(sourcemaps.init({ loadMaps: true }))
    .pipe(sourcemaps.write('.'))
    .pipe(rename({ dirname: '' }))
    .pipe(gulp.dest(fileDest, { sourcemaps: true, overwrite: true }))
}

function processJavascript (fileSrc, fileDest) {
  if (!fs.existsSync(fileSrc)) {
    throw new Error('File does not exist')
  }
  if (process.env.DEBUG === 'TRUE') {
    console.log('>>> debug mode')
    debugMode(fileSrc, fileDest)
  } else {
    console.log('>>> production mode')
    prodMode(fileSrc, fileDest)
  }
}

module.exports = processJavascript
