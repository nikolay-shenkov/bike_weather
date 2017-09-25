import os
from os.path import join as pjoin

import numpy as np
import pandas as pd

from pandas.tseries.holiday import USFederalHolidayCalendar as us_calendar


DATA_DIR = '../data'
weather = pd.read_csv(pjoin(DATA_DIR, 'weather.csv'),
                      parse_dates=['Date'])
trip = pd.read_csv(pjoin(DATA_DIR, 'trip.csv'),
                   parse_dates=['starttime', 'stoptime'])


def weather_renamer(col):
    """Standardize column names in the weather data"""
    col = col.lower()
    d = {'min_temperaturef': 'min_temperature_f',
         'meandew_point_f': 'mean_dew_point_f'
        }
    return d[col] if col in d else col


def events_renamer(event):
    """Standadrize values in the events column in the weather data"""
    event = event.lower()
    event = event.replace(' , ', '_').replace('-', ('_'))
    return event


def trip_renamer(col):
    """Standardize column names in the trip data"""
    d = {'usertype': 'user_type',
         'tripduration': 'trip_duration',
         'bikeid': 'bike_id',
         'starttime': 'start_time',
         'stoptime': 'stop_time',
         'birthyear': 'birth_year',
        }
    return d[col] if col in d else col


weather.rename_axis(weather_renamer, axis=1, inplace=True)
weather['events'] = weather['events'].fillna('no_event')
weather['events'] = weather['events'].apply(events_renamer)
weather.to_csv(pjoin(DATA_DIR, 'weather.csv'), index=False)

trip.rename_axis(trip_renamer, axis=1, inplace=True)
trip.to_csv(pjoin(DATA_DIR, 'trip.csv'), index=False)

# process time variables
trip['weekday'] = trip.start_time.apply(lambda d: d.weekday())
trip['date'] = trip.start_time.apply(lambda d: d.date())
weather['date'] = weather.date.apply(lambda d: d.date())

# include only members for the initial calculation
trips_by_day = trip[trip.user_type == 'Member'].groupby(
    ['date', 'weekday'], as_index=False)['trip_id'].count()
trips_by_day.rename_axis({'trip_id': 'num_trips'}, axis=1, inplace=True)
trips_by_day['month'] = trips_by_day.date.apply(lambda d: d.month)

# check if a date is a holiday or a weekend
cal = us_calendar()
holidays = cal.holidays(start=trips_by_day.date.min(), end=trips_by_day.date.max())
trips_by_day['is_holiday'] = pd.to_datetime(trips_by_day.date).isin(holidays)
trips_by_day['is_weekend'] = trips_by_day.weekday > 4

with_weather = trips_by_day.merge(weather, left_on='date', right_on='date')
with_weather.to_csv(pjoin(DATA_DIR, 'with_weather.csv'), index=False)

