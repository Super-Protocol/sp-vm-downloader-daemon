import logging
import json

import requests

from . import models


class Github:
    def __init__(self):
        self.repo = "Super-Protocol/sp-vm"
        self.latest_release_url = f"https://api.github.com/repos/{self.repo}/releases/latest"
        self.logger = logging.getLogger(__name__)

    def _get_release_json(self):
        self.logger.info(f'fetching release json')
        r = requests.get(self.latest_release_url)
        if r.status_code != 200:
            raise Exception(
                f"failed to get latest release from github, status code: {r.status_code}, response: {r.json()}"
            )

        return r.json()

    def _get_release_name(self, release_json: dict) -> str:
        release_name = release_json.get("tag_name", None)
        if release_name is None:
            raise Exception(f"failed to get release name from github release, response: {release_json}")
        return release_name

    def _get_assets(self, release_name: str, release_json: dict) -> list[dict]:
        assets = release_json.get("assets", None)
        if assets is None:
            raise Exception(f"failed to get assets from github release: {release_name}, response: {release_json}")
        return assets

    def _get_vm_json_link(self, release_name: str, assets: dict) -> str:
        vm_json_link = next(
            iter([x.get("browser_download_url", None) for x in assets if x.get("name", None) == "vm.json"]),
            None,
        )
        if vm_json_link is None:
            raise Exception(
                f"failed to get download link from github release: {release_name}, response: {release_json}"
            )
        return vm_json_link

    def _get_vm_json(self, vm_json_link: str):
        self.logger.info(f'fetching vm json from `{vm_json_link}`')
        r = requests.get(vm_json_link)
        if r.status_code != 200:
            raise Exception(f"failed to get vm json from github, status code: {r.status_code}, response: {r.text}")

        return r.json()

    def get_latest_release(self) -> models.Release | None:
        self.logger.info(f'fetching latest release')
        release_json = self._get_release_json()
        release_name = self._get_release_name(release_json)
        self.logger.info(f'latest release is `{release_name}`')
        assets = self._get_assets(release_name, release_json)
        vm_json_link = self._get_vm_json_link(release_name, assets)
        vm_json = self._get_vm_json(vm_json_link)

        return models.get_release_from_vm_json(release_name, vm_json)

    def get_specific_release(self, name: str) -> models.Release | None:
        vm_json = self._get_vm_json(f'https://github.com/{self.repo}/releases/download/{name}/vm.json')

        return models.get_release_from_vm_json(name, vm_json)
