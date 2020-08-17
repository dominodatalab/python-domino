class _Routes:
    def __init__(self, host, owner_username, project_name):
        self.host = host
        self._owner_username = owner_username
        self._project_name = project_name

    # URL builders
    def _build_project_url(self):
        return self.host + '/v1/projects/' + \
            self._owner_username + '/' + self._project_name

    def _build_project_url_private_api(self):
        return self.host + '/u/' + self._owner_username + \
            '/' + self._project_name

    def _build_old_project_url(self):
        # TODO refactor once these API endpoints are supported in REST API
        return self.host + '/' \
            + self._owner_username + '/' + self._project_name

    def _build_models_url(self):
        return self.host + '/v1/models'

    # Project URLs
    def project_create(self):
        return self.host + '/project'

    def runs_list(self):
        return self._build_project_url() + '/runs'

    def runs_start(self):
        return self._build_project_url() + '/runs'

    def run_stop(self, runId):
        return self._build_project_url_private_api() + '/run/stop/' + runId

    def runs_status(self, runId):
        return self._build_project_url() + '/runs/' + runId

    def runs_stdout(self, runId):
        return self._build_project_url() + '/run/' + runId + '/stdout'

    def files_list(self, commitId, path):
        return self._build_project_url() + '/files/' + commitId + '/' + path

    def files_upload(self, path):
        return self._build_project_url() + path

    def commits_list(self):
        return self._build_project_url() + '/commits'

    def blobs_get(self, key):
        return self._build_project_url() + '/blobs/' + key

    def fork_project(self, project_id):
        return self.host + f'/v4/projects/{project_id}/fork'

    def collaborators_get(self):
        return self._build_old_project_url() + '/collaborators'

    def collaborators_add(self):
        return self._build_project_url_private_api() + '/addCollaborator'

    def collaborators_remove(self):
        return self._build_old_project_url() + '/removeCollaborator'

    # API Endpoint URLs 
    def _build_endpoint_url(self):
        return self.host + '/v1/' + \
            self._owner_username + '/' + self._project_name + '/endpoint'

    def endpoint(self):
        return self._build_endpoint_url()

    def endpoint_state(self):
        return self._build_endpoint_url() + '/state'

    def endpoint_publish(self):
        return self._build_endpoint_url() + '/publishRelease'

    # Model Manager URLs
    def models_list(self):
        return self._build_project_url() + '/models'

    def model_publish(self):
        return self._build_models_url()

    def model_versions_get(self, model_id):
        return self._build_models_url() + '/' + model_id + '/versions'

    def model_version_publish(self, model_id):
        return self._build_models_url() + '/' + model_id + '/versions'

    # Environment URLs
    def environments_list(self):
        return self.host + '/v1/environments'

    # Deployment URLs
    def deployment_version(self):
        return self.host + '/version'

    # App URLs
    def app_list(self, project_id):
        return self.host + f'/v4/modelProducts?projectId={project_id}'

    def app_create(self):
        return self.host + '/v4/modelProducts'

    def app_start(self, app_id):
        return self.host + f'/v4/modelProducts/{app_id}/start'

    def app_stop(self, app_id):
        return self.host + f'/v4/modelProducts/{app_id}/stop'
    
    # Hardware Tier URLs
    def hardware_tiers_list(self, project_id):
        return self.host + f'/v4/projects/{project_id}/hardwareTiers'

    # Find Project By OwnerName and project name Url
    def find_project_by_owner_name_and_project_name_url(self):
        return f'{self.host}/v4/gateway/projects/findProjectByOwnerAndName' \
               f'?ownerName={self._owner_username}&projectName={self._project_name}'
