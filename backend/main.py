from fastapi import FastAPI

app = FastAPI(title="AgentProbe")


@app.get("/")
async def health():
    return {"status": "alive", "service": "agentprobe"}
