import random
import numpy as np
import public_utils


def dict2text(node_name, cf_qa_d, adj_mat):
    clue_node_name = [node_name[i] for i in cf_qa_d['cf_clue']]
    node_opt = cf_qa_d['node_opt']  # opt_str = ["not", "", "and", "or"]
    node_indegree = np.sum(adj_mat, axis=0, dtype=int)
    node_n = len(node_indegree)

    c_relation_line = ""
    for i in range(node_n):
        if np.sum(node_indegree[i]) > 0:
            node_opt_t_head = "The " + node_name[i] + " happens if "
            opt_idx = 0
            node_opt_t = ""
            for j in range(0, i):
                if adj_mat[j][i] == 1:
                    if node_opt[i][opt_idx] == 0:
                        edge_opt_t = "the " + node_name[j] + " not happen"
                    else:
                        edge_opt_t = "the " + node_name[j] + " happens"

                    node_opt_t += edge_opt_t
                    if opt_idx < len(node_opt[i])-1 and node_opt[i][opt_idx+1] == 2:
                        node_opt_t += " and "
                    else:
                        c_relation_line += node_opt_t_head + node_opt_t + ".\n"
                        node_opt_t = ""

                    opt_idx += 2
        else:
            if node_name[i] not in clue_node_name:
                c_relation_line += "The " + node_name[i] + " is bound to happen.\n"
    c_relation_line = '\n'.join(c_relation_line.split('\n')[:-1])

    clue_line = "We have observed "
    for i in range(len(clue_node_name)):
        clue_line += "the " + clue_node_name[i] + " happened"
        if len(clue_node_name) > 1:
            if i == len(clue_node_name)-2:
                clue_line += " and "
            elif i != len(clue_node_name)-1:
                clue_line += ", "
    clue_line += "."

    f_query_line = "What about the "
    cf_query_name = [node_name[i] for i in cf_qa_d['cf_query']]
    cf_query_line = "What the "
    for i in range(len(cf_query_name)):
        cf_query_line += cf_query_name[i]
        f_query_line += cf_query_name[i]
        if len(cf_query_name) > 1:
            if i == len(cf_query_name)-2:
                cf_query_line += " and "
                f_query_line += " and "
            elif i != len(cf_query_name)-1:
                cf_query_line += ", "
                f_query_line += ", "
    f_query_line += "? "
    cf_query_line += " would be "

    cf_assign_whatif = [cf_qa_d['cf_assign'][i] for i in cf_qa_d['cf_whatif']]
    whatif_node_name = [node_name[i] for i in cf_qa_d['cf_whatif']]
    whatif_line = "if "
    for i in range(len(whatif_node_name)):
        if cf_assign_whatif[i]:
            whatif_line += "the " + whatif_node_name[i] + " happened"
        else:
            whatif_line += "the " + whatif_node_name[i] + " didn't happen"
        if len(whatif_node_name) > 1:
            if i == len(whatif_node_name)-2:
                whatif_line += " and "
            elif i != len(whatif_node_name)-1:
                whatif_line += ", "
    whatif_line += "?"

    # query_text = c_relation_line + '\n' + clue_line + f_query_line + cf_query_line + whatif_line

    return c_relation_line, clue_line, f_query_line, cf_query_line, whatif_line
    # return query_text


def get_node_opts(adj_mat):
    # Find all paths from start to end point for counterfactual inference
    # s2q_path = []
    # for o in observed_l:
    #     for q in query_l:
    #         path_per_oq = public_utils.find_all_paths(adj_mat, o, q)
    #         for p in path_per_oq:
    #             s2q_path.append(p[:-1])  # remove query nodes form the path

    # whatif_candidates = list(set([node for path in s2q_path for node in path]))
    # whatif_candidates.sort()

    # Calculate the indegree of nodes
    node_indegree = np.sum(adj_mat, axis=0, dtype=int)

    # Assign boolean operators for nodes for counterfactual inference test
    node_opt_list = []
    for i in range(len(node_indegree)):
        opt_per_n = []
        if node_indegree[i] == 0:
            opt_per_n.append(-1)

        else:
            # NOTE: 0 = not, 1 = is/eql, 2 = and, 3 = or
            edge_opt = np.random.randint(0, 2, size=node_indegree[i])
            comb_opt = np.random.randint(2, 4, size=node_indegree[i]-1)
            opt_per_n = [None]*(len(edge_opt)+len(comb_opt))
            opt_per_n[::2] = edge_opt
            opt_per_n[1::2] = comb_opt
        node_opt_list.append(opt_per_n)

    return node_opt_list


def cf_bool_assign(adj_mat, node_opt_list, whatif_node=None, fact_assign=None):
    py_code = "def cf_bool_code():\n"
    bool_expr = ""
    node_indegree = np.sum(adj_mat, axis=0, dtype=int)
    node_n = len(node_indegree)
    opt_str = ["not", "", "and", "or"]
    output_code = "\treturn ["

    for i in range(node_n):
        if node_indegree[i] == 0:
            if whatif_node is None:
                py_code += '\t' + public_utils.int2str(i) + " = True\n"
                bool_expr += public_utils.int2str(i) + " = True\n"
            else:
                if i in whatif_node:
                    cf_bool = not fact_assign[i]
                    py_code += '\t' + public_utils.int2str(i) + " = " + str(cf_bool) + "\n"
                    bool_expr += public_utils.int2str(i) + " = " + str(cf_bool) + "\n"
                else:
                    py_code += '\t' + public_utils.int2str(i) + " = True\n"
                    bool_expr += public_utils.int2str(i) + " = True\n"

        else:
            code_line = '\t' + public_utils.int2str(i) + " = "
            opt_idx = 0
            for k in range(node_n):  # Check the indegree of the node
                if adj_mat[k][i] == 1:  # If path exist
                    if opt_idx < len(node_opt_list[i])-1:
                        if node_opt_list[i][opt_idx] != 1:
                            code_line += opt_str[node_opt_list[i][opt_idx]] + " " + public_utils.int2str(k) + " "
                        else:
                            code_line += opt_str[node_opt_list[i][opt_idx]] + public_utils.int2str(k) + " "
                        code_line += opt_str[node_opt_list[i][opt_idx+1]] + " "
                        opt_idx += 2
                    else:
                        if node_opt_list[i][opt_idx] != 1:
                            code_line += opt_str[node_opt_list[i][opt_idx]] + " " + public_utils.int2str(k) + "\n"
                        else:
                            code_line += opt_str[node_opt_list[i][opt_idx]] + public_utils.int2str(k) + "\n"

            py_code += code_line
            bool_expr += code_line.split('\t')[1]

        output_code += public_utils.int2str(i)
        if i != node_n-1:
            output_code += ", "

    output_code += "]\n"
    py_code += output_code + "result = cf_bool_code()"
    global_env, local_env = {}, {}
    exec(py_code, global_env, local_env)
    bool_value = local_env['result']

    return bool_expr, bool_value


def cf_qa_gen(node_tier, adj_mat, whatif_n):  # the node number in the node_tire must be sorted
    observed_node = []
    in_degree = np.sum(adj_mat, axis=0, dtype=int)
    for i in range(len(in_degree)):
        if in_degree[i] == 0:
            observed_node.append(i)
    query_node = []
    for n in node_tier[-1]:
        if in_degree[n] != 0:
            query_node.append(n)
    whatif_candidates = []
    for t in node_tier:
        for n in t:
            if n not in query_node:
                whatif_candidates.append(n)

    node_opt = get_node_opts(adj_mat)

    if whatif_n <= len(whatif_candidates):
        whatif_node = random.sample(whatif_candidates, whatif_n)
    else:
        whatif_node = random.sample(whatif_candidates, len(whatif_candidates))

    adj_mat_cf = adj_mat.copy()
    for i in whatif_node:
        adj_mat_cf[:, i] = 0

    f_bool_expr, f_assign = cf_bool_assign(adj_mat, node_opt)
    cf_bool_expr, cf_assign = cf_bool_assign(adj_mat_cf, node_opt, whatif_node, f_assign)

    cf_qa = {'wi_n': whatif_n, 'node_opt': node_opt,  'cf_clue': observed_node, 'cf_whatif': whatif_node, 'cf_query': query_node,
             'f_bool_expr': f_bool_expr, 'f_assign': f_assign, 'cf_bool_expr': cf_bool_expr, 'cf_assign': cf_assign}

    return cf_qa
