from config import Settings


def test_cors_origins_single():
    settings = Settings(frontend_url="https://omnirag.vercel.app")
    assert settings.cors_origins == ["https://omnirag.vercel.app"]


def test_cors_origins_comma_separated_list():
    settings = Settings(frontend_url="https://omnirag.vercel.app, https://omnirag.com")
    assert settings.cors_origins == ["https://omnirag.vercel.app", "https://omnirag.com"]


def test_cors_origins_default_is_localhost():
    settings = Settings(frontend_url="http://localhost:3000")
    assert settings.cors_origins == ["http://localhost:3000"]


def test_cors_origins_ignores_blank_entries():
    settings = Settings(frontend_url="https://omnirag.vercel.app,, ")
    assert settings.cors_origins == ["https://omnirag.vercel.app"]
