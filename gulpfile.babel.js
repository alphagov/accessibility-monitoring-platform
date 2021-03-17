const gulp = require('gulp')
const babel = require('gulp-babel')
const sass = require('gulp-sass')
const del = require('del')
const browserSync = require('browser-sync')
const uglify = require('gulp-uglify')
const browserify = require('browserify')
const babelify = require('babelify')
const plumber = require('gulp-plumber')
const source = require('vinyl-source-stream')
const buffer = require('vinyl-buffer')
const sourcemaps = require('gulp-sourcemaps')
const csso = require('gulp-csso')
const autoprefixer = require('gulp-autoprefixer')
const modifyCssUrls = require('gulp-modify-css-urls')


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
  dist: 'dist',
  ignore: '!accessibility_monitoring_platform/static/compiled'
}

gulp.task('javascripts', function () {
  const b = browserify({
    entries: paths.javascript.manifest,
    debug: true,
  });

  return b
    .transform("babelify", {presets: ["@babel/preset-env"]})
    .bundle()
    .pipe(source("app.js"))
    .pipe(buffer())
    .pipe(sourcemaps.init({loadMaps: true}))
    .pipe(uglify())
    .pipe(sourcemaps.write("./"))
    .pipe(gulp.dest(paths.javascript.dist));
})

const sassOpts = {
  outputStyle: 'extended',
  errLogToConsole: true,
  includePaths: 'node_modules'
}

gulp.task('stylesheets', () => {
  return gulp.src(paths.stylesheets.src)
    .pipe(sass(sassOpts))
    .pipe(modifyCssUrls({
      modify(url, filePath) {
        return `..${url}`;
      }
    }))
    .pipe(autoprefixer('last 2 versions'))
    .pipe(csso({
      restructure: true,
      sourceMap: true,
      debug: true
    }))
    .pipe(sourcemaps.write('.'))
    .pipe(gulp.dest(paths.stylesheets.dist))
})

gulp.task('clean', () =>
  del([`${paths.javascript.dist}/*.*`, `${paths.stylesheets.dist}/*.*`]).then(dirs =>
    console.log(`Deleted files and folders:\n ${dirs.join('\n')}`)
  )
)

gulp.task('browserSync', function () {
  browserSync.init({
    notify: false,
    proxy: 'localhost:8081'
  })
})

gulp.task('watch', (done) => {
  gulp.watch(
    [
      'accessibility_monitoring_platform/**/*.{scss,css,html,py,js}',
      '!node_modules/**',
      '!accessibility_monitoring_platform/static/dist/**'
    ]
  ).on(
    'change',
    gulp.series('clean', 'javascripts', 'stylesheets', 'copy-assets', browserSync.reload)
  )
  done()
})

var _getAllFilesFromFolder = function(dir) {
  var filesystem = require("fs");
  var results = [];
  filesystem.readdirSync(dir).forEach(function(file) {
      file = dir+'/'+file;
      var stat = filesystem.statSync(file);
      if (stat && stat.isDirectory()) {
          results = results.concat(_getAllFilesFromFolder(file))
      } else results.push(file);
  });
  return results;
};

const getFilename = (v, i, a) => v.split("/").slice(-1)[0]

const arraysEqual = (a1, a2) => JSON.stringify(a1)==JSON.stringify(a2)

gulp.task('copy-assets', (done) => {
  try {
    const sourceDir = 'node_modules/govuk-frontend/govuk/assets'
    const destDir = 'accessibility_monitoring_platform/static/compiled/assets'
    const sourceFilePaths = _getAllFilesFromFolder(sourceDir)
    const destFilePaths = _getAllFilesFromFolder(destDir)
  
    const sourceFiles = sourceFilePaths.map(getFilename)
    const destFiles = destFilePaths.map(getFilename)
  
    if (arraysEqual(sourceFiles, destFiles)) {
      console.log('No change in assets')
      done()
    } 
  }
  catch(err) {
    console.log(err.message)
  }
  console.log('Change in assets')
  return gulp.src(['node_modules/govuk-frontend/govuk/assets*/**/*']).pipe(gulp.dest('accessibility_monitoring_platform/static/compiled'));
})

gulp.task('build', gulp.series('clean', 'javascripts', 'stylesheets', 'copy-assets'))

gulp.task('serve', gulp.series('build', gulp.parallel('browserSync', 'watch')))
