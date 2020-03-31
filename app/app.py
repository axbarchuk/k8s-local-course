from __future__ import print_function
import os
import time
import logging
import socket
from flask import Flask
from redis import Redis, RedisError
from flask import Markup
from flask import render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

log = logging.getLogger('werkzeug')

app = Flask(__name__)

# Connect to Redis
redis = Redis(host=os.environ.get('REDIS_NAME', 'redis'), db=0, socket_connect_timeout=2, socket_timeout=2)


db_uri = 'mysql://root:{}@{}/db'.format(os.environ.get('DB_PASSWORD', 'supersecure'), os.environ.get('DB_NAME', 'db'))
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
db = SQLAlchemy(app)


class Visits(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    visits = db.Column(db.Integer)

    def __init__(self, visits):
        self.visits = visits

    def __repr__(self):
        return '<Id: {}: visits:{}>'.format(self.id, str(self.visits))



@app.route("/init")
def init():
    db.create_all()
    first = Visits(0)
    db.session.add(first)
    db.session.commit()
    return 'OK'


@app.route("/")
def hello():
    hostname = socket.gethostname()
    mysql_result = False
    redis_result = False
    m_visits = 0

    try:
        visits = redis.incr("counter")
        redis_result = True
    except RedisError as r_err:
        visits = "<i>cannot connect to Redis, counter disabled</i>"
        log.error(r_err)

    try:
        if db.session.query("1").from_statement(text("SELECT 1")).all():
            mysql_result = True
        v = Visits.query.filter_by(id=1).first()
        if isinstance(visits, int):
            v.visits += 1
            m_visits = v.visits
            db.session.add(v)
            db.session.commit()
        else:
            m_visits = v.visits
    except Exception as ex:
        log.error(ex)

    return render_template('index.html', hostname=hostname, mysql_result=mysql_result, redis_result=redis_result, visits=visits, m_visits=m_visits)

if __name__ == "__main__":
    time.sleep(float(os.environ.get('APP_READY', 0)))
    app.run(host='0.0.0.0', port=80)
