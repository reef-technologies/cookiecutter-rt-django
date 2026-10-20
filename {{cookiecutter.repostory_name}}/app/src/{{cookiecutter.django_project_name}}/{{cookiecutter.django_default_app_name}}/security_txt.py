from datetime import UTC, datetime, timedelta

from django.conf import settings
from django.http import Http404, HttpRequest, HttpResponse
from django.utils.timezone import now

SECURITY_TXT_EXPIRES_IN = timedelta(days=180)


def security_txt(request: HttpRequest) -> HttpResponse:
    if not settings.SECURITY_TXT_CONTACTS:
        raise Http404
    if settings.SECURITY_TXT_EXPIRES:
        expires = datetime.fromisoformat(settings.SECURITY_TXT_EXPIRES)
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=UTC)
    else:
        expires = now() + SECURITY_TXT_EXPIRES_IN
    lines = [f"Contact: {contact}" for contact in settings.SECURITY_TXT_CONTACTS]
    lines += [
        f"Expires: {expires.astimezone(UTC):%Y-%m-%dT%H:%M:%SZ}",
        f"Canonical: https://{request.get_host()}/.well-known/security.txt",
        "Preferred-Languages: en",
    ]
    return HttpResponse("\n".join(lines) + "\n", content_type="text/plain; charset=utf-8")
