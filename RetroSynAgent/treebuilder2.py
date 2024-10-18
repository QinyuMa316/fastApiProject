import copy
import json
from graphviz import Digraph
import time
import pubchempy
import pickle
import base64
from io import BytesIO
from PIL import Image # pip install Pillow
import os
from collections import deque

class CommonSubstanceDB:
    # def __init__(self):
    #     self.added_database = self.get_added_database()
    # @staticmethod
    # def read_data_from_json(filename):
    #     with open(filename, 'r', encoding='utf-8') as file:
    #         data = json.load(file)
    #     return data
    #
    # def get_added_database(self):
    #     polymers = [
    #         "Polyethylene",
    #         "Polypropylene",
    #         "Polystyrene",
    #         "Polyvinyl chloride",
    #         "Polyethylene terephthalate",
    #         "Polytetrafluoroethylene",
    #         "Polycarbonate",
    #         "Poly(methyl methacrylate)",
    #         "Polyurethane",
    #         "Polyamide",
    #         "Polyvinyl acetate",
    #         "Polybutadiene",
    #         "Polychloroprene",
    #         "Poly(acrylonitrile-butadiene-styrene)",
    #         "Polyoxymethylene",
    #         "Polylactic acid",
    #         "Polyethylene glycol",
    #         "Poly(vinyl alcohol)",
    #         "Polyacrylamide",
    #         "Polyethylene oxide",
    #         "Poly(ethylene-co-vinyl acetate)"
    #     ]
    #
    #     polymers = [polymer.lower() for polymer in polymers]
    #     emol_list = self.read_data_from_json('RetroSynAgent/emol.json')
    #     added_database = set(emol_list) | {"CCl2"} | set(polymers)
    #     return added_database


    def is_common_chemical(self, compound_name, max_retries=1, delay=1):
        """
        查询PubChem数据库以判断化合物是否为常用化合物，出现错误时重新查询
        :param compound_identifier: 化合物的SMILES、英文名称或其他标识符 (字符串)
        :param max_retries: 最大重试次数
        :param delay: 每次重试之间的等待时间（秒）
        :return: 如果找到相关记录则返回True，否则返回False
        """
        init_reactants = {'a', 'b', 'f'}
        if compound_name in init_reactants:
            return True
        return False
    #
    #     compound_identifier = self.get_smiles_from_name(compound_name)
    #     retries = 0
    #     while retries < max_retries:
    #         try:
    #             if compound_identifier in self.added_database:
    #                 print(f"{compound_identifier} query success")
    #                 return True
    #             # 通过SMILES查询化合物
    #             compound = pubchempy.get_compounds(compound_identifier, 'smiles')
    #             if not compound:
    #                 # 如果SMILES查询失败，则尝试通过名称查询
    #                 compound = pubchempy.get_compounds(compound_identifier, 'name')
    #             if compound:
    #                 print(f"{compound_identifier} query succeed")
    #                 return True
    #             return False
    #         except pubchempy.PubChemHTTPError as e:
    #             # print(f"{compound_identifier} 查询失败: {e}. 正在重试... ({retries + 1}/{max_retries})")
    #             retries += 1
    #             time.sleep(delay)
    #         except Exception as e:
    #             print(f"other error: {e}")
    #             # 其他错误: <urlopen error [Errno 54] Connection reset by peer>
    #     print(f"{compound_identifier} query failed") # 已达到最大重试次数
    #     return False
    #
    # @staticmethod
    # def get_smiles_from_name(compound_name):
    #     compounds = pubchempy.get_compounds(compound_name, 'name')
    #     if compounds:
    #         return compounds[0].canonical_smiles
    #     else:
    #         return compound_name

class Node:
    def __init__(self, substance, reactions, product_dict,
                 fathers_set=None, father=None, reaction_index=None,
                 reaction_line=None, cache_func=None, unexpandable_substances=None): # , visited_substances=None):
        '''
        reaction_index 通过第几个反应得到：idx(str)
        subtance 当前节点的名称：name(str)
        children 孩子节点列表：[Node, ...]
        fathers_set 父节点名称集合：set( name(str), name(str) )
        reaction_line 反应路径：[idx(str), ...]
        brothers 兄弟节点：[None, ...]
        '''
        self.reaction_index = reaction_index
        self.substance = substance
        self.children = []
        self.fathers_set = fathers_set if fathers_set is not None else set()
        self.father = father # father_node
        self.reaction_line = reaction_line if reaction_line is not None else []
        self.is_leaf = False
        self.cache_func = cache_func  # 添加缓存函数
        self.reactions = reactions
        self.product_dict = product_dict
        self.unexpandable_substances = unexpandable_substances
        # self.visited_substances = visited_substances

    def add_child(self, substance:str, reaction_index:int):
        '''
        为当前节点self添加孩子节点self.children
        child
        当前孩子节点child的名称：substance
        当前孩子child的父节点集合：curr_child_fathers_set = 当前节点（当前孩子节点的父节点）self + 当前节点的父节点集合
        当前孩子child的反应路线：curr_child_raction_line = 当前节点->当前孩子节点 的 idx + 当前节点的反应路线
        '''
        curr_child_fathers_set = copy.deepcopy(self.fathers_set)
        curr_child_fathers_set.add(self.substance)
        curr_child_reaction_line = copy.deepcopy(self.reaction_line) + [reaction_index]
        child = Node(substance, self.reactions, self.product_dict,
                     fathers_set=curr_child_fathers_set,
                     father = self,
                     reaction_index=reaction_index,
                     reaction_line=curr_child_reaction_line,
                     cache_func=self.cache_func,
                     unexpandable_substances=self.unexpandable_substances,
                     # visited_substances = self.visited_substances
                     )  # 传递缓存函数
        self.children.append(child)
        return child

    def remove_child_by_reaction(self, reaction_index:int):
        """
        和祖先节点重名（形成loop），删除该reactions
        不仅要删除当前孩子节点，还要删除和当前孩子节点相同反应的节点；即要删除亲兄弟（reaction idx相同）
        """
        self.children = [child for child in self.children if child.reaction_index != reaction_index]

    def expand(self)->bool:
        """
        reactions {'idx': {'reactants':[], 'products':[], conditions: ''}, ...}
        product_dict {'product': [idx1, idx2, ...], ...}
        """
        # # 如果该物质已经被访问过，直接返回之前的结果
        # if self.substance in self.visited_substances:
        #     return self.visited_substances[self.substance]

        # 基线条件：
        # 【1】反应物已经属于已有反应物中，不需要再展开
        # if self.substance in init_reactants:
        if self.cache_func(self.substance):
            self.is_leaf = True
            # self.visited_substances[self.substance] = True
            # print(f"{self.substance} is accessible")
            return True
        else:
            reactions_idxs = self.product_dict.get(self.substance, [])
            # 【2】该物质无法通过现有反应获得
            if len(reactions_idxs) == 0:
                self.unexpandable_substances.add(self.substance)
                # self.visited_substances[self.substance] = False
                # print(f"{self.substance} cannot be expanded further")
                return False
            # 【3】该物质不属于已有反应物，但可以通过现有反应获得
            else:
                # 遍历所有可以生成该物质的反应
                for reaction_idx in reactions_idxs:
                    # 获取生成该物质反应的反应物，逐一进行遍历，添加为当前节点的孩子节点
                    reactants_list = self.reactions[reaction_idx]['reactants'] # ['reactions'][0]
                    # 生成当前节点物质，的所有反应物
                    for reactant in reactants_list:
                        # 1 === self.add_child包含：创建当前孩子节点并添加为当前self.children.append(child)
                        child = self.add_child(reactant, reaction_idx)
                        # 2 === 判断当前添加的孩子节点是否合法
                        # （1）当前孩子节点和祖先节点重名（形成loop）则不合法
                        # （self.remove_child_by_reaction不仅要删除当前孩子节点，还要删除和当前孩子节点相同反应reaction_idx的节点）
                        if child.substance in child.fathers_set:
                            self.remove_child_by_reaction(reaction_idx)
                            break
                        # （2）当前孩子节点无法进一步展开（1无法展开成初始反应物 2无法通过现有反应获得）
                        # （self.remove_child_by_reaction不仅要删除当前孩子节点，还要删除和当前孩子节点相同反应reaction_idx的节点）
                        # 对当前孩子进一步进行展开（递归），判断能否展开
                        is_valid = child.expand() #, init_reactants)
                        # 无法进行展开
                        if not is_valid:
                            self.remove_child_by_reaction(reaction_idx)
                            break
                # 遍历所有可以生成该物质的反应，经过检查，「1」孩子均非法（没有合法子节点）无法合成这个物质
                if len(self.children) == 0:
                    # self.visited_substances[self.substance] = False
                    return False
                # 遍历所有可以生成该物质的反应，经过检查，「2」存在合法子节点，当前节点可以展开
                else:
                    # self.visited_substances[self.substance] = True
                    return True

# 物质树，包含所有物质节点
class Tree:
    def __init__(self, target_substance, result_dict=None, reactions_txt=None):
        """
        reactions_dict[str(idx)] = {
            'reactants': tuple(reactants),
            'products': tuple(products),
            'conditions': conditions, }
        """
        if result_dict:
            self.reactions, self.reactions_txt = self.parse_results(result_dict)
        elif reactions_txt:
            self.reactions = self.parse_reactions_txt(reactions_txt)
        # self.reactions = self.parse_reactions(reactions_txt)
        self.product_dict = self.get_product_dict(self.reactions)
        self.target_substance = target_substance
        # self.root = Node(target_substance)
        self.reaction_infos = set()
        self.all_path = []
        self.chemical_cache = self.load_dict_from_json()  # 用于记录物质在数据库中能否查询到
        self.unexpandable_substances = set()  # 记录无法展开的节点的集合
        # self.visited_substances = {}  # 记录访问过的物质及其展开结果
        # 创建根节点，并传递缓存查询方法，并传递记录无法展开的节点的集合
        self.root = Node(target_substance, self.reactions, self.product_dict,
                         cache_func=self.is_common_chemical_cached,
                         unexpandable_substances=self.unexpandable_substances,
                         # visited_substances = self.visited_substances
                         )
    def get_product_dict(self, reactions_dict):
        '''
        reactions_dict[str(idx)] = {
            'reactants': tuple(reactants),
            'products': tuple(products),
            'conditions': conditions,
        }
        '''
        product_dict = {}
        # 遍历 reactions_entry 字典
        for idx, entry in reactions_dict.items():
            products = entry['products']
            # 遍历产物
            for product in products:
                product = product.strip()
                if product not in product_dict:
                    product_dict[product] = []
                product_dict[product].append(idx)

        for key, value in product_dict.items():
            product_dict[key] = tuple(value)
        return product_dict

    # def parse_reactions_txt(self, reactions_txt):
    #     # idx = 1
    #     # todo: v13 添加解析reaction_txt中Conditions & 保留原始 Reactions idx而不是重新标注
    #     # todo: v15 优化保存词条方法
    #     reactants = []
    #     products = []
    #     reactions_dict = {}
    #     lines = reactions_txt.splitlines()
    #     for line in lines:
    #         line = line.strip()
    #         if line.startswith('Reaction idx:'):
    #             idx = line.split("Reaction idx:")[1].strip()
    #         elif line.startswith("Reactants:"):
    #             reactants = line.split("Reactants:")[1].strip().split(', ')
    #             reactants = [reactant.lower() for reactant in reactants]
    #         elif line.startswith("Products:"):
    #             products = line.split("Products:")[1].strip().split(', ')
    #             products = [product.lower() for product in products]
    #         elif line.startswith("Conditions:"):
    #             conditions = line.split("Conditions:")[1].strip()
    #         elif line.startswith("Source:"):
    #             source = line.split("Source:")[1].strip()
    #             # reactions_dict[str(idx)] = {
    #             #     'reactants': tuple(reactants),
    #             #     'products': tuple(products),
    #             #     'conditions': conditions,
    #             #     'source': source,
    #             # }
    #             # idx += 1
    #         elif line == '':
    #             reactions_dict[str(idx)] = {
    #                 'reactants': tuple(reactants),
    #                 'products': tuple(products),
    #                 'conditions': conditions if 'conditions' in locals() else '',
    #                 'source': source if 'source' in locals() else '',
    #             }
    #     return reactions_dict

    def parse_reactions_txt(self, reactions_txt):
        reactants = []
        products = []
        reactions_dict = {}
        idx = None  # 用于在每次找到新的Reaction idx时更新
        conditions = ""
        source = ""
        lines = reactions_txt.splitlines()

        for line in lines:
            line = line.strip()

            if line.startswith('Reaction idx:'):
                # 保存前一个反应条目（如果存在）
                if idx is not None:
                    reactions_dict[str(idx)] = {
                        'reactants': tuple(reactants),
                        'products': tuple(products),
                        'conditions': conditions,
                        'source': source,
                    }
                # 重置变量并解析新的Reaction idx
                idx = line.split("Reaction idx:")[1].strip()
                reactants = []
                products = []
                conditions = ""
                source = ""

            elif line.startswith("Reactants:"):
                reactants = line.split("Reactants:")[1].strip().split(', ')
                reactants = [reactant.lower() for reactant in reactants]

            elif line.startswith("Products:"):
                products = line.split("Products:")[1].strip().split(', ')
                products = [product.lower() for product in products]

            elif line.startswith("Conditions:"):
                conditions = line.split("Conditions:")[1].strip()

            elif line.startswith("Source:"):
                source = line.split("Source:")[1].strip()

            # 不需要在这里检查空行，直接在循环外添加最后一个反应

        # 添加最后一个反应条目（如果存在）
        if idx is not None:
            reactions_dict[str(idx)] = {
                'reactants': tuple(reactants),
                'products': tuple(products),
                'conditions': conditions,
                'source': source,
            }
        return reactions_dict

    def parse_reactions(self, reactions_txt, idx, pdf_name):
        # idx = 1
        reactants = []
        products = []
        reactions_dict = {}
        lines = reactions_txt.splitlines()
        for line in lines:
            line = line.strip()
            if line.startswith("Reactants:"):
                reactants = line.split("Reactants:")[1].strip().split(', ')
                reactants = [reactant.lower() for reactant in reactants]
            elif line.startswith("Products:"):
                products = line.split("Products:")[1].strip().split(', ')
                products = [product.lower() for product in products]
            elif line.startswith("Conditions:"):
                conditions = line.split("Conditions:")[1].strip()
                reactions_dict[str(idx)] = {
                    'reactants': tuple(reactants),
                    'products': tuple(products),
                    'conditions': conditions,
                    'source': pdf_name,
                }
                idx += 1
        return reactions_dict, idx

    def parse_results(self, result_dict):
        """
        result_dict : gpt_results_40.json
        """
        reactions_txt_all = ''
        reactions = {}
        idx = 1
        for pdf_name, (reaction, property) in result_dict.items():
            reactions_txt_all += (reaction + '\n\n')
            additional_reactions, idx = self.parse_reactions(reaction, idx, pdf_name)
            reactions.update(additional_reactions)
        return reactions, reactions_txt_all


    def save_dict_as_json(self, dict_file, filename="substance_query_result_40.json"):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(dict_file, f, ensure_ascii=False, indent=4)

    def load_dict_from_json(self, filename="substance_query_result_40.json"):
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                dict_file = json.load(f)
                return dict_file
        else:
            return {}

    def is_common_chemical_cached(self, compound_name):
        """使用缓存来避免重复查询化合物"""
        if compound_name in self.chemical_cache:
            return self.chemical_cache[compound_name]
        db = CommonSubstanceDB()
        result = db.is_common_chemical(compound_name)
        self.chemical_cache[compound_name] = result
        self.save_dict_as_json(self.chemical_cache)
        return result

    def construct_tree(self): # , init_reactants):
        # global init_reactants
        # if self.root.substance in init_reactants:
        #     raise ValueError("Target substance is already in initial reactants.")

        if self.is_common_chemical_cached(self.root.substance):
            raise ValueError("Target substance is easily gotten.")
            # return ("Target substance is easily gotten.")
        result = self.root.expand() #, init_reactants)
        if result:
            return True # "Build tree successfully!"
        else:
            return False # "Failed to build tree."

    def get_name(self, node):
        # 如果是根节点
        if node.reaction_index is None:
            return node.substance
        else:
            depth = str(len(node.fathers_set))
            # '.'.join(map(str, list(node.reaction_line))) 反应来源所有idx以.相连
            return (depth+ "-" + node.substance+ "-" + '.'.join(map(str, list(node.reaction_line))))

    def add_nodes_edges(self, node, dot=None, simple = False):
        # 根节点
        if dot is None:
            if len(node.children) == 0:
                raise Exception("Empty tree!")
            # dot = Digraph(comment='Substances Tree', graph_attr={'rankdir': 'LR', 'dpi': '1000'})
            dot = Digraph(comment='Substances Tree', graph_attr={'rankdir': 'LR', 'dpi': '1000', 'splines': 'true'})

            # lightblue2
            dot.attr('node', shape='ellipse', style='filled', color='lightblue2', fontname="Arial", fontsize="8")
            dot.attr('edge', color='gray', fontname="Arial", fontsize="8")
            if simple:
                dot.node(name=self.get_name(node), label='', width='0.1', height='0.1')
            else:
                dot.node(name=self.get_name(node), label=node.substance)

        for child in node.children:
            if simple:
                dot.node(name=self.get_name(child), label='', width='0.1', height='0.1')
                dot.edge(self.get_name(node), self.get_name(child), label='', arrowhead='none')
            else:
                dot.node(name=self.get_name(child), label=child.substance, width='0.1', height='0.1')
                dot.edge(self.get_name(node), self.get_name(child), label=f"idx : {str(child.reaction_index)}", arrowhead='none')

            dot = self.add_nodes_edges(child, dot=dot, simple=simple)
            # reaction_info = f"reaction idx: {str(child.reaction_index)}, conditions: {self.reactions[child.reaction_index]['conditions']}"
            reaction_info = str(child.reaction_index)
            self.reaction_infos.add(reaction_info)
        return dot

    def get_name_level_order(self, node):
        if node.reaction_index is None:
            return node.substance
        else:
            depth = str(len(node.fathers_set))
            # todo: v13 return f"{depth}-{node.substance}" -> f"{depth}-{node.substance}-{node.father.node}"
            return f"{depth}-{node.substance}-{node.father.substance}"

    def add_nodes_edges_level_order2(self, node, dot=None, simple=False):
        # todo: v11
        #  if node.is_leaf == True 则修改颜色为浅绿色
        #  两个相同节点之间的边如果idx不同则进行连接【两节点之间有多条边（idx不同）】 - 修改为 -> 边上除去idx信息，若存在第二条边则不添加【两节点之间只存在一条边，且图中不显示idx】
        # 根节点
        if dot is None:
            if len(node.children) == 0:
                raise Exception("Empty tree!")
            dot = Digraph(comment='Substances Tree', graph_attr={'rankdir': 'LR'})
            dot.attr(overlap='false', splines='false', ranksep='0.5', nodesep='1')
            dot.attr('node', shape='ellipse', style='filled', fillcolor='#82b0d2', color='#999999', fontname="Arial", fontsize="8")
            dot.attr('edge', color='#999999', fontname="Arial", fontsize="8")
            root_fillcolor = '#beb8dc' # 紫色
            dot.node(name=self.get_name_level_order(node), label='' if simple else node.substance, width='0.1', height='0.1', fillcolor=root_fillcolor)

        queue = deque([node])
        while queue:
            level_nodes = []
            level_edges = []
            for _ in range(len(queue)):
                cur_node = queue.popleft()
                if cur_node.reaction_index is not None:
                    edge_name = (self.get_name_level_order(cur_node.father) + self.get_name_level_order(cur_node))
                    # 遍历每层节点，如果未添加则添加
                    if edge_name not in level_edges:
                        # label=f"idx : {str(cur_node.reaction_index)}"
                        dot.edge(self.get_name_level_order(cur_node.father), self.get_name_level_order(cur_node), label=f"", arrowhead='none')
                        level_edges.append(edge_name)

                        reaction_info = str(cur_node.reaction_index)
                        self.reaction_infos.add(reaction_info)

                    # 判断当前节点是否为叶子节点
                    node_name = cur_node.substance
                    node_color = '#8ecfc9' if cur_node.is_leaf else '#82b0d2'  # 根据条件设定颜色
                    if node_name not in level_nodes:
                        dot.node(name=self.get_name_level_order(cur_node), label='' if simple else cur_node.substance, width='0.1', height='0.1', fillcolor=node_color)
                        level_nodes.append(node_name)

                for child in cur_node.children:
                    queue.append(child)
        return dot

    def get_reactions_in_tree(self, reaction_idx_list):
        reactions_tree = ''
        for idx in reaction_idx_list:
            reactants = self.reactions[idx]['reactants']
            products = self.reactions[idx]['products']
            conditions = self.reactions[idx]['conditions']
            source = self.reactions[idx]['source']
            reaction_string = (f"Reaction idx: {idx}\nReactants: {', '.join(reactants)}\nProducts: {', '.join(products)}\n"
                               f"Conditions: {conditions}\nSource: {source}\n\n")
            reactions_tree += reaction_string
        return reactions_tree


    def show_tree(self, view=False, simple=False, dpi='500', img_suffix = ''):
        """
        在Graphviz中，
        [dot.node]  节点的默认宽度和高度通常是：宽度 (width)：0.75，高度 (height)：0.5
                    color属性设置节点边框的颜色。fillcolor属性设置节点填充颜色。
        [dot.edge]  arrowhead = normal：默认样式，vee：V形，dot：点状，none：无箭头
                    style = 'solid' 直线
        dot.attr(splines='true')    根据布局自动生成曲线连接
        """
        # if full:
        #     dot = self.add_nodes_edges(self.root, simple=simple)
        #     dot.attr(dpi=dpi)
        #     dot.render(filename=str(self.target_substance) + '_full' + img_suffix, format='png', view=view)
        #     # tree_base64_image = self.png_to_base64(str(self.target_substance) + img_suffix + '_full.png')
        # else:
        # todo: v11
        dot = self.add_nodes_edges_level_order2(self.root, simple=simple)
        dot.attr(dpi=dpi)
        dot.render(filename=str(self.target_substance) + img_suffix, format='png', view=view)
        # tree_base64_image = self.png_to_base64(str(self.target_substance) + img_suffix + '.png')

        # dot.render('substances_tree', format='svg', view=True)

        # 根据树中涉及的idx从all_reactions_txt中提取出相关的反应
        # reactions_tree: all reactions(idx, reactants, products, conditions) in the tree
        reaction_idx_list = list(self.reaction_infos)
        reactions_tree = self.get_reactions_in_tree(reaction_idx_list)
        return reactions_tree #, tree_base64_image


    def png_to_base64(self, png_path):
        # 打开PNG图像文件
        with Image.open(png_path) as image:
            # 创建字节流对象
            buffered = BytesIO()
            # 将图像保存到字节流中，以PNG格式
            image.save(buffered, format="PNG")
            # 获取字节流的二进制内容并编码为Base64
            base64_image = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return base64_image

    def find_all_paths(self):
        """
        class Node:
        def __init__(self, substance, fathers_set=None, reaction_index=None, reaction_line=None):
        # reaction_index 通过第几个反应得到：idx(str)
        # subtance 当前节点的名称：name(str)
        # children 孩子节点列表：[Node, ...]
        # fathers_set 父节点名称集合：set( name(str), name(str) )
        # reaction_line 反应路径：[idx(str), ...]
        # brothers 兄弟节点：[None, ...]
        self.reaction_index = reaction_index
        self.substance = substance
        self.children = []
        self.fathers_set = fathers_set if fathers_set is not None else set()
        self.reaction_line = reaction_line if reaction_line is not None else []
        """
        # v2
        path = self.dfs_v2(self.root)
        path = self.clean_path(path)
        path = self.remove_supersets(path)
        return path

    def dfs_v2(self, node):
        # 后序遍历
        # 终止条件：当该节点为叶子节点时
        if node.is_leaf:
            return []
        # 处理叶子节点
        # 先按照反应归并反应路径
        reaction_paths = {}
        for child in node.children:
            paths = self.dfs_v2(child)
            reaction_idx = child.reaction_index
            # 如果该序号反应字典不存在，或者长度为0，直接覆盖
            if reaction_idx not in reaction_paths or len(reaction_paths[reaction_idx]) == 0:
                reaction_paths[reaction_idx] = paths
            elif len(paths) == 0:
                continue
            else:
                # 现有需要的反应
                cur_paths = reaction_paths[reaction_idx]
                # 置空
                reaction_paths[reaction_idx] = []
                # 组合
                for cur_path in cur_paths:
                    for child_path in paths:
                        reaction_paths[reaction_idx].append(cur_path + child_path)
        # 处理中节点：把reaction_paths的字典不同的键加起来
        ret = []
        for reaction_idx, paths in reaction_paths.items():
            if len(paths) == 0:
                paths.append([])
            for path in paths:
                ret.append([reaction_idx] + path)
        return ret

    def clean_path(self, all_path):
        # 去重函数
        def remove_duplicates(lst):
            seen = set()
            return [x for x in lst if x not in seen and not seen.add(x)]

        # 对每个子列表进行去重
        result = [remove_duplicates(sublist) for sublist in all_path]
        return result

    def remove_supersets(self, data):
        """
            去除更大的包含子集的集合，保留较小的子集
            :param data: List of lists, 原始数据
            :return: 去除包含其他集合的较大集合后的结果列表
            """
        # 转换为集合列表，便于判断子集关系
        data_sets = [set(sublist) for sublist in data]

        # 结果列表，用于存放保留的子集
        result = []

        # 遍历所有的集合
        for i, current_set in enumerate(data_sets):
            # 判断当前集合是否为其他任何集合的超集
            is_superset = False
            for j, other_set in enumerate(data_sets):
                if i != j and current_set.issuperset(other_set):
                    is_superset = True
                    break
            # 如果当前集合不是其他集合的超集，则保留
            if not is_superset:
                result.append(data[i])

        return result

class TreeLoader():
    def save_tree(self, tree, filename):
        with open(filename, 'wb') as f:
            pickle.dump(tree, f)
        print(f"Tree saved to {filename}")

    def load_tree(self, filename):
        with open(filename, 'rb') as f:
            tree = pickle.load(f)
        print(f"Tree loaded from {filename}")
        return tree

# if __name__ == '__main__':
#     reactions_txt = ''
#     target_substance = "poly(4-hydroxystyrene)"
#     tree = Tree(target_substance.lower(), reactions_txt)
#     result = tree.construct_tree()

    '''
    version declaration:
    v2: 添加字典，保存查询过的结果
    v3: 删除全局变量product_dict和reactions，作为类属性进行传参
    v4: show tree，用层序遍历，省略重复分支
    v5：输出并保存化合物查询（成功）失败信息（如果可以延伸出去则不记录）
    v6: add def get_reactions_in_tree
    v7: product_dict通过传入的reactions进行转换，即添加def get_product_dict(self, reactions_dict)
    v7: reactions通过传入的reactions_txt进行转换，即添加def parse_reactions(self, reactions_txt)
    v8: 返回树创建成功or失败的信息
    v9: reactions添加idx对应的文献来源, 改成tree输入为gpt_results.json -> dict, 
        添加def parse_reactions(self, reactions_txt, idx, pdf_name):并修改def parse_reactions(self, reactions_txt, idx, pdf_name):
    v10: fix full tree bug del visited_substances & 添加点线图
    v11: def add_nodes_edges_level_order2 两个节点之间多条边改成显示一条边 & 节点和边根据不同的性质绘制不同的颜色（is_leaf true green, false blue）
    v12：dfs -> dfs_v2进行路径搜索
    v13: def parse_reactions_txt(self, reactions_txt): 添加解析reaction_txt中Conditions & 保留原始 Reactions idx而不是重新标注
        todo: 在指定路径上节点和边均变为红色
    '''
