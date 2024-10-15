import json
import time
import sys
import pickle
from datetime import datetime
from api_request_utils import get_response


def get_extract_prompt(query_type):
    match query_type:
        case "conf_ce_path":
            extract_prompt = """The following text contains an answer to a causal path finding question. Please summarize the paths in the answer and output in format:
node1 -> node2 -> node3
node4 -> node5 -> node6 -> node7
If no path provided in the answer, please output only "None". If you can't extract, please output "Unknown". Do not output other redundant content."""
        
        case "conf_conf_ctrl":
            extract_prompt = """The following text contains an answer to a backdoor adjustment question. Please summarize the controlled factor set in the answer and output in format:
factor1, factor2, factor3
If no factor provided in the answer, please output only "None". If you can't extract, please output "Unknown". Do not output other redundant content."""
        
        case "cf_f_infer":
            extract_prompt = """The following is an answer to a inference question. Please summarize the event state in the answer and output in format:
event a, happened
event b, not happen
If you can't extract, please output "Unknown". Do not output other redundant content."""
        
        case "cf_cf_infer":
            extract_prompt = """The following is an answer to a counterfactual inference question. Please summarize the event state in the answer and output in format:
event a, will happen
event b, will not happen
If you can't extract, please output "Unknown". Do not output other redundant content."""
        
        case _:
            raise ValueError("Invalid query type.")
    return extract_prompt


def extract_answer(api_key, model, query_type, input_json_path, output_json_path):
    with open(input_json_path, 'r', encoding='utf-8') as f_in:
        lines = f_in.readlines()
    f_out = open(output_json_path, 'w', encoding='utf-8')
    retry_threshold = 3
    global_retry_threshold = retry_threshold * 20
    global_retried_cnt = 0
    current_cnt = 0
    
    for l in lines:
        res_dict = json.loads(l)
        print(datetime.now(), f"Extracting at {current_cnt} | {res_dict['query_id']}", flush=True)
        current_cnt += 1
        
        retry_cnt = 0
        backoff_time = 10
        extracted_text = "[Network Error]"
        if res_dict['response_text'] != "[Network Error]":
            input_text = get_extract_prompt(query_type) + "\n\n" + res_dict['query_text'] + "\nAnswer:\n" + res_dict['response_text']
            while retry_cnt < retry_threshold:
                try:
                    extracted_text = get_response(api_key, model, input_text)['choices'][0]['message']['content']
                    global_retried_cnt = 0
                    break
                except:
                    time.sleep(backoff_time)
                    backoff_time *= 1.5
                    retry_cnt += 1
                    global_retried_cnt += 1
        

        # print(f"======={res_dict['query_id']}=======", flush=True)
        # print(f"extracted answer:\n {extracted_text}\n", flush=True)
        res_dict['extracted_answer'] = extracted_text
        f_out.write(json.dumps(res_dict, ensure_ascii=False) + '\n')
        f_out.flush()
        if global_retried_cnt >= global_retry_threshold:
            f_out.close()
            sys.exit("Failed to connect to llm api after many retries.")
    
    f_out.close()        
    # print(datetime.now(), "Answer extraction done.", flush=True)


def validate_conf_ctrl(name_list, adj_mat, c2e_noncausal_path, extracted_answer):
    def validate_ctrl_set(ctrl_set_idx, c2e_noncausal_path):
        for path_ce_pair in c2e_noncausal_path:
            for p in path_ce_pair:
                path_ctrl_state = False
                for n_idx in range(1, len(p) - 1):
                    node_indegree = adj_mat[p[n_idx - 1]][p[n_idx]] + adj_mat[p[n_idx + 1]][p[n_idx]]
                    if node_indegree == 2:
                        if n_idx not in ctrl_set_idx:
                            path_ctrl_state = True
                            break
                    else:
                        if n_idx in ctrl_set_idx:
                            path_ctrl_state = True
                            break
                if path_ctrl_state == False:
                    return False
        return True
    
    ctrl_set_idx = []
    try:
        ctrl_set_str = [s.strip().lower() for s in extracted_answer.split(',')]
        ctrl_set_idx = [name_list.index(f) for f in ctrl_set_str]
    except:
        pass
    ctrl_state = validate_ctrl_set(ctrl_set_idx, c2e_noncausal_path)

    return ctrl_state


def validate_ce_path(name_list, c2e_path, extracted_answer):
    ans_path = extracted_answer.split('\n')
    ans_path_flat = []
    for p in ans_path:
        try:
            ans_path_flat.append([name_list.index(s.strip().lower()) for s in p.split('->')])
        except:
            pass
    
    c2e_path_flat = []
    for i in c2e_path:
        for p in i:
            c2e_path_flat.append(p)
    if sorted(ans_path_flat) == sorted(c2e_path_flat):
        result = True
    else:
        result = False

    return result


def validate_cf_tasks(name_list, query_idx, gt_assign, extracted_answer):
    state_str = [['happened', 'will happen'], ['didn\'t happen', 'not happen', 'will not happen']]

    ans_lines = extracted_answer.split('\n')
    ans_event_name, ans_event_bool = [], []
    for l in ans_lines:
        try:
            ans_event_name.append(l.split(',')[0].strip().lower())
            if l.split(',')[1].strip() in state_str[0]:
                ans_event_bool.append(True)
            elif l.split(',')[1].strip() in state_str[1]:
                ans_event_bool.append(False)
            else:
                ans_event_bool.append(None)
        except:
            pass
    
    ans_idx = []
    try:
        ans_idx = [name_list.index(n) for n in ans_event_name]
    except:
        pass
    result = True
    for i in query_idx:
        if i not in ans_idx:
            result = False
            break
    if result:
        for i in range(len(ans_idx)):
            if ans_event_bool[i] != gt_assign[ans_idx[i]]:
                result = False
                break
    
    return result


def eval_llm(query_type, graph_shape_group, name_type, data_folder, ans_ex_path, output_path):
    f_qd = open(data_folder + "/" + query_type.split("_")[0] + "_query_data_" + graph_shape_group + ".pkl", 'rb')
    f_nd = open(data_folder + "/node_name_data_" + graph_shape_group + ".pkl", 'rb')
    f_gd = open(data_folder + "/graph_data_" + graph_shape_group + ".pkl", 'rb')
    f_out = open(output_path, 'w', encoding='utf-8')

    test_counter = 0
    current_gid = ""
    graph_dict = {}
    name_dict = {}

    if query_type[0:2] == "cf":
        if name_type != "specific":
            name_type = name_type + "_c"

    with open(ans_ex_path, 'r', encoding='utf-8') as f_in:
        lines = f_in.readlines()

    if query_type[:4] == "conf":
        id_entry = "conf_id"
    else:
        id_entry = "cf_id"

    for l in lines:
        qa_dict = json.loads(l)
        qa_item_id = qa_dict['query_id']
        test_counter += 1
        required_gid = qa_item_id[:8]
        current_qid = ""
        while current_qid != qa_item_id:
            try:
                query_dict = pickle.load(f_qd)
                current_qid = query_dict[id_entry]
            except EOFError:
                sys.exit("Query data incompatible.")

        if current_gid != required_gid:
            while True:
                try:
                    graph_dict = pickle.load(f_gd)
                    name_dict = pickle.load(f_nd)
                    read_g_gid = graph_dict['gid']
                    read_n_gid = name_dict['gid']
                    if read_g_gid == read_n_gid and read_g_gid == required_gid:
                        current_gid = read_g_gid
                        break
                except EOFError:
                    sys.exit("Graph/Name data incompatible.")

        print(datetime.now(), f"evaluation process at {test_counter} | {qa_item_id}", flush=True)

        if qa_dict['extracted_answer'] == "[Network Error]":
            result = "net_err"
        elif qa_dict['extracted_answer'].strip().lower() == "unknown":
            result = "unk"
        else:
            match query_type:
                case "conf_ce_path":
                    result = validate_ce_path(name_dict[name_type], query_dict['c2e_path'], qa_dict['extracted_answer'])
                
                case "conf_conf_ctrl":
                    result = validate_conf_ctrl(name_dict[name_type], graph_dict['mat'], query_dict['c2e_noncausal_path'], qa_dict['extracted_answer'])
                
                case "cf_f_infer":
                    result = validate_cf_tasks(name_dict[name_type], query_dict['cf_query'], query_dict['f_assign'], qa_dict['extracted_answer'])
                
                case "cf_cf_infer":
                    result = validate_cf_tasks(name_dict[name_type], query_dict['cf_query'], query_dict['cf_assign'], qa_dict['extracted_answer'])

        # print(f"======={qa_item_id}=======", flush=True)
        # print(f"eval result:\n {result}\n", flush=True)
        qa_dict['result'] = result
        f_out.write(json.dumps(qa_dict, ensure_ascii=False) + '\n')
        f_out.flush()
    f_out.close()
