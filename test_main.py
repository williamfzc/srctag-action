from loguru import logger
from srctag.storage import MetadataConstant

from main import tag


def test_tag():
    fake_diff = ["main.py"]
    result = tag([], fake_diff)
    relation_graph = result.relations

    mermaid_code = "graph TD;\n"
    for each_file in fake_diff:
        related_nodes = list(relation_graph.neighbors(each_file))
        related_issues = [node for node in related_nodes if
                          relation_graph.nodes[node]["node_type"] == MetadataConstant.KEY_ISSUE_ID]
        related_commits = [node for node in related_nodes if
                           relation_graph.nodes[node]["node_type"] == MetadataConstant.KEY_COMMIT_SHA]
        logger.info(f"file {each_file} related to issues {len(related_issues)}, commits {len(related_commits)}")

        for each_issue in related_commits:
            mermaid_code += f'  style {each_file} fill:yellow,stroke:yellow;\n'
            mermaid_code += f'  {each_issue} --> {each_file};\n'

            # Find other files connected to the current issue and set yellow background
            other_related_files = [node for node in relation_graph.neighbors(each_issue) if
                                   node != each_file]
            for other_file in other_related_files:
                mermaid_code += f'  {each_issue} --> {other_file};\n'

    logger.info(f"relations: {mermaid_code}")