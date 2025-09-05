import logging
import tempfile
import subprocess
from . import models, utils
from pathlib import Path


class StorJ:
    def __init__(self, token: str):
        self.token = token
        self.logger = logging.getLogger(__name__)

    def _download_file(self, bucket: str, prefix: str, filename: str, dst: str) -> None:
        url = f"sj://{bucket}/{prefix}/{filename}"
        cmd = [
            "/usr/local/bin/uplink",
            "cp",
            "--parallelism",
            "16",
            "--access",
            self.token,
            url,
            dst,
        ]
        res = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=1800
        )
        if res.returncode != 0:
            raise Exception(
                f"failed to download file {filename}, command: {cmd}, result: {res.stdout}"
            )

    def _download_artifact(
        self,
        directory: str,
        release: models.Release,
        artifact_name: str,
        artifact: models.Artifact,
    ) -> tempfile.NamedTemporaryFile:
        self.logger.info(
            f"downloading artifact: {artifact_name} for release: {release.name}"
        )
        filename = Path(directory) / Path(artifact.filename)
        self._download_file(
            artifact.bucket, artifact.prefix, artifact.filename, filename
        )
        self.logger.debug(
            f"succesfully downloaded: {artifact_name} for release: {release.name}"
        )
        self.logger.debug(
            f"verifying sha256 for: {artifact_name} for release: {release.name}"
        )
        downloaded_file_sha256 = utils.get_file_sha256(filename)
        if downloaded_file_sha256 != artifact.sha256:
            raise Exception(
                f"downloaded file sha256 isn't match, expected: {artifact.sha256}, actual: {downloaded_file_sha256}"
            )

    def download_release_files(
        self, release: models.Release
    ) -> tempfile.TemporaryDirectory:
        self.logger.info(f"downloading release: {release.name}")

        artifacts = release.artifacts

        temp_dir = tempfile.TemporaryDirectory(
            prefix="sp_downloader_", suffix=f"_{release.name}"
        )
        self.logger.debug(f"created temp dir: {temp_dir.name}")

        for artifact_name, artifact in artifacts.iter_fields():
            self._download_artifact(temp_dir.name, release, artifact_name, artifact)
        return temp_dir
