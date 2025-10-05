release: python manage.py collectstatic --noinput
web: gunicorn ILEFN.wsgi --bind 0.0.0.0:8080 --log-file -
