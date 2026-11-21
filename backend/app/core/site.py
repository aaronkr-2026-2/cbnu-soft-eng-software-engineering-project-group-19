SCHOLWARD_PUBLIC_URL = "https://scholward-academy.vercel.app"


SCHOLWARD_SITE_ORIGINS = frozenset(
    {
        SCHOLWARD_PUBLIC_URL,
        "https://studyflow-web-1hab.vercel.app",
    }
)


def frontend_url_for_origin(configured_url: str, origin: str | None) -> str:
    if (
        origin is not None
        and origin in SCHOLWARD_SITE_ORIGINS
        and configured_url.removesuffix("/app") in SCHOLWARD_SITE_ORIGINS
    ):
        return origin
    return configured_url
