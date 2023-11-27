import pathlib
import subprocess
import sys
import typing

from loguru import logger
from srctag.collector import Collector
from srctag.storage import Storage
from srctag.tagger import Tagger


def main():
    # locally run
    args = sys.argv[1:]
    input_tag_file = args[0]
    input_before_sha = args[1]
    input_after_sha = args[2]

    if not (input_before_sha and input_after_sha):
        # ok

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
    subprocess.check_call(["ls"])
    subprocess.check_call(["git", "status"])
    subprocess.check_call(["git", "config", "--global", "--add", "safe.directory", "."])
    git_diff_command = ['git', 'diff', '--name-only', input_before_sha, input_after_sha]
    output = subprocess.check_output(git_diff_command).decode().strip()
    diff_files = output.split('\n')
    logger.info(f"diff files: {diff_files}")

    # main work
    result = tag(tags)

    # calc impacts
    for each in diff_files:
        selected_tags = result.top_n_tags(each, 3)
        logger.info(f"file {each} tags: {selected_tags}")


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


if __name__ == '__main__':
    main()
