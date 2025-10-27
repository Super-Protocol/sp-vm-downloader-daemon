import logging
from concurrent import futures
from pathlib import Path

import grpc

from .local_storage import LocalStorage
from .github import Github
from .storj import StorJ
from .proto import sp_vm_downloader_pb2_grpc, sp_vm_downloader_pb2


class ServerServicer(sp_vm_downloader_pb2_grpc.SpVmDownloaderServicer):
    def __init__(self, gh: Github, sj: StorJ, ls: LocalStorage):
        self.logger = logging.getLogger(__name__)
        self.gh = gh
        self.sj = sj
        self.ls = ls

    def GetRelease(self, request, context) -> sp_vm_downloader_pb2.ReleaseReply:
        self.logger.info(f'received request for release: `{request.name}`')
        try:
            local_release = self.ls.get_release(request.name)
            if local_release is not None:
                path = self.ls.get_release_path(request.name)
                self.logger.info(f'found local valid release: `{request.name}`')
                return sp_vm_downloader_pb2.ReleaseReply(path=str(path), msg="", success=True)

            self.logger.info(f'searching github release: `{request.name}`')
            github_release = self.gh.get_specific_release(request.name)
            if github_release is None:
                raise Exception(f'github release: `{request.name}` not found')
            self.logger.info(f'found github release: `{request.name}`')

            is_latest = self.gh.get_latest_release() == github_release
            self.logger.info(f'downloading release from github: `{request.name}`')
            temp_release_dir = self.sj.download_release_files(github_release)
            self.logger.info(f'saving release from github: `{request.name}`')
            self.ls.save_release(github_release, temp_release_dir, is_latest=is_latest)
            path = self.ls.get_release_path(request.name)
            return sp_vm_downloader_pb2.ReleaseReply(path=str(path), msg="", success=True)
        except Exception as e:
            return sp_vm_downloader_pb2.ReleaseReply(path="", msg=str(e), success=False)

    def GetLatestGithubReleaseName(self, request, context) -> sp_vm_downloader_pb2.LatestGithubReleaseNameReply:
        try:
            github_release = self.gh.get_latest_release()
            if github_release is None:
                raise Exception(f'github latest release not found')
            return sp_vm_downloader_pb2.LatestGithubReleaseNameReply(name=github_release.name, msg="", success=True)
        except Exception as e:
            return sp_vm_downloader_pb2.LatestGithubReleaseNameReply(name="", msg=str(e), success=False)


class Server:
    def __init__(self, socket_path_str: str, gh: Github, sj: StorJ, ls: LocalStorage):
        self.logger = logging.getLogger(__name__)

        self.socket_path = Path(socket_path_str)
        self.socket_path.parent.mkdir(parents=True, exist_ok=True)

        self.server = None
        self.pool = futures.ThreadPoolExecutor(max_workers=1)
        self.servicier = ServerServicer(gh, sj, ls)

        self.stop_timeout = 120

    def run(self) -> None:
        if self.server is not None:
            self.logger.error(f'server is already running on `{self.socket_path}`, stop it first')
            return

        if self.socket_path.exists():
            self.socket_path.unlink()

        self.server = grpc.server(self.pool)
        self.server.add_insecure_port(f"unix://{self.socket_path}")
        sp_vm_downloader_pb2_grpc.add_SpVmDownloaderServicer_to_server(self.servicier, self.server)

        self.server.start()
        self.logger.info(f'server is started on `{self.socket_path}`')

    def stop(self) -> None:
        if self.server is not None:
            self.logger.info(f'stopping server on `{self.socket_path}`, timeout: `{self.stop_timeout}`')
            self.server.stop(self.stop_timeout)
            self.server = None

        if self.socket_path.exists():
            self.logger.info(f'removing socket `{self.socket_path}`')
            self.socket_path.unlink()
