"""
Write an HTTP server that will accept requests to start a virtual machine (VM) and to
shut it down.

Start:

    POST http://localhost:8000/vm/start

    {
        "cpu_count": 2,
        "mem_size_gb": 32,
        "image": "ubuntu-22.04"
    }

Validate that:
    - cpu_count is bigger than 0 and less than 65
    - mem_size_gb is bigger than 8 and smaller than 1025
    - image is one of "ubuntu-24.04", "debian:bookworm" or "alpine:3.20"

Return a JSON message with new VM id:
    {
        "id": "c9abe3b66fc544c78e355968119081ed"
    }

Stop:

    POST http://localhost:8000/vm/{id}/stop

Validate that {id} is a valid VM id and return a JSON message:
    {
        "id": "c9abe3b66fc544c78e355968119081ed",
        "spec": {
            "cpu_count": 2,
            "mem_size_gb": 32,
            "image": "ubuntu-22.04"
        }
    }
"""
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel, Field
from http import HTTPStatus
from typing import Literal
from uuid import uuid4
from threading import Lock

MIN_CPU_COUNT = 0
MAX_CPU_COUNT = 65
MIN_MEM_SIZE_GB = 8
MAX_MEM_SIZE_GB = 1025
IMAGES = ["ubuntu-24.04", "debian:bookworm", "alpine:3.20"]


class Vm(BaseModel):
    cpu_count: int = Field(gt=0, lt=65)
    mem_size_gb: int = Field(gt=8, lt=1025)
    image: Literal["ubuntu-24.04", "debian:bookworm", "alpine:3.20"]


lock = Lock()
vms = {}

app = FastAPI()


@app.post('/vm/start')
def vm_start(vm: Vm):
    id = uuid4().hex
    with lock:
        vms[id] = vm
    return {
        'id': id
    }


@app.post('/vm/{id}/stop')
def vm_stop(id: str) -> dict:
    with lock:
        vm = vms.pop(id, None)
    if vm is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail='vm not found')
    return {
        'id': id,
        'spec': vm.dict()
    }
