#!/usr/bin/env python3

# Copyright 2022 The MLX Contributors
#
# SPDX-License-Identifier: Apache-2.0

"""
    This script is used to (re)generate the README.md file with the listing of
    default assets found in the Katalog repo.
    Run it from the project root folder via `make update_asset_list`.
"""


from __future__ import print_function

from glob import glob
from os.path import abspath, dirname, relpath
import yaml
import textwrap
import json

asset_types = [
    "pipeline",
    "component",
    "model",
    "dataset",
    "notebook"
]

script_path = abspath(dirname(__file__))
project_dir = dirname(script_path)

katalog_dir = f"{project_dir}/../"


def get_list_of_yaml_files_in_katalog(asset_type: str) -> list[str]:

    yaml_files = glob(f"{katalog_dir}/{asset_type}-samples/**/*.yaml", recursive=True)

    yaml_files = [filepath for filepath in yaml_files
                  if not any(word in filepath for word in ["template", "test", "src"])]

    return sorted(yaml_files)


def generate_katalog_dict() -> dict:

    katalog_dict = dict()

    for asset_type in asset_types:

        yaml_files = get_list_of_yaml_files_in_katalog(asset_type)
        katalog_asset_list = []

        for yaml_file in yaml_files:

            with open(yaml_file) as f:
                yaml_dict = yaml.load(f, Loader=yaml.FullLoader)

                if asset_type == "pipeline":
                    template_metadata = yaml_dict.get("metadata") or dict()
                    annotations = template_metadata.get("annotations", {})
                    pipeline_spec = json.loads(annotations.get("pipelines.kubeflow.org/pipeline_spec", "{}"))
                    asset_name: str = pipeline_spec.get("name", "").strip()
                    if asset_name == asset_name.lower() and "-" in asset_name and " " not in asset_name:
                        asset_name = asset_name.replace("-", " ").title()
                else:
                    asset_name = yaml_dict.get("name") or yaml_dict.get("metadata", {}).get("name", "")

                asset_name = title_case_asset_name(asset_name)

                asset_url = "./" + relpath(yaml_file, katalog_dir)

            katalog_asset_item = {
                "name": asset_name,
                "url": asset_url
            }

            katalog_asset_list.append(katalog_asset_item)

        katalog_dict[asset_type + "s"] = katalog_asset_list

    return katalog_dict


def title_case_asset_name(asset_name):

    acronyms = "AI AIF360 ART IBM JFK KFP MLM NOAA WML ML".split(" ")
    prepositions = "on in of and or with".split(" ")

    text_replacements = {
        "Codenet": "CodeNet",
        "Kfp Tekton": "KFP-Tekton",
        "Publaynet": "PubLayNet",
        "Pubtabnet": "PubTabNet",
        "Tensorflow": "TensorFlow",
    }

    text_replacements.update({word.title(): word.upper() for word in acronyms})
    text_replacements.update({word.title(): word.lower() for word in prepositions})

    asset_name = asset_name.title()

    if any(word in asset_name for word in text_replacements.keys()):
        # reverse replacements so we replace MLM before ML (don't want MLm)
        for word, replacement in sorted(text_replacements.items(), reverse=True):
            # split into words to not replace 'AI' in 'Airport'
            if word in asset_name.split(" "):
                asset_name = asset_name.replace(word, replacement)

    return asset_name


def generate_katalog_md() -> None:

    katalog_dict = generate_katalog_dict()

    md = list()

    md.append(textwrap.dedent("""\
        <!-- Do not edit. This file was generated by ./tools/python/update_asset_list.py (`make update_asset_list`) -->
        
        # MLX Katalog
        
        The MLX _Katalog_ project hosts the default assets to bootstrap the _Machine Learning Exchange_.
        
        # List of Default Catalog Assets
        
        """))

    for asset_type in katalog_dict.keys():
        if asset_type == "components":
            md.append("## Pipeline Components")
        else:
            md.append("## " + asset_type.capitalize())

        name_url_map = {d["name"]: d["url"] for d in katalog_dict[asset_type]}

        for name, url in name_url_map.items():
            md.append(f"* [{name}]({url})")

        md.append("\n")

    with open('README.md', 'w') as f:
        f.write("\n".join(md))


if __name__ == '__main__':

    print("Regenerating asset list in /README.md ...", end=" ")

    # TODO: Add functionality to compare current list of assets in the README.md
    #   to identify external asset links that are not in the `katalog` repo. Also
    #   download the `catalog_upload.json` file from the bootstrapper folder in
    #   the `mlx` repo to preserve external assets links in the regenerated README
    #   file. Also consider moving the external assets into the `katalog` repo
    generate_katalog_md()

    print("Done")

    print("Use `git diff` to evaluate which changes are desired!\n")