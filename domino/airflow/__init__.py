try:
    from domino.airflow._operator import DominoOperator, DominoSparkOperator
except SyntaxError:
    raise ImportError(
        "Use of the Airflow DominoOperator requires typing (Python 3.5+)."
    )
