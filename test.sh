echo $APP_PLATFORM

if [ "$APP_PLATFORM" = "TRUE" ]
then
    echo "Setting up amp"
    python manage.py migrate
    python manage.py recache_statuses
    waitress-serve --port=8001 accessibility_monitoring_platform.wsgi:application
else
    echo "Setting up viewer"
    waitress-serve --port=8001 report_viewer.wsgi:application
fi