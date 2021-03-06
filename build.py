# -*- coding: utf-8 -*-

from dataclasses import dataclass, field
from functools import partial
import os
import json
import pathlib
import shutil
import sys

# Use symlinks on Linux, copy everything over on Windows
if sys.platform.startswith("linux"):
    default_folder = pathlib.Path("~/.factorio/mods").expanduser().resolve()
    link_function = partial(os.symlink, target_is_directory=True)
elif sys.platform.startswith("win"):
    default_folder = pathlib.Path(os.getenv("APPDATA")).joinpath(r"Factorio\mods")
    link_function = shutil.copytree


@dataclass
class ModBuilder:
    target_folder: pathlib.Path
    source_folder: pathlib.Path
    mod_key: str
    avoidables: list = field(default_factory=list)
    building_all: bool = False
    found_mods: list = field(default_factory=list)

    def build_mods(self):
        for mod in self.found_mods:
            new_target_folder = self.target_folder.joinpath(repr(mod))
            link_function(
                src=self.source_folder.joinpath(mod.name), dst=new_target_folder,
            )

    def delete_mods(self, delete_zips=True):
        if delete_zips:
            for mod in self.found_mods:
                for f in self.target_folder.glob(f"{mod.name}_[0-9.]*.zip"):
                    f.unlink()

        for mod in self.found_mods:
            for folder in self.target_folder.glob(f"{mod.name}_[0-9.]*"):
                if folder.is_symlink():
                    os.unlink(folder)
                elif folder.is_dir():
                    shutil.rmtree(folder)

    def find_mods(self):
        """
        If build_all, returns all mods in the source_folder.
        Else only the ones found in mod_folder.
        """
        source_mods = [
            Mod(path) for path in self.source_folder.glob(f"*{self.mod_key}*")
        ]
        if self.building_all:
            target_mods = source_mods
        else:
            target_mods = [
                Mod(path) for path in self.target_folder.glob(f"*{self.mod_key}*")
            ]

        self.found_mods = [
            mod
            for mod in target_mods
            if not any(avoidable in mod.name for avoidable in self.avoidables)
        ]


@dataclass
class Mod:
    path: pathlib.Path
    name: str
    version: str

    def __init__(self, path):
        self.path = path
        self._initialize()

    def __repr__(self):
        return f"{self.name}_{self.version}"

    def _initialize(self):
        if self.path.is_file() and not self.path.is_symlink():
            # zip file, name and version is in the filename
            last_dash_idx = self.path.name.rfind("_")
            self.name = self.path.name[:last_dash_idx]
            self.version = self.path.name[last_dash_idx + 1 : -4]
        else:
            self._data_from_info()

    def _data_from_info(self):
        with open(self.path.joinpath("info.json"), "r") as info_file:
            try:
                data = json.load(info_file)
            except:
                print(info_file)
                raise
            self.name = data["name"]
            self.version = data["version"]


if __name__ == "__main__":
    mb = ModBuilder(
        target_folder=default_folder,
        source_folder=pathlib.Path(__file__).parent.resolve(),
        mod_key="omni",
        avoidables=[
            "omnimatter_chemistry",
            "omnimatter_logistics",
            "omnimatter_marathon",
            "omnimatter_research",
        ],
        building_all=True,
    )
    mb.find_mods()
    mb.delete_mods()
    mb.build_mods()
