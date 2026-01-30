import pytest
from unittest.mock import MagicMock, patch
from python_service.services.dataset_service import DatasetService

@pytest.fixture
def dataset_service():
    return DatasetService()

def test_list_datasets(dataset_service):
    datasets = dataset_service.list_datasets()
    assert isinstance(datasets, list)
    assert len(datasets) > 0
    # Check if docred is in the list
    docred = next((d for d in datasets if d["dataset_id"] == "docred"), None)
    assert docred is not None

def test_get_spec(dataset_service):
    spec = dataset_service.get_spec("docred")
    assert spec.dataset_id == "docred"
    assert spec.source == "local"
    
    with pytest.raises(KeyError):
        dataset_service.get_spec("non_existent_dataset")

def test_normalize_sample_docred(dataset_service):
    raw_sample = {
        "title": "Test Title",
        "sents": [["This", "is", "sentence", "one", "."], ["Sentence", "two", "."]],
        "vertexSet": [],
        "labels": []
    }
    norm = dataset_service.normalize_sample("docred", "train", 0, raw_sample)
    assert norm["query"] == "Test Title"
    assert "This is sentence one . Sentence two ." in norm["context"]
    assert norm["dataset_id"] == "docred"

@patch("python_service.services.dataset_service.DatasetService._load_hf_split")
def test_get_total_hf(mock_load, dataset_service):
    # Mock HF dataset
    mock_ds = MagicMock()
    mock_ds.__len__.return_value = 100
    mock_load.return_value = mock_ds
    
    total = dataset_service.get_total("fever", "train")
    assert total == 100

def test_list_splits_docred(dataset_service):
    splits = dataset_service.list_splits("docred")
    assert "train_annotated" in splits
    assert "dev" in splits
