"""Unit tests for de_gspread."""

import pytest

from de_toolkit.gsheets.de_gspread import DtkGspread


def test_service_acc_invalid_credentials() -> None:
    """Test that the DtkGspread class raises an error when given invalid credentials."""
    with pytest.raises(ValueError, match="Invalid credential!"):
        DtkGspread(credentials="")


def test_oauth_no_credentials() -> None:
    """Test that the DtkGspread class raises an error when given no credentials for OAuth."""
    with pytest.raises(TypeError):
        DtkGspread(credentials="", credentials_type="oauth")
