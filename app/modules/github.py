import requests

from . import models


class Github:
    def __init__(self):
        self.repo = "Super-Protocol/sp-vm"
        self.latest_release_url = (
            f"https://api.github.com/repos/{self.repo}/releases/latest"
        )

    def _get_release_json(self):
        r = requests.get(self.latest_release_url)
        if r.status_code != 200:
            raise Exception(
                f"failed to get latest release from github, status code: {r.status_code}, response: {r.json()}"
            )

        return r.json()

    def _get_release_name(self, release_json):
        release_name = release_json.get("tag_name", None)
        if release_name is None:
            raise Exception(
                f"failed to get release name from github release, response: {release_json}"
            )
        return release_name

    def get_latest_release(self) -> models.Release:
        release_json = self._get_release_json()
        release_name = self._get_release_name(release_json)

        assets = release_json.get("assets", None)
        if assets is None:
            raise Exception(
                f"failed to get assets from github release: {release_name}, response: {release_json}"
            )

        vm_json_link = next(
            iter(
                [
                    x.get("browser_download_url", None)
                    for x in assets
                    if x.get("name", None) == "vm.json"
                ]
            ),
            None,
        )

        if vm_json_link is None:
            raise Exception(
                f"failed to get download link from github release: {release_name}, response: {release_json}"
            )
        print(vm_json_link)
        return models.Release(name=release_name)
