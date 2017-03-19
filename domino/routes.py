class _Routes:
    def __init__(self, host, owner_username, project_name):
        self.host = host
        self._owner_username = owner_username
        self._project_name = project_name

    # Project URLs
    def _build_project_url(self):
        return self.host + '/v1/projects/' + \
            self._owner_username + '/' + self._project_name

    def runs_list(self):
        return self._build_project_url() + '/runs'

    def runs_start(self):
        return self._build_project_url() + '/runs'

    def files_list(self, commitId, path):
        return self._build_project_url() + '/files/' + commitId + '/' + path

    def files_upload(self, path):
        return self._build_project_url() + path

    def blobs_get(self, key):
        return self._build_project_url() + '/blobs/' + key

    # Endpoint URLs
    def _build_endpoint_url(self):
        return self.host + '/v1/' + \
            self._owner_username + '/' + self._project_name + '/endpoint'

    def endpoint(self):
        return self._build_endpoint_url()

    def endpoint_state(self):
        return self._build_endpoint_url() + '/state'

    def endpoint_publish(self):
        return self._build_endpoint_url() + '/publishRelease'

    # Miscellaneous URLs
    def deployment_version(self):
        return self.host + '/version'
