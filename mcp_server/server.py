#!/usr/bin/env python3
import argparse
import json
import os
import random
import requests
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from clean_node import transform_figma_json

mcp = FastMCP("figma")


def main():
    """Entry point for the figma-mcp CLI."""
    # Load environment variables
    load_dotenv()

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Figma MCP Python Server")
    parser.add_argument(
        "--figma-api-key",
        type=str,
        help="Figma API token to use instead of environment variable",
    )
    args = parser.parse_args()

    # Use command-line argument if provided, otherwise use environment variable
    FIGMA_API_TOKEN = args.figma_api_key or os.getenv("FIGMA_API_TOKEN")
    if not FIGMA_API_TOKEN:
        print(
            "Please provide Figma API token via --figma-api-key or "
            "FIGMA_API_TOKEN environment variable."
        )
        return

    # Define helper functions
    def fetch_figma_file(file_key: str, download_file: bool = False):
        headers = {"X-Figma-Token": FIGMA_API_TOKEN}
        url = f"https://api.figma.com/v1/files/{file_key}"
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            return {"error": f"Failed to fetch Figma file: {response.status_code}"}

        figma_data = response.json()

        if download_file:
            with open(f"{file_key}.json", "w") as f:
                json.dump(figma_data, f, indent=2)

        return figma_data

    def extract_prototype_connections(figma_data):
        connections = []

        def traverse_nodes(node):
            if "children" in node:
                for child in node.get("children", []):
                    if "transitionNodeID" in child and child.get("transitionNodeID"):
                        connections.append(
                            {
                                "sourceNodeID": child.get("id"),
                                "sourceNodeName": child.get("name", "Unnamed"),
                                "targetNodeID": child.get("transitionNodeID"),
                                "interaction": child.get("transitionDuration", 0),
                            }
                        )
                    traverse_nodes(child)

        # Start traversal from the document
        if "document" in figma_data:
            traverse_nodes(figma_data["document"])

        return connections

    def fetch_figma_nodes(file_key: str, node_ids: str):
        headers = {"X-Figma-Token": FIGMA_API_TOKEN}
        url = f"https://api.figma.com/v1/files/{file_key}/nodes?ids={node_ids}"
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            return {"error": f"Failed to fetch Figma nodes: {response.status_code}"}

        return response.json()

    # Register MCP tools
    @mcp.tool()
    def get_components(file_key: str) -> list[dict]:
        """Get components available in a Figma file

        Args:
            file_key (str): The file key found in the shared Figma URL

        Returns:
            list[dict]: List of components found in the Figma file
        """
        figma_data = fetch_figma_file(file_key)
        if "error" in figma_data:
            return [{"error": figma_data["error"]}]

        components = []
        for component_id, component_data in figma_data.get("components", {}).items():
            components.append(
                {
                    "id": component_id,
                    "name": component_data.get("name", "Unnamed Component"),
                    "description": component_data.get("description", ""),
                }
            )

        return components

    @mcp.tool()
    def get_node(file_key: str, node_id: str) -> dict:
        """Get a specific node from a Figma file

        Args:
            file_key (str): The file key from the Figma URL.
                            (e.g., from .../file/FILE_KEY/...)
            node_id (str): The ID of the node (e.g., '0:3' or '0-3').

        Returns:
            dict: The transformed node data or an error dict.
        """
        # Convert node_id format if needed (from 0-3 to 0:3)
        if "-" in node_id and ":" not in node_id:
            node_id = node_id.replace("-", ":")

        response = fetch_figma_nodes(file_key, node_id)
        if "error" in response:
            return {"error": response["error"]}

        # Find the node in the response
        def find_node_by_id(data, target_id):
            if isinstance(data, dict):
                if data.get("id") == target_id:
                    return transform_figma_json(data)

                for key, value in data.items():
                    result = find_node_by_id(value, target_id)
                    if result:
                        return result

            elif isinstance(data, list):
                for item in data:
                    result = find_node_by_id(item, target_id)
                    if result:
                        return result

            return None

        # Look for the node in the nodes data
        for node_key, node_data in response.get("nodes", {}).items():
            if node_data.get("document"):
                node = find_node_by_id(node_data["document"], node_id)
                if node:
                    return node

        return {}

    @mcp.tool()
    def get_workflow(file_key: str) -> list[dict]:
        """Get workflows (prototype connections) available in a Figma file

        Args:
            file_key (str): The file key from the Figma URL.
                            (e.g., from .../file/FILE_KEY/...)

        Returns:
            list[dict]: List of workflow connections or an error list.
        """
        figma_data = fetch_figma_file(file_key)
        if "error" in figma_data:
            return [{"error": figma_data["error"]}]

        connections = extract_prototype_connections(figma_data)
        return connections

    @mcp.tool()
    def generate_random_number() -> int:
        """Generate a random number

        Returns:
            int: A random number
        """
        return random.randint(0, 100)

    # Start the MCP server
    print("Starting Figma MCP server...")
    mcp.run()


if __name__ == "__main__":
    main()
