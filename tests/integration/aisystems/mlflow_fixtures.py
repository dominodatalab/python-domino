import pytest

def fixture_create_traces():
        pytest.importorskip("mlflow")
        import mlflow
        @mlflow.trace(name="test_add")
        def test_add(x, y):
                return x + y

        # create traces
        with mlflow.start_run():
                test_add(1, 2)
