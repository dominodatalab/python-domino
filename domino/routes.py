class _Routes:
    def __init__(self, host, owner_username, project_name):
        self.host = host
        self._owner_username = owner_username
        self._project_name = project_name

    def runs_list(self):
        return self._build_url() + '/runs'

    def runs_start(self):
        return self._build_url() + '/runs'

    def files_list(self, commitId, path):
        return self._build_url() + '/files/' + commitId + '/' + path

    def blobs_get(self, key):
        return self._build_url() + '/blobs/' + key

    def _build_url(self):
        return self.host + '/v1/projects/' + self._owner_username + '/' + self._project_name
