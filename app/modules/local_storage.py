import tempfile
import logging
import shutil
import json
import os
from pathlib import Path

from . import models, utils


class LocalStorage:
    def __init__(self, basedir: str):
        self.basedir = basedir
        self.logger = logging.getLogger(__name__)
        self.logger.debug(f"creating {self.basedir}")
        utils.ensure_writable_dir(self.basedir)
        self.latest_mark_path = Path(self.basedir) / Path("latest")

    def get_latest_release(self) -> models.Release | None:
        latest_release_name = self._get_latest_mark()
        if latest_release_name is None:
            self.logger.info(f"no local latest releases found")
            return None

        release_path = Path(self.basedir) / Path(latest_release_name)
        if not release_path.is_dir():
            self.logger.error(f"locally latest release {latest_release_name} defined but {release_path} doesn't exists")
            return None

        vm_json = self._get_vm_json(release_path)
        if vm_json is None:
            self.logger.error(f"locally latest release {latest_release_name} defined but {vm_json} doesn't exists")
            return None

        release = models.get_release_from_vm_json(latest_release_name, vm_json)
        if release is None:
            self.logger.error(f"can't construct release {latest_release_name} from {vm_json}")
            return None

        if not models.is_release_files_valid(release, release_path):
            self.logger.error(f"some release files isn't valid for {latest_release_name}")
            return None

        self.logger.debug(f"locally latest release {latest_release_name} is valid")
        return release

    def _save_vm_json(self, target_dir: str, vm_json: dict) -> None:
        filename = Path(target_dir) / Path("vm.json")
        self.logger.debug(f"saving vm.json to {filename}")
        with open(filename, "w") as f:
            json.dump(vm_json, f, ensure_ascii=False, indent=2)
            f.write("\n")

    def _get_vm_json(self, target_dir: Path) -> dict | None:
        filename = target_dir / Path("vm.json")
        try:
            with open(filename, "r") as f:
                vm_json = json.load(f)
            return vm_json
        # need to cover any not valid files, empty, or missing
        except Exception as e:
            self.logger.debug(f"failed to get vm.json from {target_dir}, reason: {e}")
            return None

    def _save_latest_mark(self, release_name: str) -> None:
        self.logger.debug(f"setting latest mark {release_name} to {self.latest_mark_path}")
        with open(self.latest_mark_path, "w") as f:
            f.write(release_name)

    def _get_latest_mark(self) -> str | None:
        try:
            with open(self.latest_mark_path, "r") as f:
                latest_mark = f.readline().strip()
            return latest_mark
        # need to cover any not valid files, empty, or missing
        except Exception as e:
            self.logger.debug(f"failed to get latest mark file from {self.latest_mark_path}, reason: {e}")
            return None

    def save_release(self, release: models.Release, temp_dir: tempfile.TemporaryDirectory) -> None:
        target_dir = Path(self.basedir) / Path(release.name)
        self.logger.info(f"saving release {release.name} to {target_dir}")

        self.logger.debug(f"removing {target_dir}")
        utils.remove_directory_full(target_dir)

        self.logger.debug(f"creating {target_dir}")
        utils.ensure_writable_dir(target_dir)

        for artifact_name, artifact in release.artifacts.iter_fields():
            filepath_src = Path(temp_dir.name) / Path(artifact.filename)
            filepath_dst = Path(target_dir) / Path(artifact.filename)
            self.logger.debug(f"moving file from {filepath_src} to {filepath_dst}")
            shutil.move(filepath_src, filepath_dst)

        self._save_vm_json(target_dir, release.vm_json)
        self._save_latest_mark(release.name)
        temp_dir.cleanup()
        self.logger.info(f"successfully saved release {release.name} to {target_dir}")
