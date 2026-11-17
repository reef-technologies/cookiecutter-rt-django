import pytest
from django.core.exceptions import ImproperlyConfigured
from freezegun import freeze_time

from ...settings import _parse_security_txt_expires


def test__security_txt__disabled_without_contacts(client, settings):
    settings.SECURITY_TXT_CONTACTS = []

    response = client.get("/.well-known/security.txt")

    assert response.status_code == 404


@freeze_time("2026-01-01T12:00:00Z")
def test__security_txt(client, settings):
    settings.SECURITY_TXT_CONTACTS = ["mailto:security@example.com", "https://example.com/security"]
    settings.SECURITY_TXT_EXPIRES = _parse_security_txt_expires("")

    response = client.get("/.well-known/security.txt", HTTP_HOST="example.com")

    assert response.status_code == 200
    assert response["Content-Type"] == "text/plain; charset=utf-8"
    assert response.content.decode() == (
        "Contact: mailto:security@example.com\n"
        "Contact: https://example.com/security\n"
        "Expires: 2026-06-30T12:00:00Z\n"
        "Canonical: https://example.com/.well-known/security.txt\n"
        "Preferred-Languages: en\n"
    )


@pytest.mark.parametrize("expires", ["2027-10-01", "2027-10-01T00:00:00Z", "2027-10-01T02:00:00+02:00"])
def test__security_txt__fixed_expires(client, settings, expires):
    settings.SECURITY_TXT_CONTACTS = ["mailto:security@example.com"]
    settings.SECURITY_TXT_EXPIRES = _parse_security_txt_expires(expires)

    response = client.get("/.well-known/security.txt", HTTP_HOST="example.com")

    assert response.status_code == 200
    assert response.content.decode() == (
        "Contact: mailto:security@example.com\n"
        "Expires: 2027-10-01T00:00:00Z\n"
        "Canonical: https://example.com/.well-known/security.txt\n"
        "Preferred-Languages: en\n"
    )


def test__security_txt__invalid_expires_fails_at_startup():
    with pytest.raises(ImproperlyConfigured) as exc_info:
        _parse_security_txt_expires("01.10.2027")

    assert str(exc_info.value) == "SECURITY_TXT_EXPIRES must be an ISO 8601 date, e.g. 2027-10-01, got '01.10.2027'"
