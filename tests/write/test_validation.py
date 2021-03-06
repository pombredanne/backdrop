from hamcrest import assert_that, is_
from backdrop.write.validation import (auth_header_is_valid,
                                       extract_bearer_token)


class TestBearerTokenIsValid(object):
    def test_auth_header_is_valid(self):
        auth_header = "Bearer token"
        data_set_config = {'bearer_token': 'token'}

        assert_that(auth_header_is_valid(data_set_config, auth_header))

    def test_extract_bearer_token_returns_blank_string_if_invalid(self):
        received_token = "token"

        assert_that(extract_bearer_token(received_token),
                    is_(None))

    def test_extract_bearer_token_returns_blank_string_if_wrong_prefix(self):
        token = "token"
        received_token = "Nearer {}".format(token)

        assert_that(extract_bearer_token(received_token),
                    is_(None))

    def test_extract_bearer_token_returns_the_token_if_valid(self):
        token = "token"
        received_token = "Bearer {}".format(token)

        assert_that(extract_bearer_token(received_token),
                    is_(token))
