import warnings

from urllib.parse import quote

from typing import Optional


class _Routes:
    def __init__(self, host, owner_username, project_name):
        self.host = host
        self._owner_username = owner_username
        self._project_name = project_name

    # URL builders
    def _build_project_url(self):
        return (
            self.host
            + "/v1/projects/"
            + self._owner_username
            + "/"
            + self._project_name
        )

    def _build_project_url_private_api(self):
        return self.host + "/u/" + self._owner_username + "/" + self._project_name

    def _build_old_project_url(self):
        # TODO refactor once these API endpoints are supported in REST API
        return self.host + "/" + self._owner_username + "/" + self._project_name

    def _build_models_url(self):
        return self.host + "/v1/models"

    def _build_models_v4_url(self):
        return self.host + "/v4/models"

    # Project URLs
    def project_create(self):
        return self.host + "/project"

    def project_v4(self, project_id: Optional[str] = None) -> str:
        return self.host + "/v4/projects" + (f"/{project_id}" if project_id else "")

    def projects_list(self):
        return f"{self.host}/v4/gateway/projects"

    def tag_details(self, tag_id):
        return f"{self.host}/projectTags/{tag_id}"

    def tags_add(self, project_id):
        return f"{self.host}/v4/projects/{project_id}/tags"

    def tags_remove(self, project_id, tag_id):
        return f"{self.host}/v4/projects/{project_id}/tags/{tag_id}"

    def runs_list(self):
        return self._build_project_url() + "/runs"

    def runs_start(self):
        return self._build_project_url() + "/runs"

    def runs_status(self, runId):
        return self._build_project_url() + "/runs/" + runId

    def runs_stdout(self, runId):
        return self._build_project_url() + "/run/" + runId + "/stdout"

    def files_list(self, commitId, path):
        return self._build_project_url() + "/files/" + commitId + "/" + path

    def files_upload(self, path):
        return self._build_project_url() + path

    def commits_list(self):
        return self._build_project_url() + "/commits"

    # Deprecated - use blobs_get_v2 instead
    def blobs_get(self, key):
        message = "blobs_get is deprecated and will soon be removed. Please migrate to blobs_get_v2 and adjust the " \
                  "input parameters accordingly "
        warnings.warn(message, DeprecationWarning)
        return self._build_project_url() + "/blobs/" + key

    def blobs_get_v2(self, path, commit_id, project_id):
        return self.host + f"/api/projects/v1/projects/{project_id}/files/{commit_id}/{path}/content"

    def fork_project(self, project_id):
        return self.host + f"/v4/projects/{project_id}/fork"

    def collaborators_get(self):
        return self._build_old_project_url() + "/collaborators"

    def collaborators_add(self, project_id):
        return self.host + f"/v4/projects/{project_id}/collaborators"

    def collaborators_remove(self, project_id, user_id):
        return self.host + f"/v4/projects/{project_id}/collaborators/{user_id}"

    # API Endpoint URLs
    def _build_endpoint_url(self):
        return (
            self.host
            + "/v1/"
            + self._owner_username
            + "/"
            + self._project_name
            + "/endpoint"
        )

    def endpoint(self):
        return self._build_endpoint_url()

    def endpoint_state(self):
        return self._build_endpoint_url() + "/state"

    def endpoint_publish(self):
        return self._build_endpoint_url() + "/publishRelease"

    # Model Manager URLs
    def models_list(self):
        return self._build_project_url() + "/models"

    def model_publish(self):
        return self._build_models_url()

    def model_versions_get(self, model_id):
        return self._build_models_url() + "/" + model_id + "/versions"

    def model_version_publish(self, model_id):
        return self._build_models_url() + "/" + model_id + "/versions"

    def model_version_export(self, model_id, model_version_id):
        return (
            self._build_models_v4_url()
            + "/"
            + model_id
            + "/"
            + model_version_id
            + "/exportImageToRegistry"
        )

    def model_version_sagemaker_export(self, model_id, model_version_id):
        return (
            self._build_models_v4_url()
            + "/"
            + model_id
            + "/"
            + model_version_id
            + "/exportImageForSagemaker"
        )

    def model_version_export_status(self, model_export_id):
        return (
            self._build_models_v4_url()
            + "/"
            + model_export_id
            + "/getExportImageStatus"
        )

    def model_version_export_logs(self, model_export_id):
        return self._build_models_v4_url() + "/" + model_export_id + "/getExportLogs"

    # Environment URLs
    def environments_list(self):
        return self.host + "/v1/environments"

    # Deployment URLs
    def deployment_version(self):
        return self.host + "/version"

    # Job URLs
    def job_start(self):
        return f"{self.host}/v4/jobs/start"

    def job_stop(self):
        return f"{self.host}/v4/jobs/stop"

    def job_status(self, job_id):
        return f"{self.host}/v4/jobs/{job_id}"

    def job_runtime_execution_details(self, job_id):
        return f"{self.host}/v4/jobs/{job_id}/runtimeExecutionDetails"

    def default_spark_setting(self, project_id):
        return f"{self.host}/v4/jobs/project/{project_id}/defaultSparkSettings"

    def useable_environments_list(self, project_id):
        return f"{self.host}/v4/projects/{project_id}/useableEnvironments"

    # App URLs
    def app_publish(self):
        return self._build_project_url_private_api() + "/nb/startSession"

    # Datasets URLs
    def datasets_list(self, project_id):
        if project_id is None:
            return self.host + "/dataset"
        else:
            return self.host + "/dataset?projectId=" + str(project_id)

    def datasets_create(self):
        return self.host + "/dataset"

    def datasets_details(self, dataset_id):
        return self.host + "/dataset" + "/" + str(dataset_id)

    def datasets_start_upload(self, dataset_id):
        return self.host + f"/v4/datasetrw/datasets/{str(dataset_id)}/snapshot/file/start"

    def datasets_test_chunk(
        self,
        dataset_id,
        upload_key,
        chunk_number,
        total_chunks,
        identifier,
        checksum
    ):
        return (
            self.host +
            f"/v4/datasetrw/datasets/{str(dataset_id)}/snapshot/file/test?key={upload_key}"
            f"&resumableChunkNumber={chunk_number}&resumableIdentifier={quote(identifier)}"
            f"&resumableTotalChunks={total_chunks}&checksum={quote(checksum)}"
        )

    def datasets_upload_chunk(
        self,
        dataset_id,
        key,
        chunk_number,
        total_chunks,
        target_chunk_size,
        current_chunk_size,
        identifier,
        resumable_relative_path,
        checksum
    ):
        return (
            self.host +
            f"/v4/datasetrw/datasets/{dataset_id}/snapshot/file?key={key}&resumableChunkNumber={chunk_number}" +
            f"&resumableChunkSize={target_chunk_size}&resumableCurrentChunkSize={current_chunk_size}"
            f"&resumableIdentifier={quote(identifier)}&resumableRelativePath={quote(resumable_relative_path)}"
            f"&resumableTotalChunks={total_chunks}&checksum={quote(checksum)}"
        )

    def datasets_cancel_upload(self, dataset_id, upload_key):
        return self.host + f"/v4/datasetrw/datasets/{dataset_id}/snapshot/file/cancel/{upload_key}"

    def datasets_end_upload(self, dataset_id, upload_key, target_relative_path=None):
        url = self.host + f"/v4/datasetrw/datasets/{dataset_id}/snapshot/file/end/{upload_key}"
        if target_relative_path:
            url += f"?targetRelativePath={target_relative_path}"
        return url

    def app_list(self, project_id):
        return self.host + f"/v4/modelProducts?projectId={project_id}"

    def app_create(self):
        return self.host + "/v4/modelProducts"

    def app_start(self, app_id):
        return self.host + f"/v4/modelProducts/{app_id}/start"

    def app_stop(self, app_id):
        return self.host + f"/v4/modelProducts/{app_id}/stop"

    def app_get(self, app_id):
        return f"{self.host}/v4/modelProducts/{app_id}"

    # Hardware Tier URLs
    def hardware_tiers_list(self, project_id):
        return self.host + f"/v4/projects/{project_id}/hardwareTiers"

    # Custom Metrics URLs
    def metric_alerts(self):
        return self.host + "/api/metricAlerts/v1"

    def log_metrics(self):
        return self.host + f"/api/metricValues/v1"

    def read_metrics(self, model_monitoring_id, metric):
        return self.host + f"/api/metricValues/v1/{model_monitoring_id}/{metric}"

    # Find Project By OwnerName and project name Url
    def find_project_by_owner_name_and_project_name_url(self):
        return (
            f"{self.host}/v4/gateway/projects/findProjectByOwnerAndName"
            f"?ownerName={self._owner_username}&projectName={self._project_name}"
        )

    # User URLs
    def users_get(self) -> str:
        return self.host + "/v4/users"

    # Budgets and Billing Tags
    def budget_settings(self) -> str:
        return self.host + "/v4/cost/budgets/global/alertsSettings"

    def budgets_default(self, budget_label: Optional[str] = None) -> str:
        label = f"/{budget_label}" if budget_label else ""
        return self.host + f"/v4/cost/budgets/defaults{label}"

    def budget_overrides(self, override_id: Optional[str] = None) -> str:
        override = f"/{override_id}" if override_id else ""
        return self.host + f"/v4/cost/budgets/overrides{override}"

    def billing_tags_settings(self, mode_only: Optional[bool] = False) -> str:
        mode_str = "/mode" if mode_only else ""
        return self.host + "/v4/cost/billingtagSettings" + mode_str

    def billing_tags(self, name: Optional[str] = None) -> str:
        optional_name = f"/{name}" if name else ""
        return self.host + "/v4/cost/billingtags" + optional_name

    def project_billing_tag(self, project_id: Optional[str] = None) -> str:
        return self.host + f"/v4/projects/{project_id}/billingtag"

    def projects_billing_tags(self):
        return self.host + "/v4/projects/billingtags/projects"
