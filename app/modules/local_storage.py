from . import models
import tempfile
import logging
import os
import shutil
import json
from pathlib import Path

from . import utils


class LocalStorage:
    def __init__(self, basedir: str):
        self.basedir = basedir
        self.logger = logging.getLogger(__name__)
        self.logger.debug(f"creating {self.basedir}")
        utils.ensure_writable_dir(self.basedir)

    def get_latest_release(self):
        pass

    def _save_vm_json(self, target_dir, vm_json) -> None:
        filename = Path(target_dir) / Path("vm.json")
        with open(filename, "w") as f:
            json.dump(vm_json, f, ensure_ascii=False, indent=2)
            f.write("\n")

    def save_release(
        self,
        release: models.Release,
        temp_dir: tempfile.TemporaryDirectory,
        vm_json: dict,
    ) -> None:
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

        self.logger.debug(f"saving vm.json to {target_dir}")
        self._save_vm_json(target_dir, vm_json)
        temp_dir.cleanup()
