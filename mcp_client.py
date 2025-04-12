import asyncio
from openai import OpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import os
import json

server_params = StdioServerParameters(command="python", args=["./mcp_server/server.py"])


openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generate_html(response: str):
    """
    Generate HTML from the response.
    """
    prompt = f"""
    Generate HTML from the response.
    The return is a strict HTML string, containing no other content!!!
    Do not include ```html or ``` these strings
    Response: {response}
    """
    response = openai_client.chat.completions.create(
        model="gpt-4o", messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()


def llm_client(message: str):
    """
    Send a message to the LLM and return the response.
    """

    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an intelligent assistant. "
                    "You will execute tasks as prompted"
                ),
            },
            {"role": "user", "content": message},
        ],
        max_tokens=2500,
        temperature=0.2,
    )

    return response.choices[0].message.content.strip()


def get_tool_prompt(query, tools):
    tools_description = "\n".join(
        [
            f"- {tool.name}, " f"{tool.description}, " f"{tool.inputSchema} "
            for tool in tools
        ]
    )
    return (
        "You are a helpful assistant with access to these tools:\n\n"
        f"{tools_description}\n"
        "Choose the appropriate tool based on the user's question. \n"
        f"User's Question: {query}\n"
        "If no tool is needed, reply directly.\n\n"
        "IMPORTANT: When you need to use a tool, you must ONLY respond with "
        "the exact JSON object format below, nothing else:\n"
        "Keep the values in str "
        "{\n"
        '    "tool": "tool-name",\n'
        '    "arguments": {\n'
        '        "argument-name": "value"\n'
        "    }\n"
        "}\n\n"
    )


async def run(query: str):
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            # print(f"Available tools: {tools}")

            prompt = get_tool_prompt(query, tools.tools)
            llm_response = llm_client(prompt)
            print(f"LLM Response: {llm_response}")

            tool_call = json.loads(llm_response)
            result = await session.call_tool(
                tool_call["tool"], arguments=tool_call["arguments"]
            )

            if tool_call["tool"] == "get_node":
                html = generate_html(result.content[0].text)
                with open("output/file.html", "w") as f:
                    f.write(html)

            if tool_call["tool"] == "get_components":
                print(f"Components: {result.content[0].text}")
                html = generate_html(result.content[0].text)
                with open("output/components.html", "w") as f:
                    f.write(html)
            if tool_call["tool"] == "generate_random_number":
                print(f"Random number: {result.content[0].text}")


if __name__ == "__main__":
    # User input
    query = input("Enter your query: ")
    asyncio.run(run(query))
