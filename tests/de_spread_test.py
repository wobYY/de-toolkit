"""Unit tests for de_gspread."""

import pytest

from de_toolkit.gsheets.de_gspread import DtkGspread
from dotenv import load_dotenv
import os
import gspread

# Load environment variables
load_dotenv()


def test_service_acc_invalid_credentials() -> None:
    """Test that the DtkGspread class raises an error when given invalid credentials."""
    with pytest.raises(ValueError, match="Invalid credential!"):
        DtkGspread(credentials="")


def test_oauth_no_credentials() -> None:
    """Test that the DtkGspread class raises an error when given no credentials for OAuth."""
    with pytest.raises(TypeError):
        DtkGspread(credentials="", credentials_type="oauth")


def test_invalid_spreadsheet_id() -> None:
    """Test that the DtkGspread class raises an error when given an invalid spreadsheet ID."""
    with pytest.raises(
        gspread.SpreadsheetNotFound, match="No spreadsheet ID, name, or URL provided."
    ):
        DtkGspread(credentials=os.environ["GSPREAD_CREDENTAILS"], spreadsheet_id="")


def test_invalid_spreadsheet_name() -> None:
    """Test that the DtkGspread class raises an error when given an invalid spreadsheet name."""
    with pytest.raises(
        gspread.NoValidUrlKeyFound, match="No spreadsheet ID, name, or URL provided."
    ):
        DtkGspread(credentials=os.environ["GSPREAD_CREDENTAILS"], spreadsheet_name="")


def test_invalid_spreadsheet_url() -> None:
    """Test that the DtkGspread class raises an error when given an invalid spreadsheet URL."""
    with pytest.raises(
        gspread.NoValidUrlKeyFound, match="No spreadsheet ID, name, or URL provided."
    ):
        DtkGspread(credentials=os.environ["GSPREAD_CREDENTAILS"], spreadsheet_url="")
