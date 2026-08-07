# Comando de arranque. Nota: com o builder Railpack (o default no Railway) é o
# "startCommand" do railpack.json que manda; este Procfile é o fallback para
# outros builders. As migrações correm no arranque (a BD só está acessível em
# runtime); o build do React e o collectstatic são feitos na fase de build.
web: python manage.py migrate --no-input && gunicorn config.wsgi --bind 0.0.0.0:$PORT
