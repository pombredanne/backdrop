from datetime import datetime
import unittest


from hamcrest import *
import pytz
from werkzeug.datastructures import MultiDict
from freezegun import freeze_time

from backdrop.read.query import parse_request_args


class Test_parse_request_args(unittest.TestCase):
    def test_start_at_is_parsed(self):
        request_args = MultiDict([
            ("start_at", "2012-12-12T08:12:43+00:00")])

        args = parse_request_args(request_args)

        assert_that(args['start_at'], is_(
            datetime(2012, 12, 12, 8, 12, 43, tzinfo=pytz.UTC)))

    def test_first_start_at_is_used(self):
        request_args = MultiDict([
            ("start_at", "2012-12-12T08:12:43+00:00"),
            ("start_at", "2012-12-13T08:12:43+00:00"),
        ])

        args = parse_request_args(request_args)

        assert_that(args['start_at'], is_(
            datetime(2012, 12, 12, 8, 12, 43, tzinfo=pytz.UTC)))

    def test_end_at_is_parsed(self):
        request_args = MultiDict([
            ("end_at", "2012-12-12T08:12:43+00:00")])

        args = parse_request_args(request_args)

        assert_that(args['end_at'], is_(
            datetime(2012, 12, 12, 8, 12, 43, tzinfo=pytz.UTC)))

    def test_first_end_at_is_used(self):
        request_args = MultiDict([
            ("end_at", "2012-12-12T08:12:43+00:00"),
            ("end_at", "2012-12-13T08:12:43+00:00"),
        ])

        args = parse_request_args(request_args)

        assert_that(args['end_at'], is_(
            datetime(2012, 12, 12, 8, 12, 43, tzinfo=pytz.UTC)))

    def test_one_filter_by_is_parsed(self):
        request_args = MultiDict([
            ("filter_by", "foo:bar")])

        args = parse_request_args(request_args)

        assert_that(args['filter_by'], has_item(["foo", "bar"]))

    def test_many_filter_by_are_parsed(self):
        request_args = MultiDict([
            ("filter_by", "foo:bar"),
            ("filter_by", "bar:foo")
        ])

        args = parse_request_args(request_args)

        assert_that(args['filter_by'], has_item(["foo", "bar"]))
        assert_that(args['filter_by'], has_item(["bar", "foo"]))

    def test_build_query_with_boolean_value(self):
        request_args = MultiDict([
            ("filter_by", "planet:true"),
            ("filter_by", "star:false"),
        ])

        args = parse_request_args(request_args)

        assert_that(args['filter_by'], has_item([ "planet", True ]))
        assert_that(args['filter_by'], has_item([ "star", False ]))

    def test_group_by_is_passed_through_untouched(self):
        request_args = MultiDict([("group_by", "foobar")])

        args = parse_request_args(request_args)

        assert_that(args['group_by'], is_('foobar'))

    def test_sort_is_parsed(self):
        request_args = MultiDict([
            ("sort_by", "foo:ascending")])

        args = parse_request_args(request_args)

        assert_that(args['sort_by'], is_(["foo", "ascending"]))

    def test_sort_will_use_first_argument_only(self):
        request_args = MultiDict([
            ("sort_by", "foo:descending"),
            ("sort_by", "foo:ascending"),
        ])

        args = parse_request_args(request_args)

        assert_that(args['sort_by'], is_(["foo", "descending"]))

    def test_limit_is_parsed(self):
        request_args = MultiDict([
            ("limit", "123")
        ])

        args = parse_request_args(request_args)

        assert_that(args['limit'], is_(123))

    def test_one_collect_is_parsed_with_default_method(self):
        request_args = MultiDict([
            ("collect", "some_key")
        ])

        args = parse_request_args(request_args)

        assert_that(args['collect'], is_([("some_key", "default")]))

    def test_two_collects_are_parsed_with_default_methods(self):
        request_args = MultiDict([
            ("collect", "some_key"),
            ("collect", "some_other_key")
        ])

        args = parse_request_args(request_args)

        assert_that(args['collect'], is_([("some_key", "default"),
                                          ("some_other_key", "default")]))

    def test_one_collect_is_parsed_with_custom_method(self):
        request_args = MultiDict([
            ("collect", "some_key:mean")
        ])

        args = parse_request_args(request_args)

        assert_that(args['collect'], is_([("some_key", "mean")]))

    @freeze_time('2014-01-09 00:00:00')
    def test_now_and_positive_delta_sets_start_end_window(self):
        request_args = MultiDict([
            ('period', 'day'),
            ('delta', '3'),
        ])

        args = parse_request_args(request_args)

        assert_that(args['start_at'], is_(
            datetime(2014, 1, 9, 0, 0, 0, tzinfo=pytz.UTC)))

        assert_that(args['end_at'], is_(
            datetime(2014, 1, 12, 0, 0, 0, tzinfo=pytz.UTC)))

    @freeze_time('2014-01-09 00:00:00')
    def test_now_and_negative_delta_sets_start_end_window(self):
        request_args = MultiDict([
            ('period', 'day'),
            ('delta', '-3'),
        ])

        args = parse_request_args(request_args)

        assert_that(args['start_at'], is_(
            datetime(2014, 1, 6, 0, 0, 0, tzinfo=pytz.UTC)))

        assert_that(args['end_at'], is_(
            datetime(2014, 1, 9, 0, 0, 0, tzinfo=pytz.UTC)))

    def test_date_on_boundary_and_positive_delta_sets_start_end_window(self):
        request_args = MultiDict([
            ('date', '2014-01-09T00:00:00+00:00'),
            ('period', 'day'),
            ('delta', '3'),
        ])

        args = parse_request_args(request_args)

        assert_that(args['start_at'], is_(
            datetime(2014, 1, 9, 0, 0, 0, tzinfo=pytz.UTC)))

        assert_that(args['end_at'], is_(
            datetime(2014, 1, 12, 0, 0, 0, tzinfo=pytz.UTC)))

    def test_date_on_boundary_and_negative_delta_sets_start_end_window(self):
        request_args = MultiDict([
            ('date', '2014-01-11T0:0:0+00:00'),
            ('period', 'day'),
            ('delta', '-3'),
        ])

        args = parse_request_args(request_args)

        assert_that(args['start_at'], is_(
            datetime(2014, 1, 8, 0, 0, 0, tzinfo=pytz.UTC)))

        assert_that(args['end_at'], is_(
            datetime(2014, 1, 11, 0, 0, 0, tzinfo=pytz.UTC)))

    def test_date_off_boundary_and_positive_delta_sets_start_end_window(self):
        request_args = MultiDict([
            ('date', '2014-01-09T01:02:03+00:00'),
            ('period', 'day'),
            ('delta', '3'),
        ])

        args = parse_request_args(request_args)

        assert_that(args['start_at'], is_(
            datetime(2014, 1, 10, 0, 0, 0, tzinfo=pytz.UTC)))

        assert_that(args['end_at'], is_(
            datetime(2014, 1, 13, 0, 0, 0, tzinfo=pytz.UTC)))

    def test_date_off_boundary_and_negative_delta_sets_start_end_window(self):
        request_args = MultiDict([
            ('date', '2014-01-11T23:58:57+00:00'),
            ('period', 'day'),
            ('delta', '-3'),
        ])

        args = parse_request_args(request_args)

        assert_that(args['start_at'], is_(
            datetime(2014, 1, 8, 0, 0, 0, tzinfo=pytz.UTC)))

        assert_that(args['end_at'], is_(
            datetime(2014, 1, 11, 0, 0, 0, tzinfo=pytz.UTC)))
