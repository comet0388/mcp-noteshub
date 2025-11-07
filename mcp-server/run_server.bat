@echo off
cd /d E:\mcp-noteshub\mcp-server
call ..\.venv\Scripts\activate.bat
echo.
echo Starting MCP Noteshub server...
echo ----------------------------------
uvicorn main:app
pause
