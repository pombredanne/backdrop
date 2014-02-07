import os
from behave import given, when, then
from dateutil import parser
from hamcrest import assert_that, has_length

FIXTURE_PATH = os.path.join(os.path.dirname(__file__), '..', 'fixtures')


@given('I have the data in "{fixture_name}"')
def step(context, fixture_name):
    path_to_fixture = os.path.join(FIXTURE_PATH, fixture_name)
    with open(path_to_fixture) as fixture:
        context.data_to_post = fixture.read()


@given('I use the bearer token for the bucket')
def step(context):
    context.bearer_token = "%s-bearer-token" % context.bucket


@when('I post the data to "{bucket_name}"')
def step(context, bucket_name):
    if not (context and 'bucket' in context):
        context.bucket = bucket_name.replace('/', '')
    context.response = context.client.post(
        bucket_name,
        data=context.data_to_post,
        content_type="application/json",
        headers=_make_headers_from_context(context),
    )


@when('I post to the specific path "{path}"')
def step(context, path):
    context.response = context.client.post(
        path,
        data=context.data_to_post,
        content_type="application/json",
        headers=_make_headers_from_context(context),
    )


@when('I post the file "{filename}" to "/{bucket_name}/upload"')
def step(context, filename, bucket_name):
    context.bucket = bucket_name.replace('/', '')
    context.response = context.client.post(
        "/" + bucket_name + "/upload",
        files={"file": open("tmp/%s" % filename, "r")},
        headers=_make_headers_from_context(context),
    )


@then('the stored data should contain "{amount}" "{key}" equaling "{value}"')
def step(context, amount, key, value):
    result = context.client.storage()[context.bucket].find({key: value})
    assert_that(list(result), has_length(int(amount)))


@then('the stored data should contain "{amount}" "{key}" on "{time}"')
def step(context, amount, key, time):
    time_query = parser.parse(time)
    result = context.client.storage()[context.bucket].find({key: time_query})
    assert_that(list(result), has_length(int(amount)))


def _make_headers_from_context(context):
    if context and 'bearer_token' in context:
        return [('Authorization', "Bearer %s" % context.bearer_token)]
    return []
