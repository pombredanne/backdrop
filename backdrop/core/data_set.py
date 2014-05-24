from collections import namedtuple
from flask import logging
from .records import add_auto_ids, parse_timestamp, validate_record, \
    add_period_keys
from .validation import data_set_is_valid

import timeutils
import datetime

log = logging.getLogger(__name__)


class NewDataSet(object):
    def __init__(self, storage, config):
        self.storage = storage
        self.config = config

    @property
    def name(self):
        return self.config.name

    def is_recent_enough(self):
        if self.config.max_age_expected is None:
            return True

        max_age_expected = datetime.timedelta(
            seconds=self.config.max_age_expected)

        now = timeutils.now()
        last_updated = self.get_last_updated()

        if not last_updated:
            return False

        return (now - last_updated) < max_age_expected

    def get_last_updated(self):
        return self.storage.get_last_updated(self.config.name)

    def empty(self):
        return self.storage.empty(self.config.name)

    def store(self, records):
        log.info('received {} records'.format(len(records)))

        # add auto-id keys
        records = add_auto_ids(records, self.config.auto_ids)
        # parse _timestamp
        records = map(parse_timestamp, records)
        # validate
        records = map(validate_record, records)
        # add period data
        records = map(add_period_keys, records)

        [self.storage.save(self.config.name, record) for record in records]


class DataSet(object):

    def __init__(self, db, config):
        self.name = config.name
        self.repository = db.get_repository(config.name)
        self.auto_id_keys = config.auto_ids
        self.config = config
        self.db = db

    def query(self, query):
        result = query.execute(self.repository)

        return result


_DataSetConfig = namedtuple(
    "_DataSetConfig",
    "name data_group data_type raw_queries_allowed bearer_token upload_format "
    "upload_filters auto_ids queryable realtime capped_size max_age_expected")


class DataSetConfig(_DataSetConfig):

    def __new__(cls, name, data_group, data_type, raw_queries_allowed=False,
                bearer_token=None, upload_format="csv", upload_filters=None,
                auto_ids=None, queryable=True, realtime=False,
                capped_size=5040, max_age_expected=2678400):
        if not data_set_is_valid(name):
            raise ValueError("DataSet name is not valid: '{}'".format(name))

        if not upload_filters:
            upload_filters = [
                "backdrop.core.upload.filters.first_sheet_filter"]

        return super(DataSetConfig, cls).__new__(cls, name, data_group,
                                                 data_type,
                                                 raw_queries_allowed,
                                                 bearer_token, upload_format,
                                                 upload_filters, auto_ids,
                                                 queryable, realtime,
                                                 capped_size, max_age_expected)

    @property
    def max_age(self):
        """ Set cache-control header length based on type of data_set. """
        return 120 if self.realtime else 1800
