import pytest

from src.migrate import parse_users


def test_parse_users_reads_a_json_object():
    assert parse_users('{"user0": "pass,0", "user1": "pass:1"}') == {
        "user0": "pass,0",
        "user1": "pass:1",
    }


@pytest.mark.parametrize("raw", [None, ""])
def test_parse_users_is_optional(raw):
    assert parse_users(raw) == {}


@pytest.mark.parametrize(
    "raw", ["not json s3cret", '["user0"]', '{"user0": ""}', '{"user0": 1}', '{"": "s3cret"}']
)
def test_parse_users_rejects_bad_values_without_quoting_them(raw):
    with pytest.raises(ValueError) as error:
        parse_users(raw)
    assert "s3cret" not in str(error.value)
