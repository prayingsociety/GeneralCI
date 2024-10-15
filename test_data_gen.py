import public_utils
import conf_utils
import cf_utils
import graph_utils
import pickle
import os
import sys
from settings import get_data_gen_settings
from public_utils import int2two_char_str
from datetime import datetime


output_path = "./generated_data"
(
    gs_indicator,
    graph_shape,
    graph_shape_group,
    path_iter_n,
    graph_p,
    graph_n_per_condition,
    conf_ce_d,
    cf_whatif_n,
    name_type,
) = get_data_gen_settings(int(sys.argv[1])).values()

os.makedirs(output_path + "/graph_png", exist_ok=True)
os.makedirs(output_path + "/pickle", exist_ok=True)
graph_n = len(graph_shape) * len(graph_p) * len(path_iter_n) * graph_n_per_condition
graph_count = 0
graph_png_out_path = f"{output_path}/graph_png"
pickle_out_path = {
    "graph": f"./{output_path}/pickle/graph_data_{graph_shape_group}.pkl",
    "node_name": f"./{output_path}/pickle/node_name_data_{graph_shape_group}.pkl",
    "conf": f"./{output_path}/pickle/conf_query_data_{graph_shape_group}.pkl",
    "cf": f"./{output_path}/pickle/cf_query_data_{graph_shape_group}.pkl",
}
fp_out_graph = open(pickle_out_path["graph"], "wb")
fp_out_name = open(pickle_out_path["node_name"], "wb")
fp_out_conf = open(pickle_out_path["conf"], "wb")
fp_out_cf = open(pickle_out_path["cf"], "wb")

for g_s in graph_shape:
    for g_p in graph_p:
        for p_itn in path_iter_n:
            for g_n in range(graph_n_per_condition):
                print(
                    datetime.now(), f"Process [{graph_count}/{graph_n-1}]", flush=True
                )
                graph_count += 1

                # gid is 8 digits
                gid = f"{gs_indicator}{graph_shape.index(g_s)}{int2two_char_str(graph_p.index(g_p))}{int2two_char_str(path_iter_n.index(p_itn))}{int2two_char_str(g_n)}"
                node_list, node_tier, matrix, complexity = graph_utils.dag_gen(
                    g_s, g_p, p_itn
                )
                public_utils.draw_graph(
                    matrix, node_list, f"{graph_png_out_path}/{gid}"
                )
                graph_item = {
                    "gid": gid,
                    "mat": matrix,
                    "node_tier": node_tier,
                    "node_n": complexity[0],
                    "in_degree_avg": complexity[1],
                    "chain_n": complexity[2],
                    "fork_n": complexity[3],
                    "collider_n": complexity[4],
                }
                pickle.dump(graph_item, fp_out_graph)

                node_name_s = public_utils.node_name_gen_specific(node_list)
                node_name = []
                for n_t in name_type:
                    n, n_c = public_utils.node_name_gen(node_name_s, n_t)
                    node_name.append([n, n_c])
                name_item = {
                    "gid": gid,
                    "specific": node_name_s,
                    "bio": node_name[0][0],
                    "bio_c": node_name[0][1],
                    "che": node_name[1][0],
                    "che_c": node_name[1][1],
                    "eco": node_name[2][0],
                    "eco_c": node_name[2][1],
                    "phy": node_name[3][0],
                    "phy_c": node_name[3][1],
                }
                pickle.dump(name_item, fp_out_name)

                for ce_d in conf_ce_d:
                    if ce_d == 1:
                        ce_d_id = "100"
                    else:
                        ce_d_id = "0" + int2two_char_str(int(ce_d * 100))
                    conf_item_id = gid + ce_d_id  # 8 digit gid + 3 digit ce_d_id
                    conf_qa_d = conf_utils.conf_qa_gen(node_tier, matrix, ce_d)
                    id_d = {"conf_id": conf_item_id}
                    conf_query_item = {**id_d, **conf_qa_d}
                    pickle.dump(conf_query_item, fp_out_conf)

                for wi_n in cf_whatif_n:
                    cf_item_id = gid + int2two_char_str(
                        wi_n
                    )  # 8 digit gid + 2 digit wi_n
                    id_d = {"cf_id": cf_item_id}
                    cf_qa_d = cf_utils.cf_qa_gen(node_tier, matrix, wi_n)
                    cf_query_item = {**id_d, **cf_qa_d}
                    pickle.dump(cf_query_item, fp_out_cf)

fp_out_graph.close()
fp_out_name.close()
fp_out_conf.close()
fp_out_cf.close()
print(datetime.now(), "All finished.", flush=True)
