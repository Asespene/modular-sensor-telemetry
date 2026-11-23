from fastapi import FastAPI, HTTPException, Request

from fastapi.responses import JSONResponse


from enum import StrEnum

last_item = None

app = FastAPI()

class ModelName(StrEnum):
    alexnet = "alexnet"
    resnet = "resnet"
    lenet = "lenet"

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id", item_id}

@app.get("/models/{model_name}")
async def getModel(model_name: ModelName):
    if (model_name is ModelName.alexnet):
        return {"model_name", model_name}
    elif (model_name is ModelName.lenet):
        return {"model_name", model_name}
    else:
        #this should do the resnet model
        return {"model_name", model_name}

@app.get("/health")
async def returnStatus():
    return {"status": "ok"}

@app.get("/devices/{device_id}/sensors/{sensor_id}")
async def validDIoT(device_id: str, sensor_id: str):
    if (device_id != "node-01"):
        raise HTTPException(status_code=404, detail="Device not found")
    else:
        return {"device_id": device_id, "sensor_id": sensor_id}



@app.post("/echo")
async def echo(request: Request):
    global last_item
    try:
        requestBody = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "Invalid JSON"})

    last_item = requestBody

    return JSONResponse(status_code=201, content={"received": requestBody})

@app.get("/echo/latest")
async def retrieveTemp():
    if (last_item is None):
        raise HTTPException(status_code=404, detail="last_item is None!")
    else:
        return last_item