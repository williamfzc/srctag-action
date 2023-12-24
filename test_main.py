from loguru import logger
from srctag.storage import MetadataConstant

from main import tag


def test_tag():
    fake_diff = ["main.py"]
    result = tag([], fake_diff)
    relation_graph = result.relations

    for each_file in fake_diff:
        related_nodes = list(relation_graph.neighbors(each_file))
        related_issues = [node for node in related_nodes if
                          relation_graph.nodes[node]["node_type"] == MetadataConstant.KEY_ISSUE_ID]
        related_commits = [node for node in related_nodes if
                           relation_graph.nodes[node]["node_type"] == MetadataConstant.KEY_COMMIT_SHA]
        logger.info(f"file {each_file} related to issues {len(related_issues)}, commits {len(related_commits)}")
