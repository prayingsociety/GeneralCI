import public_utils
import numpy as np


def dict2text(node_name, conf_qa_d, adj_mat):
    c_list = conf_qa_d['c_list']
    e_list = conf_qa_d['e_list']
    n_rows, n_cols = adj_mat.shape
    c_relations_line = ""
    for i in range(n_rows):
        target_nodes = adj_mat[i, :]
        target_nodes_n = np.sum(target_nodes)
        target_nodes_remain = target_nodes_n
        if target_nodes_n > 1:
            c_relations_line += node_name[i][0].upper() + node_name[i][1:] + " has a causal effect on "
            for j in range(i, n_rows):
                if adj_mat[i][j] == 1:
                    if target_nodes_remain > 2:
                        c_relations_line += node_name[j] + ", "
                    elif target_nodes_remain == 2:
                        c_relations_line += node_name[j] + " and "
                    else:
                        c_relations_line += node_name[j] + ".\n"
                    target_nodes_remain -= 1
        else:
            for j in range(i, n_rows):
                if adj_mat[i][j] == 1:
                    c_relations_line += node_name[i][0].upper() + node_name[i][1:] + " has a causal effect on " + node_name[j] + ".\n"
    c_relations_line = '\n'.join(c_relations_line.split('\n')[:-1])

    ce_query_line = "We want to estimate the causal effect of the"
    if len(c_list) > 1:
        ce_query_line += "s "
    for i in range(len(c_list)):
        ce_query_line += node_name[c_list[i]]
        if len(c_list) > 1:
            if i == len(c_list) - 2:
                ce_query_line += " and "
            elif i != len(c_list) - 1:
                ce_query_line += ", "
    ce_query_line += " on the"
    if len(e_list) > 1:
        ce_query_line += "s "
    for i in range(len(e_list)):
        ce_query_line += node_name[e_list[i]]
        if len(e_list) > 1:
            if i == len(e_list) - 2:
                ce_query_line += " and "
            elif i != len(e_list) - 1:
                ce_query_line += ", "
    ce_query_line += "."

    return c_relations_line, ce_query_line


def conf_qa_gen(node_tier, adj_mat, ce_d):
    # Define causal tier and effect tier by relative distance
    max_d = len(node_tier[1:-1])
    offset = round(max_d/2*(1-ce_d))
    c_list = node_tier[1+offset]
    if offset > max_d/2:
        e_list = node_tier[1+offset+1]
    else:
        e_list = node_tier[-2-offset]

    # Find causal paths and non-causal paths
    c2e_path = []
    c2e_noncausal_path = []
    undir_adj_mat = adj_mat + adj_mat.T
    for c in c_list:
        for e in e_list:
            c2e_path_t = public_utils.find_all_paths(adj_mat, c, e)
            c2e_path.append(c2e_path_t)
            c2e_undir_path_t = public_utils.find_all_paths(undir_adj_mat, c, e)
            c2e_undir_path_woc2e = []
            for i in c2e_undir_path_t:
                if i not in c2e_path_t:
                    c2e_undir_path_woc2e.append(i)
            c2e_noncausal_path.append(c2e_undir_path_woc2e)

    conf_qa = {'ce_d': ce_d, 'c_list': c_list, 'e_list': e_list, 'c2e_path': c2e_path, 'c2e_noncausal_path': c2e_noncausal_path}

    return conf_qa
