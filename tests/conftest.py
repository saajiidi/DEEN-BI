import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_streamlit(mocker):
    return mocker.patch("streamlit.session_state", new_callable=MagicMock)


@pytest.fixture
def mock_some_dependency():
    return MagicMock()
