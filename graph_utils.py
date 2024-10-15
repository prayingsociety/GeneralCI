import numpy as np
import random
from math import comb


def graph_complexity_count(matrix):
    row, col = matrix.shape
    node_n = row
    node_indegree = np.sum(matrix, axis=0, dtype=int)
    node_outdegree = np.sum(matrix, axis=1, dtype=int)
    indegree_avg = np.sum(node_indegree, dtype=int) / node_n

    chain_n, fork_n, collider_n = 0, 0, 0
    for i in range(row):
        chain_n += node_indegree[i] * node_outdegree[i]
        fork_n += comb(node_outdegree[i], 2)
        collider_n += comb(node_indegree[i], 2)

    return node_n, indegree_avg, chain_n, fork_n, collider_n


def dag_gen(graph_shape, p, iter_n): # i.e. graph_shape = [4, 3, 5, 3, 4]
    node_n = np.sum(graph_shape)
    matrix = np.zeros((node_n, node_n))
    node_list = list(range(node_n))
    node_tier = []
    tier_n = len(graph_shape)  # must bigger than 3
    idx_tmp = 0
    for i in graph_shape:
        node_tier.append(node_list[idx_tmp:idx_tmp+i])
        idx_tmp += i

    threshold = [np.sum(p[0:i]) for i in range(1, 4)]
    for i in range(iter_n):
        for t in range(tier_n):
            for node_i in node_tier[t]:
                node_state = random.uniform(0, 1)
                if node_state < threshold[2]:
                    if node_state < threshold[0]:  # chain
                        if t == 0:
                            target_tiers = random.sample(list(range(1, tier_n)), 2)
                            target_tiers.sort()
                            target_nodes = [random.sample(node_tier[i], 1)[0] for i in target_tiers]
                            matrix[node_i][target_nodes[0]] = 1
                            matrix[target_nodes[0]][target_nodes[1]] = 1
                        elif t == tier_n-1:
                            target_tiers = random.sample(list(range(0, tier_n-1)), 2)
                            target_tiers.sort()
                            target_nodes = [random.sample(node_tier[i], 1)[0] for i in target_tiers]
                            matrix[target_nodes[0]][target_nodes[1]] = 1
                            matrix[target_nodes[1]][node_i] = 1
                        else:
                            target_tiers = random.sample(list(range(0, t)), 1) + random.sample(list(range(t+1, tier_n)),
                                                                                               1)
                            target_tiers.sort()
                            target_nodes = [random.sample(node_tier[i], 1)[0] for i in target_tiers]
                            matrix[target_nodes[0]][node_i] = 1
                            matrix[node_i][target_nodes[1]] = 1

                    elif threshold[0] <= node_state < threshold[1]:  # fork
                        if t != tier_n-1:
                            target_tiers = (random.sample(list(range(t+1, tier_n)), 1)
                                            + random.sample(list(range(t+1, tier_n)), 1))
                            target_tiers.sort()
                            target_nodes = [random.sample(node_tier[i], 1)[0] for i in target_tiers]
                            matrix[node_i][target_nodes[0]] = 1
                            matrix[node_i][target_nodes[1]] = 1

                    else:  # collider
                        if t != 0:
                            target_tiers = random.sample(list(range(0, t)), 1) + random.sample(list(range(0, t)), 1)
                            target_tiers.sort()
                            target_nodes = [random.sample(node_tier[i], 1)[0] for i in target_tiers]
                            matrix[target_nodes[0]][node_i] = 1
                            matrix[target_nodes[1]][node_i] = 1

    node_n, indegree_avg, chain_n, fork_n, collider_n = graph_complexity_count(matrix)
    complexity = [node_n, indegree_avg, chain_n, fork_n, collider_n]

    return node_list, node_tier, matrix, complexity
