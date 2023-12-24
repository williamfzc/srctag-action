import os
import pathlib
import subprocess
import sys
import typing

from github import Github
from loguru import logger
from srctag.collector import Collector
from srctag.model import RuntimeContext
from srctag.storage import MetadataConstant


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

    for each_file in diff_files:
        related_nodes = relation_graph.neighbors(each_file)
        related_issues = [node for node in related_nodes if
                          relation_graph.nodes[node]["node_type"] == MetadataConstant.KEY_ISSUE_ID]
        related_commits = [node for node in related_nodes if
                           relation_graph.nodes[node]["node_type"] == MetadataConstant.KEY_COMMIT_SHA]
        logger.info(f"file {each_file} related to issues {len(related_issues)}, commits {len(related_commits)}")


def tag(_: typing.Iterable[str], diff_files: typing.Iterable[str]) -> RuntimeContext:
    # todo: currently, we aim at shipping a MVP
    collector = Collector()
    collector.config.include_file_list = set(diff_files)
    ctx = collector.collect_metadata()
    return ctx


def comment(token: str, repo_id: str, issue_number: int, content: str):
    logger.info(f"send comment to {repo_id}, issue id: {issue_number}")
    g = Github(token)
    repo = g.get_repo(repo_id)
    pr = repo.get_pull(issue_number)
    comments = pr.get_issue_comments()
    for each in comments:
        if "srctag report" in each.body:
            logger.info(f"found an existed comment: {each.id}, edit directly")
            each.edit(content)
            return

    # no existed comment
    pr.create_issue_comment(content)


if __name__ == '__main__':
    main()
