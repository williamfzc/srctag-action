import os
import pathlib
import subprocess
import sys
import typing

from github import Github
from loguru import logger
from pandas import Series
from srctag.collector import Collector
from srctag.storage import Storage
from srctag.tagger import Tagger
from tabulate import tabulate


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

    tag_file = pathlib.Path(input_tag_file)
    assert tag_file.is_file(), f"{tag_file.absolute()} is not a file"
    with tag_file.open() as f:
        lines = f.readlines()
    tags = [each.strip() for each in lines]
    logger.info(f"tags: {tags}")

    # diff
    subprocess.check_call(["git", "config", "--global", "--add", "safe.directory", input_github_workspace])
    subprocess.check_call(["git", "status"])
    git_diff_command = ['git', 'diff', '--name-only', input_before_sha, input_after_sha]
    output = subprocess.check_output(git_diff_command).decode().strip()
    diff_files = output.split('\n')
    logger.info(f"diff files: {diff_files}")

    # main work
    result = tag(tags)

    # save result for uploading
    output_dot = os.path.join(input_github_workspace, "srctag.dot")
    result.export_dot(output_dot)
    subprocess.check_call(f"echo 'SRCTAG_GRAPH_FILE={output_dot}' >> '$GITHUB_ENV'", shell=True)

    # calc impacts
    comment_content = "# srctag report\n\n"

    # detail table
    table = []
    headers = ["File", "Related Topics"]
    tag_scores = dict()
    for each in diff_files:
        selected_tags: Series = result.tags_by_file(each).head(input_n_result)
        table.append((each, selected_tags.index.tolist()))

        for each_tag, each_score in selected_tags.items():
            if each_tag in tag_scores:
                tag_scores[each_tag] += each_score
            else:
                tag_scores[each_tag] = each_score
        # END loop tag
    # END loop file

    comment_content += tabulate(table, headers, tablefmt="github")

    # summary table
    table = []
    headers = ["Related Topics", "Score"]
    for each_tag, score in tag_scores.items():
        table.append((tag, score))
    comment_content += ("\n\n" + tabulate(table, headers, tablefmt="github"))

    # give a feedback
    # temp removed
    # comment(input_repo_token, input_repo_name, int(input_issue_number), comment_content)


def tag(tags: typing.Iterable[str]):
    collector = Collector()
    collector.config.repo_root = "."
    ctx = collector.collect_metadata()
    storage = Storage()
    storage.embed_ctx(ctx)
    tagger = Tagger()
    tagger.config.tags = tags
    tag_dict = tagger.tag(storage)
    return tag_dict


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
