from config import get_settings

def test_settings_load():
    settings = get_settings()
    assert settings.PROJECT_NAME == "EDGAR AlphaOps"
    assert "EDGAR-AlphaOps" in settings.SEC_USER_AGENT
