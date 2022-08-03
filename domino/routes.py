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

    def project_archive(self, project_id):
        return f"{self.host}/v4/projects/{project_id}"

    def projects_list(self):
        return f"{self.host}/v4/gateway/projects"

    # tags URLs
    def tags_list(self, project_id):
        return f"{self.host}/v4/projects/{project_id}"

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

    def blobs_get(self, key):
        return self._build_project_url() + "/blobs/" + key

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

    # Find Project By OwnerName and project name Url
    def find_project_by_owner_name_and_project_name_url(self):
        return (
            f"{self.host}/v4/gateway/projects/findProjectByOwnerAndName"
            f"?ownerName={self._owner_username}&projectName={self._project_name}"
        )

    # User URLs
    def users_get(self):
        return self.host + "/v4/users"
