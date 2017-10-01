# [START app]
import logging
from flask import Flask, render_template

from google.appengine.api import memcache

from models import query_db, store_in_db
from weather_request import get_weather_scores


app = Flask(__name__)

@app.route('/')
def show_scores():
    weather_scores = memcache.get('weather_scores')
    if weather_scores is None:
        weather_scores = query_db()
        memcache.set('weather_scores', weather_scores)
        
    return render_template('index.html', 
                           weather_scores=weather_scores,
                           empty_scores=(not weather_scores))



@app.route('/tasks/query_weather')
def query_weather():
    """Run cron job: 
    1. Query weather forecast 
    2. Compute weather scores
    3. Update memcache and DB with new scores"""
    
    weather_scores = get_weather_scores()
    if weather_scores:
        # update memcache with new scores
        memcache.set(key='weather_scores', value=weather_scores)
        store_in_db(weather_scores)
    return 'OK'


@app.errorhandler(500)
def server_error(e):
    # Log the error and stacktrace.
    logging.exception('An error occurred during a request.')
    return 'An internal error occurred.', 500
# [END app]
