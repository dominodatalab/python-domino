# flake8: noqa

_import_error_message = (
    "domino.training_sets is not installed.\n\n"
    "Please pip install dominodatalab-data:\n\n"
    "  python -m pip install dominodatalab-data   # install directly\n"
    '  python -m pip install "dominodatalab[data]" --upgrade   # install via extra dependency'
)

try:
    from domino_data.training_sets import client as TrainingSetClient, model
except ImportError as e:
    if e.msg == "No module named 'domino_data'":
        raise ImportError(_import_error_message) from e
    else:
        raise


def __getattr__(value):
    try:
        import domino_data.training_sets
    except ImportError as e:
        raise ImportError(_import_error_message) from e
    return getattr(domino_data, value)
