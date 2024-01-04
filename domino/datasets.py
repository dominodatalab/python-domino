import hashlib
import math
import os
import time
from concurrent.futures import ThreadPoolExecutor
from logging import Logger
from typing import AnyStr

from domino.http_request_manager import _HttpRequestManager
from domino.routes import _Routes

FILE_UPLOAD_SETTING_DEFAULT = "Overwrite"
MAX_WORKERS = 10
MAX_UPLOAD_ATTEMPTS = 10
MB = 2 ** 20  # 2^20 bytes - 1 Megabyte
SLEEP_TIME_IN_SEC = 5
UPLOAD_READ_TIMEOUT_IN_SEC = 30


class UploadChunk:
    def __init__(
            self,
            absolute_path: str,
            chunk_number: int,
            dataset_id: str,
            file_name: str,
            file_size: int,
            upload_key: str,
            identifier: str,
            relative_path: str,
            target_chunk_size: int,
            total_chunks: int,
    ):
        self.absolute_path = absolute_path
        self.chunk_number = chunk_number
        self.dataset_id = dataset_id
        self.file_name = file_name
        self.file_size = file_size
        self.identifier = identifier
        self.relative_path = relative_path
        self.target_chunk_size = target_chunk_size
        self.total_chunks = total_chunks
        self.upload_key = upload_key


class Uploader:
    def __init__(
            self,
            csrf_no_check_header: {str, str},
            dataset_id: str,
            local_path_to_file: str,
            log: Logger,
            request_manager: _HttpRequestManager,
            routes: _Routes,

            file_upload_setting: str,
            max_workers: int,
            target_chunk_size: int,

    ):
        self.csrf_no_check_header = csrf_no_check_header
        self.dataset_id = dataset_id
        self.local_path_file = local_path_to_file
        self.log = log
        self.request_manager = request_manager
        self.routes = routes
        self.target_chunk_size = target_chunk_size or 8 * MB
        self.file_upload_setting = file_upload_setting or FILE_UPLOAD_SETTING_DEFAULT
        self.max_workers = max_workers or MAX_WORKERS
        self.upload_key = None  # this will be set once the session is started

    def start_upload_session(self):
        start_upload_body = {
            "filePaths": [],
            "fileCollisionSetting": self.file_upload_setting
        }
        start_upload_url = self.routes.datasets_start_upload(self.dataset_id)
        self.upload_key = self.request_manager.post(start_upload_url, json=start_upload_body).json()
        if not self.upload_key:
            raise RuntimeError(f"upload key for {self.dataset_id} not found. Session could not start.")

    def upload(self):
        if not self.upload_key:
            raise RuntimeError(f"upload key for {self.dataset_id} not found. Please start session before uploading.")
        q = self._create_chunk_queue()
        with ThreadPoolExecutor(self.max_workers) as executor:
            # list ensures all the threads are complete before returning results
            results = list(executor.map(self._upload_chunk, q))
        return results

    def cancel_upload_session(self):
        url = self.routes.datasets_cancel_upload(self.dataset_id, self.upload_key)
        return self.request_manager.delete(url).json()

    def end_upload_session(self):
        if not self.upload_key:
            raise RuntimeError(f"upload key for {self.dataset_id} not found. Could not end session.")
        url = self.routes.datasets_end_upload(self.dataset_id, self.upload_key)
        return self.request_manager.get(url).json()

    def _create_chunk_queue(self) -> [UploadChunk]:
        file_size = os.path.getsize(self.local_path_file)
        file_name = os.path.basename(self.local_path_file)
        total_chunks = max(int(math.ceil(float(file_size) / self.target_chunk_size)), 1)
        return [UploadChunk(absolute_path=os.path.abspath(self.local_path_file),  chunk_number=chunk_num,
                            dataset_id=self.dataset_id, file_name=file_name, file_size=file_size,
                            identifier=f"{file_size}-{file_name}", relative_path=self.local_path_file,
                            target_chunk_size=self.target_chunk_size, total_chunks=total_chunks,
                            upload_key=self.upload_key)
                for chunk_num in range(1, total_chunks + 1)]

    def _upload_chunk(self, chunk: UploadChunk):
        # read the file chunk
        starting_skip = chunk.target_chunk_size * (chunk.chunk_number - 1)
        with open(chunk.absolute_path, 'rb') as file:
            file.seek(starting_skip)
            chunk_data = file.read(chunk.target_chunk_size)

        # testing chunk
        should_upload, checksum = self._test_chunk(chunk, chunk_data)

        # uploading chunk
        if should_upload:
            upload_try = 1
            uploaded = False
            while upload_try <= MAX_UPLOAD_ATTEMPTS and not uploaded:
                try:
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
                    uploaded = True
                except Exception:
                    if upload_try > MAX_UPLOAD_ATTEMPTS:
                        raise Exception(f"Uploading chunk {chunk.chunk_number} of {chunk.total_chunks} "
                                           f"for {chunk.file_name} failed. Please try again")
                    else:
                        self.log.info(f"Failed to upload chunk {chunk.chunk_number} of {chunk.total_chunks} "
                                      f"for {chunk.file_name}. Retrying...")
                        time.sleep(SLEEP_TIME_IN_SEC * upload_try)
                        upload_try += 1
        else:
            self.log.info(f"Skipping chunk {chunk.chunk_number} of {chunk.total_chunks} for {chunk.file_name}")

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
