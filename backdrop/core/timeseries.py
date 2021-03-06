from datetime import timedelta, time
from itertools import groupby
import time as _time
from dateutil.relativedelta import relativedelta, MO
import pytz
import itertools


class Period(object):

    @property
    def delta(self):
        return self._delta

    @property
    def start_at_key(self):
        return "_%s_start_at" % self.name

    def _is_boundary(self, timestamp):
        return self.valid_start_at(timestamp) \
            and self._is_start_of_day(timestamp)

    def _is_start_of_day(self, timestamp):
        return timestamp.time() == time(0, 0, 0, 0)

    def end(self, timestamp):
        if self._is_boundary(timestamp):
            return timestamp
        return self.start(timestamp + self._delta)

    def start(self, timestamp):
        raise NotImplementedError()

    def range(self, start, end):
        _start = self.start(start).replace(tzinfo=pytz.UTC)
        _end = self.end(end).replace(tzinfo=pytz.UTC)
        while _start < _end:
            yield (_start, _start + self._delta)
            _start += self._delta

    def valid_start_at(self, timestamp):
        raise NotImplementedError()


class Hour(Period):

    def __init__(self):
        self.name = "hour"
        self._delta = timedelta(hours=1)

    def _is_boundary(self, timestamp):
        return self.valid_start_at(timestamp)

    def start(self, timestamp):
        return timestamp.replace(minute=0, second=0, microsecond=0)

    def valid_start_at(self, timestamp):
        return timestamp.time() == time(timestamp.hour, 0, 0, 0)


class Day(Period):

    def __init__(self):
        self.name = "day"
        self._delta = timedelta(days=1)

    def start(self, timestamp):
        return _truncate_time(timestamp)

    def valid_start_at(self, timestamp):
        return self._is_start_of_day(timestamp)


class Week(Period):

    def __init__(self):
        self.name = "week"
        self._delta = timedelta(days=7)

    def start(self, timestamp):
        return _truncate_time(timestamp) + relativedelta(weekday=MO(-1))

    def valid_start_at(self, timestamp):
        return timestamp.weekday() == 0 and self._is_start_of_day(timestamp)


class Month(Period):

    def __init__(self):
        self.name = "month"
        self._delta = relativedelta(months=1)

    def start(self, timestamp):
        return timestamp.replace(day=1, hour=0, minute=0,
                                 second=0, microsecond=0)

    def valid_start_at(self, timestamp):
        return timestamp.day == 1 and self._is_start_of_day(timestamp)


class Quarter(Period):

    def __init__(self):
        self.name = "quarter"
        self._delta = relativedelta(months=3)
        self.quarter_starts = [10, 7, 4, 1]

    def start(self, timestamp):
        quarter_month = next(quarter for quarter in self.quarter_starts
                             if timestamp.month >= quarter)

        return timestamp.replace(month=quarter_month, day=1, hour=0, minute=0,
                                 second=0, microsecond=0)

    def valid_start_at(self, timestamp):
        return (timestamp.day == 1 and timestamp.month in self.quarter_starts
                and self._is_start_of_day(timestamp))


class Year(Period):

    def __init__(self):
        self.name = "year"
        self._delta = relativedelta(years=1)

    def start(self, timestamp):
        return timestamp.replace(month=1, day=1, hour=0, minute=0, second=0,
                                 microsecond=0)

    def valid_start_at(self, timestamp):
        return (timestamp.month == 1 and timestamp.day == 1
                and self._is_start_of_day(timestamp))


HOUR = Hour()
DAY = Day()
WEEK = Week()
MONTH = Month()
QUARTER = Quarter()
YEAR = Year()
PERIODS = [HOUR, DAY, WEEK, MONTH, QUARTER, YEAR]


def parse_period(period_name):
    for period in PERIODS:
        if period.name == period_name:
            return period


def _time_to_index(dt):
    return _time.mktime(dt.replace(tzinfo=pytz.utc).timetuple())


def timeseries(start, end, period, data, default):
    """
    Return a list of results from start to end, with missing
    data filled in with default.
    """
    data_by_start_at = _group_by_start_at(data)

    results = []
    for period_start, period_end in period.range(start, end):
        time_index = _time_to_index(period_start)
        if time_index in data_by_start_at:
            results += data_by_start_at[time_index]
        else:
            result = _merge(default, _period_limits(period_start, period_end))
            results.append(result)
    return results


def fill_group_by_permutations(start, end, period, data, default, group_by):

    # Generate all permutations of group_by keys
    def unique_values(key):
        return set([d[key] for d in data])

    def all_group_by_permutations():
        possible_keys = {
            group_key: unique_values(group_key) for group_key in group_by}
        step_1 = {k: [(k, v) for v in possible_keys[k]] for k in possible_keys}
        step_2 = list(itertools.product(*[step_1[x] for x in step_1]))
        return [dict(item) for item in step_2]

    permutations = all_group_by_permutations()

    def hash_datum(datum):
        return '{0}{1}{2}'.format(
            datum['_start_at'],
            datum['_end_at'],
            str([datum[key] for key in group_by]))

    def hash_permutation(perm, start, end):
        return '{0}{1}{2}'.format(
            start, end,
            str([perm[key] for key in group_by]))

    hashed_data = {hash_datum(datum): datum for datum in data}

    results = []
    # for each time period (e.g. 1 week) in the period requested (e.g. 3 weeks)
    for period_start, period_end in period.range(start, end):
        for group in permutations:
            group['_start_at'] = period_start
            group['_end_at'] = period_end

            datum = hashed_data.get(
                hash_permutation(group, period_start, period_end),
                None)

            if datum is not None:
                results.append(datum)
            else:
                results.append(_merge(default, group))

    return results


def _period_limits(start, end):
    return {
        "_start_at": start,
        "_end_at": end
    }


def _group_by_start_at(data):
    sorted_data = sorted(data, key=lambda d: d['_start_at'])
    grouped = groupby(sorted_data, lambda d: _time_to_index(d['_start_at']))
    return {k: list(g) for k, g in grouped}


def _period_range(start, stop, period):
    while start < stop:
        yield (start, start + period)
        start += period


def _merge(first, second):
    return dict(first.items() + second.items())


def _truncate_time(datetime):
    return datetime.replace(hour=0, minute=0, second=0, microsecond=0)
