import hashlib
import math
import os
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from logging import Logger
from typing import AnyStr

from retry import retry

from domino.http_request_manager import _HttpRequestManager
from domino.routes import _Routes

FILE_UPLOAD_SETTING_DEFAULT = "Ignore"
MAX_WORKERS = 10
MAX_UPLOAD_ATTEMPTS = 10
MB = 2 ** 20  # 2^20 bytes - 1 Megabyte
SLEEP_TIME_IN_SEC = 3
UPLOAD_READ_TIMEOUT_IN_SEC = 30


@dataclass
class UploadChunk:
    """ Class for keeping track of a dataset upload chunk."""
    absolute_path: str
    chunk_number: int
    dataset_id: str
    file_name: str
    file_size: int
    upload_key: str
    identifier: str
    relative_path: str
    target_chunk_size: int
    total_chunks: int


class Uploader:
    def __init__(
        self,
        csrf_no_check_header: {str, str},
        dataset_id: str,
        local_path_to_file_or_directory: str,
        log: Logger,
        request_manager: _HttpRequestManager,
        routes: _Routes,
        target_relative_path: str,

        file_upload_setting: str,
        max_workers: int,
        target_chunk_size: int,
        interrupted: bool = False
    ):
        cleaned_relative_local_path = os.path.relpath(os.path.normpath(local_path_to_file_or_directory), start=os.curdir)
        # in case running on windows
        cleaned_relative_local_path = self._get_unix_style_path(cleaned_relative_local_path)        

        self.csrf_no_check_header = csrf_no_check_header
        self.dataset_id = dataset_id
        self.local_path_file_or_directory = cleaned_relative_local_path
        self.log = log
        self.request_manager = request_manager
        self.routes = routes
        self.target_chunk_size = target_chunk_size or 8 * MB
        self.file_upload_setting = file_upload_setting or FILE_UPLOAD_SETTING_DEFAULT
        self.max_workers = max_workers or MAX_WORKERS
        self.target_relative_path = target_relative_path
        self.interrupted = interrupted
        self.upload_key = None  # this will be set once the session is started

    def __enter__(self):
        # creating upload session
        start_upload_body = {
            "filePaths": [],
            "fileCollisionSetting": self.file_upload_setting
        }
        start_upload_url = self.routes.datasets_start_upload(self.dataset_id)
        self.upload_key = self.request_manager.post(start_upload_url, json=start_upload_body).json()
        if not self.upload_key:
            raise RuntimeError(f"upload key for {self.dataset_id} not found. Session could not start.")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # catching errors
        if exc_type is not None:
            self.log.error(f"Upload for dataset {self.dataset_id} and file or directory "
                           f"`{self.local_path_file_or_directory}` failed, attempting to cancel session. "
                           f"Please try again.")
            self.log.error(f"Error type: {exc_val}. Error message: {exc_tb}.")
            if not isinstance(exc_type, ValueError):
                self._cancel_upload_session()  # is it is a ValueError, canceling session would fail
            return False
        # ending snapshot upload
        try:
            url = self.routes.datasets_end_upload(self.dataset_id, self.upload_key, self.target_relative_path)
            self.request_manager.get(url)
            self.log.info("Upload session ended successfully.")
            return True
        except:
            self.log.error("Ending snapshot upload failed. See error for details. Attempting to cancel "
                           "upload session.")
            self._cancel_upload_session()
            return False

    def upload(self):
        try:
            if not self.upload_key:
                raise RuntimeError(f"upload key for {self.dataset_id} not found. Please start session before uploading.")
            q = self._create_chunk_queue()
            with ThreadPoolExecutor(self.max_workers) as executor:
                # list ensures all the threads are complete before returning results
                results = list(executor.map(self._upload_chunk, q))
            return self.local_path_file_or_directory
        except KeyboardInterrupt:
            self.interrupted = True  # this will allow the threads to stop properly
            raise

    def _cancel_upload_session(self):
        url = self.routes.datasets_cancel_upload(self.dataset_id, self.upload_key)
        self.request_manager.get(url)
        self.log.info("Upload session cancelled successfully.")

    def _create_chunk_queue(self) -> list[UploadChunk]:
        if not os.path.exists(self.local_path_file_or_directory):
            raise ValueError(f"local file or directory {self.local_path_file_or_directory} does not exist.")
        if os.path.isfile(self.local_path_file_or_directory):
            return self._create_chunks(self.local_path_file_or_directory)
        chunk_q = []
        for dirpath, _, filenames in os.walk(self.local_path_file_or_directory):
            for filename in filenames:
                # construct the relative path for each file
                relative_path_to_file = os.path.join(dirpath, filename)

                # in case running on windows
                cleaned_relative_path = self._get_unix_style_path(relative_path_to_file)
                
                # append chunk to queue
                chunk_q.extend(self._create_chunks(cleaned_relative_path))
        return chunk_q

    def _create_chunks(self, local_path_file, starting_index=1) -> list[UploadChunk]:
        file_size = os.path.getsize(local_path_file)
        file_name = os.path.basename(local_path_file)
        total_chunks = max(int(math.ceil(float(file_size) / self.target_chunk_size)), 1)
        return [UploadChunk(absolute_path=os.path.abspath(local_path_file), chunk_number=chunk_num,
                            dataset_id=self.dataset_id, file_name=file_name, file_size=file_size,
                            identifier=f"{file_size}-{file_name}", relative_path=local_path_file,
                            target_chunk_size=self.target_chunk_size, total_chunks=total_chunks,
                            upload_key=self.upload_key)
                for chunk_num in range(starting_index, total_chunks + 1)]

    def _upload_chunk(self, chunk: UploadChunk) -> None:
        if self.interrupted:
            return
        # read the file chunk
        starting_skip = chunk.target_chunk_size * (chunk.chunk_number - 1)
        with open(chunk.absolute_path, 'rb') as file:
            file.seek(starting_skip)
            chunk_data = file.read(chunk.target_chunk_size)

        # testing chunk
        should_upload, checksum = self._test_chunk(chunk, chunk_data)

        # uploading chunk
        if should_upload:
            self._upload_chunk_retry(checksum, chunk, chunk_data)
        else:
            self.log.info(f"Skipping chunk {chunk.chunk_number} of {chunk.total_chunks} for {chunk.file_name}")

    @retry(tries=MAX_UPLOAD_ATTEMPTS, delay=SLEEP_TIME_IN_SEC, backoff=2)
    def _upload_chunk_retry(self, checksum: str, chunk: UploadChunk, chunk_data):
        if self.interrupted:
            return
        actual_chunk_size = len(chunk_data)
        # uploading chunk
        self.log.info(f"Uploading chunk {chunk.chunk_number} of {chunk.total_chunks} for {chunk.file_name}")
        upload_chunk_url = self.routes.datasets_upload_chunk(chunk.dataset_id, chunk.upload_key,
                                                             chunk.chunk_number, chunk.total_chunks,
                                                             chunk.target_chunk_size, actual_chunk_size,
                                                             chunk.identifier, chunk.relative_path,
                                                             checksum)
        # files to pass in post's **kwargs
        files = {
            chunk.relative_path: (chunk.file_name, chunk_data, 'application/octet-stream')
        }
        start_time_ns = time.time_ns()
        # making call to upload
        self.request_manager.post(upload_chunk_url, files=files, timeout=UPLOAD_READ_TIMEOUT_IN_SEC,
                                  headers=self.csrf_no_check_header)
        end_time_ns = time.time_ns()
        duration_ns = end_time_ns - start_time_ns
        bandwidth_bytes_per_second = actual_chunk_size / duration_ns * 1000000000.0
        self.log.info(f"Uploaded chunk {chunk.chunk_number} of {chunk.total_chunks} for {chunk.file_name} "
                      f"in {duration_ns / 1_000_000:.1f}ms ({bandwidth_bytes_per_second:.1f} B/s)")

    def _test_chunk(self, chunk: UploadChunk, chunk_data: AnyStr) -> (bool, int):
        # computing the MD5 checksum
        digest = hashlib.md5()
        digest.update(chunk_data)

        chunk_checksum = digest.hexdigest().upper()
        # testing chunk
        test_chunk_url = self.routes.datasets_test_chunk(chunk.dataset_id, chunk.upload_key, chunk.chunk_number,
                                                         chunk.total_chunks, chunk.identifier, chunk_checksum)
        # test chunk returns no content if it should upload
        return self.request_manager.get(test_chunk_url).status_code == 204, chunk_checksum

    def _get_unix_style_path(self, path: str) -> str:
        # when running on Windows, converts path to Unix-style path, which the upload chunk API expects
        if os.sep != '/':
            path = path.replace(os.sep, '/')
        return path
