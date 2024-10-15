import graphviz
import random
import string
import numpy as np
import sys


# Visualize graph by graphviz
def draw_graph(matrix, node_name, file_name):
    g = graphviz.Digraph()
    row, col = matrix.shape
    for i in range(row):
        for j in range(row):
            if matrix[i][j] == 1:
                g.edge(str(node_name[i]), str(node_name[j]))
    g.render(file_name, format='png', cleanup=True)


# DFS path search
def find_all_paths(adj_matrix, start, end_node):
    def dfs(current_node, end, path):
        path.append(current_node)
        if current_node == end:
            all_paths.append(list(path))
        else:
            for neighbor, is_connected in enumerate(adj_matrix[current_node]):
                if is_connected and neighbor not in path:
                    dfs(neighbor, end, path)
        path.pop()

    all_paths = []
    dfs(start, end_node, [])

    return all_paths


def int2str(n):
    text = "var_"
    text += chr(97+n//10000)
    text += chr(97+(n % 10000)//1000)
    text += chr(97+(n % 1000)//100)
    text += chr(97+(n % 100)//10)
    text += chr(97+(n % 10)//1)

    return text


def int2str_plain(n):
    text = chr(97+n//100)
    text += chr(97+(n % 100)//10)
    text += chr(97+(n % 10)//1)

    return text


def random_str_gen(n):
    str_list = []
    for i in range(n):
        str_list.append(''.join(random.choices(string.ascii_lowercase, k=5)))

    return str_list


def node_name_gen(specific_name, name_type):
    file_path = "./name_data/" + name_type + ".txt"
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    noun, change = [], []

    for i in lines:
        words = i.split()
        noun.append(words[0])
        change.append(words[1:])

    name_candidate_n = len(noun)

    node_name = []
    node_name_c = []

    for s_n in specific_name:
        n_idx = np.random.randint(0, name_candidate_n)
        c_idx = np.random.randint(0, 2)
        name = s_n + " " + noun[n_idx]
        name_c = change[n_idx][c_idx] + " of " + s_n + " " + noun[n_idx]
        node_name.append(name)
        node_name_c.append(name_c)

    return node_name, node_name_c


def node_name_gen_specific(node_list):
    node_name_s = []

    for i in range(len(node_list)):
        specific_name = random_str_gen(1)[0] + int2str_plain(node_list[i])
        node_name_s.append(specific_name)

    return node_name_s

def int2two_char_str(n):
    if 0 <= n < 10:
        return f"0{n}"
    
    if 10 <= n < 100:
        return str(n)
    
    else:
        raise ValueError("Integer out of range.")


def get_size(obj, seen=None):
    """Recursively finds size of objects"""
    size = sys.getsizeof(obj)
    if seen is None:
        seen = set()
    obj_id = id(obj)
    if obj_id in seen:
        return 0
    # Important mark as seen *before* entering recursion to gracefully handle
    # self-referential objects
    seen.add(obj_id)
    if isinstance(obj, dict):
        size += sum([get_size(v, seen) for v in obj.values()])
        size += sum([get_size(k, seen) for k in obj.keys()])
    elif hasattr(obj, '__dict__'):
        size += get_size(obj.__dict__, seen)
    elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes, bytearray)):
        size += sum([get_size(i, seen) for i in obj])
    return size
