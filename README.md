# ric-aiagent

## Setup

1. **Python Requirement**: Ensure you have Python 3.13.3+ installed.
2. **Virtual Environment**:
   ```bash
   python3.13 -m venv .venv
   source .venv/bin/activate
   ```
3. **Dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install "fastapi[standard]"
   ```

## Running the Server

You can run the server using the Antigravity workflow or manually.

### Workflow
Run the following command in Antigravity:
`/run_server`

### VS Code
Open the "Run and Debug" side bar and select "Run FastAPI (Dev)". This will start the server with debugging features enabled.

### Manual
```bash
source .venv/bin/activate
fastapi dev app/main.py
```

The server will be available at http://127.0.0.1:8000.
