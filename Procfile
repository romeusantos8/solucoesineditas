web: npm ci --prefix frontend && npm run build --prefix frontend && python manage.py collectstatic --no-input && python manage.py migrate --no-input && gunicorn config.wsgi --bind 0.0.0.0:$PORT
