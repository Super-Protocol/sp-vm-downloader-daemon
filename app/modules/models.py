from dataclasses import dataclass, fields
import json


@dataclass
class Artifact:
    bucket: str
    prefix: str
    filename: str
    sha256: str


@dataclass
class Artifacts:
    rootfs: Artifact
    bios: Artifact
    bios_amd: Artifact
    root_hash: Artifact
    kernel: Artifact

    def iter_fields(self):
        for f in fields(self):
            value = getattr(self, f.name)
            yield f.name, value


@dataclass
class Release:
    name: str
    artifacts: Artifacts


def get_release_from_vm_json(release_name: str, vm_json: dict) -> Release:
    artifacts = {}
    for f in fields(Artifacts):
        artifact_json = vm_json.get(f.name, None)
        if artifact_json is None:
            raise Exception(
                f"failed to get artifact json for {f.name} in vm_json: {vm_json}"
            )
        kwargs = {}
        for c in fields(Artifact):
            current_field = artifact_json.get(c.name, None)
            if current_field is None:
                raise Exception(
                    f"failed to get {c.name} for {f.name} in vm_json: {vm_json}"
                )
            kwargs[c.name] = current_field
        artifacts[f.name] = Artifact(**kwargs)
    return Release(name=release_name, artifacts=Artifacts(**artifacts))
