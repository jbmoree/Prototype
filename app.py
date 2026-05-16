
from fastapi import FastAPI
import numpy as np

app = FastAPI()

@app.get("/")
def root():
    return {"message": "hello"}

@app.get("/square")
def square(x: float, y:float):
    return {
        "x": x,
        "y": y,
        "x_squared": np.pi*x**2 + y**2
    }
  