# flake8: noqa

_import_error_message = (
    "domino.data_sources is not installed.\n\n"
    "Please pip install dominodatalab-data:\n\n"
    '  python -m pip install "dominodatalab[data]" --upgrade'
)

try:
    from domino_data.datasource import *
except ImportError as e:
    if e.msg == "No module named 'domino_data'":
        raise ImportError(_import_error_message) from e
    else:
        raise


def __getattr__(value):
    try:
        import domino_data.datasource
    except ImportError as e:
        raise ImportError(_import_error_message) from e
    return getattr(domino_data, value)
