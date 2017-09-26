import time

import requests
from requests.exceptions import ConnectionError, Timeout

# api parameters
COUNTRY = 'canada'
CITY = 'vancouver'

with open('../secret.txt', 'r') as f:
    API_KEY = f.read().strip()

TEMPLATE = 'http://api.wunderground.com/api/{}/forecast/q/{}/{}.json'
REQUEST_URL = TEMPLATE.format(API_KEY, COUNTRY, CITY)


def get_days_with_scores():
    """Sends a request to the Weather Underground API for a four day 
    forecast and produces a bike-weather score for each day.

    Returns:
        result: dict of the form {day_stamp: score} for each of the four
                days in the forecast. Example output:
                {'Mon, Sep 25, 2017': 32, 'Thu, Sep 28, 2017': 72, 
                 'Tue, Sep 26, 2017': 45, 'Wed, Sep 27, 2017': 55}
    """

    four_day = send_request()
    if four_day is not None:
        result = {}
        for daily in four_day:
            time_label = extract_time_label(daily)
            features = compute_features(daily)
            raw_score = compute_raw_score(features)
            result[time_label] = compute_final_score(raw_score)
        return result


def send_request(failed=False):
    """Extract the four day forecast (including today's) for the 
    city of Vancouver, BC, Canada. For details of the API used, see:
    see: https://www.wunderground.com/weather/api/d/docs?d=data/forecast#simpleforecast__forecastday
    
    This method makes two attempts to send the request where the 
    second attempt is sent after a 10-sec pause. 

    Returns:
        four_day: a list with four elements, where each element
                  includes the weather forecast. For more details, see
    """

    if failed:
        time.sleep(10)

    try:
        r = requests.get(REQUEST_URL)
    except (ConnectionError, Timeout):  # This is the correct syntax
        return None if failed else send_request(failed=True) 
    contents = r.json()
    
    try:
        four_day = contents['forecast']['simpleforecast']['forecastday']
    except (KeyError, TypeError):
        return None if failed else send_request(failed=True)
    
    return four_day


def extract_time_label(daily):
    """The formatted time label is in the form: 
    'Mon, Nov 3, 2017' (it is not fixed width)
    """
    time_fields = ['weekday_short', 'monthname_short', 'day', 'year']
    values = [daily['date'][field] for field in time_fields]
    return '{}, {} {}, {}'.format(*values)


def compute_features(daily):
    """Extract weather features from the daily forecast.
    Compute additional features such as temp_wind (an interaction term)."""

    features = {
        'min_temp': float(daily['low']['fahrenheit']),
        'max_temp': float(daily['high']['fahrenheit']),
        'max_wind': daily['maxwind']['mph'],
        'mean_wind': daily['avewind']['mph'],
        'mean_humidity': daily['avehumidity'],
    }

    mean_temp = (features['min_temp'] + features['max_temp'])/2.0
    features['temp_squared'] = mean_temp**2
    features['temp_humidity'] = features['min_temp']*features['mean_humidity']
    features['temp_wind'] = features['min_temp']*features['max_wind']
    return features


def compute_raw_score(features):
    """Use the extracted features to compute a raw score that estimates 
    how suitable the weather for the corresponding day is for biking.
    Following the pipeline used in fitting the Lasso model, the features are:
    1. Transformed to zero median, and an interquartile range of 1.
    2. Multiplied by the Lasso coefficients and added up (dot product) to 
    estimate the raw score.
    
    The raw score is roughly between -100 and +100. 
    """

    feat_order = ['min_temp', 'max_temp', 'mean_humidity', 'max_wind', 
                  'mean_wind', 'temp_squared', 'temp_humidity', 'temp_wind'
                 ]
    # median and interquartile range for each features 
    scale = [13.25, 18., 19., 5., 3., 1824., 862.5, 272.25]
    center = [50., 63., 70., 10., 4., 3192.25, 3410., 524.]

    # lasso coefficients
    lasso_coefs = [172.222, 124.748, 18.416, 14.291, -3.437, 
                   -202.417, -59.271, -28.963]

    weights = {}
    for i, feat in enumerate(feat_order):
        rescaled = (features[feat] - center[i])/scale[i]
        # store weights to perform dot product
        weights[feat] = lasso_coefs[i]*rescaled

    return sum(weights.values())


def compute_final_score(raw_score):
    """Rescales the raw score to be between 0 and 100."""
    lower_bound, upper_bound = -95, 95
    score = (raw_score - lower_bound)/(upper_bound - lower_bound)
    score = max(0.0, score)
    score = min(1.0, score)
    return int(round(score, 2)*100)

