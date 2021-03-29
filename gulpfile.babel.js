const autoprefixer = require('gulp-autoprefixer')
const browserify = require('browserify')
const browserSync = require('browser-sync')
const buffer = require('vinyl-buffer')
const csso = require('gulp-csso')
const del = require('del')
const dotenv = require('dotenv')
const fs = require('fs')
const gulp = require('gulp')
const gulpif = require('gulp-if')
const modifyCssUrls = require('gulp-modify-css-urls')
const replace = require('gulp-replace');
const sass = require('gulp-sass')
const source = require('vinyl-source-stream')
const sourcemaps = require('gulp-sourcemaps')
const uglify = require('gulp-uglify')

dotenv.config()

const paths = {
  javascript: {
    src: ['accessibility_monitoring_platform/static/js/*.js'],
    manifest: 'accessibility_monitoring_platform/static/js/index.js',
    dist: 'accessibility_monitoring_platform/static/compiled/js'
  },
  stylesheets: {
    src: ['accessibility_monitoring_platform/static/scss/*.scss'],
    dist: 'accessibility_monitoring_platform/static/compiled/css'
  },
  static: 'accessibility_monitoring_platform/static/compiled/',
  ignore: '!accessibility_monitoring_platform/static/compiled'
}

// Gulp task to transpile javascript code to static
gulp.task('javascripts', function () {
  const b = browserify({
    entries: paths.javascript.manifest,
    debug: true
  })

  return b
    .transform('babelify', { presets: ['@babel/preset-env'] })
    .bundle()
    .pipe(source('app.js'))
    .pipe(buffer())
    .pipe(sourcemaps.init({ loadMaps: true }))
    .pipe(uglify())
    .pipe(gulpif(process.env.DEBUG === 'TRUE', sourcemaps.write('./')))
    .pipe(gulp.dest(paths.javascript.dist))
})

// Gulp task to compile SCSS to CSS
gulp.task('stylesheets', () => {
  return gulp.src(paths.stylesheets.src)
    .pipe(sass({
      outputStyle: 'extended',
      errLogToConsole: true,
      includePaths: 'node_modules'
    }))
    .pipe(modifyCssUrls({
      modify (url, filePath) {
        return `..${url}`
      }
    }))
    .pipe(autoprefixer('last 2 versions'))
    .pipe(csso({
      restructure: true,
      sourceMap: true,
      debug: true
    }))
    .pipe(replace('::-webkit-details-marker', '::marker'))
    .pipe(gulpif(process.env.DEBUG === 'TRUE', sourcemaps.write('.')))
    .pipe(gulp.dest(paths.stylesheets.dist))
})

// Deletes old javascript and CSS files
gulp.task('clean', () =>
  del([`${paths.javascript.dist}/*.*`, `${paths.stylesheets.dist}/*.*`]).then(
    dirs => console.log(`Deleted files and folders:\n ${dirs.join('\n')}`)
  )
)

// Starts Browsersync
gulp.task('browserSync', function () {
  browserSync.init({
    notify: false,
    proxy: 'localhost:8081'
  })
})

// Watches for changes in Python, HTML, Javascript and SCSS files
gulp.task('watch', (done) => {
  gulp.watch(
    [
      'accessibility_monitoring_platform/**/*.{scss,css,html,py,js}',
      '!node_modules/**',
      '!accessibility_monitoring_platform/static/dist/**',
      '!accessibility_monitoring_platform/static/compiled/assets/**',
      '!accessibility_monitoring_platform/static/compiled/js/*.js'
    ]
  ).on(
    'change',
    gulp.series('clean', 'javascripts', 'stylesheets', 'copy-assets', browserSync.reload)
  )
  done()
})

// Gets all files and sub directories within directory
const _getAllFilesFromFolder = function (dir) {
  let results = []
  fs.readdirSync(dir).forEach(function (file) {
    file = dir + '/' + file
    const stat = fs.statSync(file)
    if (stat && stat.isDirectory()) {
      results = results.concat(_getAllFilesFromFolder(file))
    } else results.push(file)
  })
  return results
}

// Gets file name from directory string
const getFilename = (v, i, a) => v.split('/').slice(-1)[0]

// Copies assets from Gov UK front end library to local static directory.
gulp.task('copy-assets', (done) => {
  try {
    const sourceDir = 'node_modules/govuk-frontend/govuk/assets'
    const destDir = 'accessibility_monitoring_platform/static/compiled/assets'
    if (!fs.existsSync(destDir)) fs.mkdirSync('accessibility_monitoring_platform/static/compiled')
    if (!fs.existsSync(destDir)) fs.mkdirSync(destDir)
    const sourceFilePaths = _getAllFilesFromFolder(sourceDir)
    const destFilePaths = _getAllFilesFromFolder(destDir)

    const sourceFiles = sourceFilePaths.map(getFilename)
    const destFiles = destFilePaths.map(getFilename)

    const missingFiles = sourceFiles.filter(v => !destFiles.includes(v))

    missingFiles.forEach(filename => {
      const index = sourceFiles.findIndex(x => x === filename)
      const copySource = sourceFilePaths[index]
      const ext = copySource.replace(sourceDir, '')
      const copyDest = `${destDir}${ext}`
      const subDir = copyDest.replace(filename, '')

      fs.mkdir(subDir, { recursive: true }, (err) => { if (err) throw err })

      fs.copyFile(
        copySource,
        copyDest,
        (err) => {
          if (err) throw err
          console.log('File was copied to destination')
        }
      )
    })

    done()
  } catch (err) {
    console.log(err.message)
  }
})

// Builds the assets, Javascript, and CSS files
gulp.task('build', gulp.series('clean', 'javascripts', 'stylesheets', 'copy-assets'))

// Starts browsersync and will recompile the files when it detects a change
gulp.task('serve', gulp.series('build', gulp.parallel('browserSync', 'watch')))
