from google.appengine.ext import ndb


class DailyResult(ndb.Model):
    item_order = ndb.IntegerProperty()
    score = ndb.IntegerProperty()
    date = ndb.StringProperty()
    weekday = ndb.StringProperty()

    @classmethod
    def query_daily(cls, ancestor_key):
        return cls.query(ancestor=ancestor_key).order(cls.item_order)


def query_db():
    weather_scores = []
    parent = ndb.Key('DailyParent', 'weather_scores')
    for res in DailyResult.query_daily(parent).fetch(4):
        weather_scores.append({
            'score': res.score,
            'weekday': res.weekday,
            'date': res.date
        })
    return weather_scores


def store_in_db(weather_scores):
    """Overwrites previously stored daily scores."""
    if weather_scores:
        # delete old scores
        parent = ndb.Key('DailyParent', 'weather_scores')
        keys_to_del = [d.key for d in DailyResult.query_daily(parent).fetch(4)]
        ndb.delete_multi(keys_to_del)
        
        # store new scores in DB
        for (i, daily) in enumerate(weather_scores):
            res = DailyResult(parent=parent,
                              item_order=i,
                              date=daily['date'],
                              score=daily['score'],
                              weekday=daily['weekday']
                             )
            res.put()

