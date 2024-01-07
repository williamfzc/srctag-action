import json
import os
import pathlib
import subprocess
import sys
import typing

import networkx
import requests
from loguru import logger
from pydantic import BaseModel
from srctag.collector import Collector
from srctag.model import RuntimeContext

URL_BACKEND_VERCEL = r"https://srctag-http-api.vercel.app/api/v1/conclusion/github"


class ConclusionRequest(BaseModel):
    repo_name: str
    issue_number: int
    # for making sure that this request came from GitHub
    token: str
    graph_data: str
    diff_files: typing.List[str]


def main():
    # locally run
    args = sys.argv[1:]
    input_tag_file = args[0]
    input_before_sha = args[1]
    input_after_sha = args[2]
    input_repo_token = args[3]
    input_issue_number = args[4]
    input_n_result = int(args[5])
    input_repo_name = os.getenv("GITHUB_REPOSITORY")
    input_github_workspace = "/github/workspace"

    if not (input_before_sha and input_after_sha):
        logger.warning("It seems not a pull request. Bye~")
        return
    logger.info(f"diff between {input_before_sha} and {input_after_sha}")

    # diff
    subprocess.check_call(["git", "config", "--global", "--add", "safe.directory", input_github_workspace])
    subprocess.check_call(["git", "status"])
    git_diff_command = ['git', 'diff', '--name-only', input_before_sha, input_after_sha]
    output = subprocess.check_output(git_diff_command).decode().strip()
    diff_files = output.split('\n')
    logger.info(f"diff files: {diff_files}")

    # optional tags
    tag_file = pathlib.Path(input_tag_file)
    tags = []
    if tag_file.is_file():
        with tag_file.open() as f:
            lines = f.readlines()
        tags = [each.strip() for each in lines]
        logger.info(f"tags: {tags}")
    else:
        logger.info(f"{tag_file.absolute()} is not a file")

    # main work
    result = tag(tags, diff_files)
    relation_graph = result.relations

    # upload
    nodes_to_remove = [node for node, data in relation_graph.nodes(data=True) if data.get('node_type') == 'commit_sha']
    relation_graph.remove_nodes_from(nodes_to_remove)

    graph_data = networkx.node_link_data(relation_graph)
    json_data = json.dumps(graph_data)
    upload_obj = ConclusionRequest(
        repo_name=input_repo_name,
        issue_number=input_issue_number,
        token=input_repo_token,
        graph_data=json_data,
        diff_files=diff_files,
    )
    response = requests.post(URL_BACKEND_VERCEL, json=upload_obj.dict())
    logger.info(f"backend response: {response}")


def tag(_: typing.Iterable[str], diff_files: typing.Iterable[str]) -> RuntimeContext:
    # todo: currently, we aim at shipping a MVP
    collector = Collector()
    collector.config.include_file_list = set(diff_files)
    ctx = collector.collect_metadata()
    return ctx


if __name__ == '__main__':
    main()
