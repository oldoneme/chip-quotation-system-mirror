import os
from fastapi import FastAPI, Query, Response
from typing import Optional

os.environ['WECOM_TOKEN'] = 'cN9bXxcD80'
os.environ['WECOM_AES_KEY'] = 'S1iZ8DxsKGpiL3b10oVpRm59FphYwKzhtdSCR18q3nl'
os.environ['WECOM_CORP_ID'] = 'ww3bf2288344490c'

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Test server"}

@app.get("/wecom/callback")
async def wecom_callback(
    msg_signature: Optional[str] = Query(None),
    timestamp: Optional[str] = Query(None),
    nonce: Optional[str] = Query(None),
    echostr: Optional[str] = Query(None)
):
    return Response(content=f"Received: msg_signature={msg_signature}, timestamp={timestamp}, nonce={nonce}, echostr={echostr}", media_type="text/plain")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)