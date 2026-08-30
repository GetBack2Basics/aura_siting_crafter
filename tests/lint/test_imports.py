import importlib, sys, pytest

def test_national_analysis_import():
    mod = importlib.import_module("src.Analysis.national_suitability_analysis")
    assert hasattr(mod, "evaluate_national_suitability") or hasattr(mod, "main")

def test_data_ingest_import():
    try:
        import geopandas
    except ImportError:
        pytest.skip("geopandas not installed in local environment")
    mod = importlib.import_module("src.Ingestion.data_ingest")
    assert hasattr(mod, "main") or hasattr(mod, "save_audit_report")


def test_dataset_loader_import():
    mod = importlib.import_module("src.Ingestion.dataset_loader")
    assert hasattr(mod, "list_available_datasets")
    assert hasattr(mod, "load_dataset_config")
    datasets = mod.list_available_datasets(state="nsw")
    assert len(datasets) >= 10

