import logging
import json
from dataclasses import dataclass, fields
from pathlib import Path

from . import utils

__logger__ = logging.getLogger(__name__)


@dataclass
class Artifact:
    bucket: str
    prefix: str
    filename: str
    sha256: str


@dataclass
class Artifacts:
    image: Artifact
    bios: Artifact
    bios_amd: Artifact
    rootfs_hash: Artifact
    kernel: Artifact

    def iter_fields(self):
        for f in fields(self):
            value = getattr(self, f.name)
            yield f.name, value


@dataclass
class Release:
    name: str
    artifacts: Artifacts
    vm_json: dict


def get_release_from_vm_json(release_name: str, vm_json: dict) -> Release | None:
    try:
        artifacts = {}
        for f in fields(Artifacts):
            artifact_json = vm_json.get(f.name, None)
            if artifact_json is None:
                raise Exception(f"failed to get artifact json for {f.name} in vm_json: {vm_json}")
            kwargs = {}
            for c in fields(Artifact):
                current_field = artifact_json.get(c.name, None)
                if current_field is None:
                    raise Exception(f"failed to get {c.name} for {f.name} in vm_json: {vm_json}")
                kwargs[c.name] = current_field
            artifacts[f.name] = Artifact(**kwargs)
        return Release(name=release_name, artifacts=Artifacts(**artifacts), vm_json=vm_json)

    except Exception as e:
        __logger__.error(f"failed to get release {release_name} from {vm_json}, reason: {e}")
        return None


def is_release_files_valid(release: Release, release_path: Path) -> bool:
    for artifact_name, artifact in release.artifacts.iter_fields():
        artifact_path = release_path / Path(artifact.filename)
        if not artifact_path.is_file():
            __logger__.error(f"required release file {artifact_name} not found in path {release_path}")
            return False
        artifact_sha = utils.get_file_sha256(str(artifact_path))
        if artifact_sha != artifact.sha256:
            __logger__.error(
                f"release file {artifact_name} in {release_path} sha differs from declared in release json"
            )
            return False
    return True
