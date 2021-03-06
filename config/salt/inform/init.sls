include:
  - app.virtualenv
  - app.supervisor
  - github
  - gunicorn
  - logs
  - nginx.config

extend:
  supervisor:
    pip.installed:
      - require:
        - virtualenv: app-virtualenv

  nginx:
    service.running:
      - watch:
        - file: /etc/nginx/conf.d/http.conf
        - file: /etc/nginx/conf.d/proxy.conf
        - file: /etc/nginx/sites-available/inform.conf

  app-virtualenv:
    virtualenv.managed:
      - requirements: /srv/inform/config/requirements.txt

  app-log-directory:
    file.directory:
      - require_in:
        - service: supervisor

  inform-supervisor-service:
    supervisord.running:
      - watch:
        - file: /etc/supervisor/conf.d/inform.conf
        - file: /etc/gunicorn.d/inform.conf.py

  gunicorn-config:
    file.managed:
      - context:
          gunicorn_port: {{ pillar['gunicorn_port'] }}

  {% if grains.get('env', '') == 'prod' %}
  /etc/nginx/sites-available/inform.conf:
    file.managed:
      - context:
          server_name: {{ pillar['hostname'] }}
          root: /srv/inform
  {% endif %}


flask-app-config:
  file.managed:
    - name: /srv/inform/inform/flask.conf.py
    - source: salt://inform/flask.conf.py
    - template: jinja
    - user: {{ pillar['app_user'] }}
    - group: {{ pillar['app_user'] }}
    - require:
      - git: git-clone-app
    - require_in:
      - service: supervisor

sqlite3:
  pkg.installed

sqlalchemy-init:
  cmd.run:
    - name: /home/{{ pillar['app_user'] }}/.virtualenvs/inform/bin/python manage.py init_db
    - unless: test -f /srv/inform/inform.sqlitedb
    - cwd: /srv/inform
    - user: {{ pillar['app_user'] }}
    - require:
      - pkg: sqlite3
      - file: flask-app-config
    - require_in:
      - service: supervisor

memcached:
  pkg.installed
