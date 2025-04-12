# MCP Demo 🚀

A demonstration of the Model Context Protocol (MCP) implementation with Python.

## Installation 📦

Install dependencies using `uv sync`:

```bash
uv sync install
```

## Running the Application 🏃‍♀️

### Standard Mode 🖥️
```bash
python mcp_client.py
```
Then input your query when prompted.

### Debug Mode 🔍
```bash
npx @modelcontextprotocol/inspector python mcp_server/server.py
```

### SSE Mode 📡
```bash
python mcp_server/server_sse.py
```

## Configuration ⚙️

### MCP Settings 🛠️
Set the MCP endpoint to:
```
http://localhost:8000/sse
```

### Development 👨‍💻
```bash
mcp dev mcp_server/server_sse.py
```
or
```bash
python mcp_server/server_sse.py
```

## Tools and Debugging 🧰

### MCP Inspector 🔎
Access the inspector at:
```
http://127.0.0.1:6274/#tools
```

