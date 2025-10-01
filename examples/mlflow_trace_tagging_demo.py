import argparse
import os
import time

import mlflow
from mlflow import MlflowClient


def ensure_experiment(name: str) -> str:
    """Create or get an experiment and tag it with ai_system=true.

    Returns the experiment ID and sets it as the active experiment.
    """
    client = MlflowClient()
    print("making experiment with name ", name)
    exp = client.get_experiment_by_name(name)
    print(exp)
    if exp is None:
        exp_id = client.create_experiment(name)
        print("CREATED", exp_id)
        client.set_experiment_tag(exp_id, "ai_system", "true")
    else:
        exp_id = exp.experiment_id
        # idempotent tag set to ensure the tag exists
        client.set_experiment_tag(exp_id, "ai_system", "true")

    # Ensure spans log to this experiment
    mlflow.set_experiment(experiment_id=exp_id)
    return exp_id


def log_traces(
    exp_id: str,
    app_id: str,
    app_version_id: str,
    trace_name: str,
    count: int,
    delay: float,
    eval_type: str,
) -> None:
    client = MlflowClient()

    def traced_fn(i):
        span = client.start_trace(name=trace_name)
        child_span = client.start_span(
                "child_span",
                trace_id=span.trace_id,
                parent_id=span.span_id,
                inputs={"x": i},
                )

        client.end_span(
                trace_id=child_span.trace_id,
                span_id=child_span.span_id,
                outputs=i,
                )
        client.end_trace(span.trace_id)
        return span

    for i in range(count):
        if delay > 0:
            time.sleep(delay)

        t = traced_fn(i)
        print(f"Logged trace {trace_name}")

        trace_id = t.trace_id
        print(trace_id)
        client.set_trace_tag(trace_id, "mlflow.domino.app_id", app_id)
        client.set_trace_tag(trace_id, "mlflow.domino.app_version_id", app_version_id)

        if eval_type == "metric":
            client.set_trace_tag(trace_id, "domino.prog.metric.accuracy", str(i))
        elif eval_type == "label":
            client.set_trace_tag(trace_id, "domino.prog.label.category", str(i))
            client.set_trace_tag(trace_id, "domino.prog.label.accuracy", str(i))

    print("tagged traces")


def main():
    parser = argparse.ArgumentParser(description="Emit MLflow traces and tag them for Domino")
    parser.add_argument("--app-id", required=True, help="Domino app ID")
    parser.add_argument(
        "--app-version-id", required=True, help="Domino app version ID"
    )
    parser.add_argument(
        "--trace-name", default="demo_span", help="Name of the span to create"
    )
    parser.add_argument("--eval-type", type=str, default="metric", help="The type of evaluation to log")
    parser.add_argument("--count", type=int, default=3, help="Number of traces to emit")
    parser.add_argument(
        "--delay",
        type=float,
        default=0.0,
        help="Seconds to sleep between traces",
    )
    args = parser.parse_args()

    print("MLFLOW_TRACKING_URI", os.getenv("MLFLOW_TRACKING_URI"))

    experiment = f"ai_system_experiment_{args.app_id}"
    exp_id = ensure_experiment(experiment)
    log_traces(
        exp_id,
        app_id=args.app_id,
        app_version_id=args.app_version_id,
        trace_name=args.trace_name,
        count=args.count,
        delay=args.delay,
        eval_type=args.eval_type,
    )


if __name__ == "__main__":
    main()
