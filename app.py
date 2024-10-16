from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import List, Optional
from pydantic import BaseModel

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# 节点定义
class Node(BaseModel):
    name: str
    children: Optional[List['Node']] = None

# Node.update_forward_refs() is deprecated

# 创建树结构
def create_tree():
    return Node(name="Root", children=[
        Node(name="Child 1", children=[
            Node(name="Child 1.1"),
            Node(name="Child 1.2"),
        ]),
        Node(name="Child 2", children=[
            Node(name="Child 2.1"),
            Node(name="Child 2.2", children=[
                Node(name="Child 2.2.1")
            ])
        ])
    ])

# 路由：主页
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# 路由：返回树结构的JSON
@app.get("/api/tree", response_model=Node)
async def get_tree():
    return create_tree()