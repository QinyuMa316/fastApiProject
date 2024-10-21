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

# 创建树结构（示例）
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

# =======


# 定义递归函数，将Tree中的节点转换为FastAPI的Node

# def convert_tree_to_fastapi_node(node):
#     # v1 孩子节点未去重
#     # 递归终止条件，如果没有子节点
#     if not node.children:
#         return Node(name=node.substance)
#     # 有子节点的情况，递归构造子节点
#     return Node(
#         name=node.substance,
#         children=[convert_tree_to_fastapi_node(child) for child in node.children]
#     )

def convert_tree_to_fastapi_node(node):
    # v2 对孩子节点进行去重
    # 递归终止条件，如果没有子节点
    if not node.children:
        return Node(name=node.substance)

    # 用于存储已处理的子节点名称，防止重复
    unique_children = []
    seen_substances = set()

    # 遍历子节点，去重并递归构造
    for child in node.children:
        if child.substance not in seen_substances:
            unique_children.append(convert_tree_to_fastapi_node(child))
            seen_substances.add(child.substance)

    # 构造当前节点并返回
    return Node(name=node.substance, children=unique_children)


# 修改create_tree函数以使用转换后的树
def create_tree_from_saved_tree(tree):
    return convert_tree_to_fastapi_node(tree.root)


material = 'Polyimide'


# 【测试用例1】
# from RetroSynAgent.treebuilder2 import TreeLoader, Tree
# with open('reactions_test.txt', 'r') as file:
#     reactions_txt = file.read()
# target_substance = 'X'
# tree = Tree(target_substance.lower(), reactions_txt=reactions_txt)
# tree.construct_tree()

# 【测试用例2】
from RetroSynAgent.treebuilder import TreeLoader, Tree
tree_loader = TreeLoader()
# tree_filename = material + '.pkl'

# tree_filename = material + '_filtered.pkl'

# 【小图】
# tree_filename = material + '_wo_exp.pkl'
# 【大图】
tree_filename = material + '2.pkl'
tree = tree_loader.load_tree(tree_filename)

api_tree = create_tree_from_saved_tree(tree)

# =======


# 路由：主页
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# 路由：返回树结构的JSON
@app.get("/api/tree", response_model=Node)
async def get_tree():
    # return create_tree()
    return api_tree

