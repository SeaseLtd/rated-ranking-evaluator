import pytest
from typing import Any
from unittest.mock import MagicMock, mock_open, patch
from src.utils import QuepidWriter
from src.search_engine.data_store import DataStore
from src.schemas import Query, Score

@pytest.fixture
def mock_ds():
    """Returns a mocked DataStore instance."""
    return MagicMock(spec=DataStore)

@pytest.fixture
def writer(mock_ds):
    """Returns a QuepidWriter instance with a mocked DataStore."""
    return QuepidWriter(datastore=mock_ds)

def test_write_to_quepid_format(writer, mock_ds):
    # Arrange
    query1 = Query(id="q-1", text="query one", scores={
        "doc-1": Score(doc_id="doc-1", value=1),
        "doc-2": Score(doc_id="doc-2", value=0)
    })
    query2 = Query(id="q-2", text="query two", scores={
        "doc-3": Score(doc_id="doc-3", value=2)
    })
    mock_ds.get_queries.return_value = [query1, query2]

    m = mock_open()
    with patch("builtins.open", m):
        # Act
        writer.write("fake/path/output.csv")

    # Assert
    m.assert_called_once_with("fake/path/output.csv", 'w', newline='')
    handle = m()
    
    # Check header
    handle.write.assert_any_call('query,docid,rating\r\n')
    
    # Check rows
    handle.write.assert_any_call('query one,doc-1,1\r\n')
    handle.write.assert_any_call('query one,doc-2,0\r\n')
    handle.write.assert_any_call('query two,doc-3,2\r\n')

def test_write_skips_unscored_documents(writer, mock_ds):
    # Arrange
    query1 = Query(id="q-1", text="query one", scores={
        "doc-1": Score(doc_id="doc-1", value=1),
        "doc-2": Score(doc_id="doc-2", value=-1)  # Unscored
    })
    mock_ds.get_queries.return_value = [query1]

    m = mock_open()
    with patch("builtins.open", m):
        # Act
        writer.write("fake/path/output.csv")

    # Assert
    handle = m()
    handle.write.assert_any_call('query,docid,rating\r\n')
    handle.write.assert_any_call('query one,doc-1,1\r\n')
    
    # Ensure the unscored document was not written
    written_content = "".join(call.args[0] for call in handle.write.call_args_list)
    assert 'doc-2' not in written_content

def test_write_empty_datastore(writer, mock_ds):
    # Arrange
    mock_ds.get_queries.return_value = []

    m = mock_open()
    with patch("builtins.open", m):
        # Act
        writer.write("fake/path/output.csv")

    # Assert
    handle = m()
    handle.write.assert_called_once_with('query,docid,rating\r\n')
