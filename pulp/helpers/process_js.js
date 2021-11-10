const gulp = require('gulp')
const source = require('vinyl-source-stream')
const browserify = require('browserify')
const buffer = require('vinyl-buffer')
const sourcemaps = require('gulp-sourcemaps')
const babelify = require('babelify')
const uglify = require('gulp-uglify')
const rename = require('gulp-rename')
require('dotenv').config()

const myArgs = process.argv.slice(2)

const file = myArgs[0]
const dest = myArgs[1]

gulp.task('build_prod', function () {
  return browserify(file, { debug: true })
    .transform(babelify, { presets: ['@babel/preset-env'] })
    .bundle()
    .pipe(source(file))
    .pipe(buffer())
    .pipe(uglify())
    .pipe(rename({ dirname: '' }))
    .pipe(gulp.dest(dest, { sourcemaps: false, overwrite: true }))
})

gulp.task('build_local', function () {
  return browserify(file, { debug: true })
    .transform(babelify, { presets: ['@babel/preset-env'] })
    .bundle()
    .pipe(source(file))
    .pipe(buffer())
    .pipe(sourcemaps.init({ loadMaps: true }))
    .pipe(sourcemaps.write('.'))
    .pipe(rename({ dirname: '' }))
    .pipe(gulp.dest(dest, { sourcemaps: true, overwrite: true }))
})

if (process.env.DEBUG === 'TRUE') {
  console.log('>>> debug mode')
  gulp.series(gulp.task('build_local'))()
} else {
  console.log('>>> production mode')
  gulp.series(gulp.task('build_prod'))()
}
