import pickle
import json
import time
import sys
from conf_utils import dict2text as conf_d2t
from cf_utils import dict2text as cf_d2t
from api_request_utils import get_response
from datetime import datetime


def query_filter(qid, gs=None, gp=None, gi=None, f_infer_history=[]):
    if gs is not None:
        if qid[0:2] not in gs:
            return False

    if gp is not None:
        if qid[2:4] not in gp:
            return False

    if gi is not None:
        if qid[4:6] not in gi:
            return False
    
    if f_infer_history:
        if qid[:8] in f_infer_history:
            return False
    return True


def get_conf_prompt(c_relation, ce_query, name_type):
    subject_name = ""
    if name_type == "bio":
        subject_name = "biological "
    elif name_type == "che":
        subject_name = "chemical "
    elif name_type == "eco":
        subject_name = "economic "
    elif name_type == "phy":
        subject_name = "physics "

    intro = f"The following text describes the assumed causal relationship between factors in a recent {subject_name}study:"
    q_find_path = "Based on the information above, please identify all the causal paths between them."
    q_conf_ctrl = "Based on the information above, please provide a set of factors that can block all backdoor paths between them."

    prompt_find_path = f"""{intro}
{c_relation} 
Question:
{ce_query}
{q_find_path}"""

    prompt_conf_ctrl = f"""{intro}
{c_relation} 
Question:
{ce_query}
{q_conf_ctrl}"""
    return prompt_find_path, prompt_conf_ctrl


def get_cf_prompt(c_relation, clue, f_query, cf_query, whatif, name_type):
    subject_name = ""
    if name_type == "bio":
        subject_name = "biological "
    elif name_type == "che":
        subject_name = "chemical "
    elif name_type == "eco":
        subject_name = "economic "
    elif name_type == "phy":
        subject_name = "physics "

    intro = f"The following text describes the assumed causal relationship between events in a recent {subject_name}study:"

    prompt_f_infer = f"""{intro}
{c_relation}
Question:
{clue}
{f_query}"""

    prompt_cf_infer = f"""{intro}
{c_relation}
Question:
{clue}
{cf_query}{whatif}"""

    return prompt_f_infer, prompt_cf_infer


def add_1_example(query_type):
    conf_cr_text = """The following text describes the assumed causal relationship between things in a recent study:
Factor A has a causal effect on factor B.
Factor B has a causal effect on factor C.
Factor D has a causal effect on factor A and factor E.
Factor C has a causal effect on factor E.
Factor F has a causal effect on factor A and factor C."""

    cf_cr_text = """The following text describes the assumed causal relationship between things in a recent study:
The change of B happens if the change of A happens.
The change of C happens if the change of B happens.
The change of D happens if the change of B happens.
The change of E happens if the change of C happens and the change of D happens."""

    if query_type == "conf_ce_path":
        q_text = """
Question:
We want to estimate the causal effect of factor A on factor C.
Based on the information above, please identify all the causal paths between them.
Answer:
factor A -> factor B -> factor C"""
        return conf_cr_text + q_text

    elif query_type == "conf_conf_ctrl":
        q_text = """
Question:
We want to estimate the causal effect of factor A on factor C.
Based on the information above, please provide a set of factors that can block all backdoor paths between them.
Answer:
factor F"""
        return conf_cr_text + q_text

    elif query_type == "cf_f_infer":
        q_text = """
Question:
We have observed the change of A happened.
What about the change of E?
Answer:
The change of E happened."""
        return cf_cr_text + q_text

    elif query_type == "cf_cf_infer":
        q_text = """
Question:
We have observed the change of A happened.
What the change of E would be if the change of C didn't happen?
Answer:
The change of E will not happen."""
        return cf_cr_text + q_text

    else:
        return None


def add_2_examples(query_type):
    conf_cr_text = """The following text describes the assumed causal relationship between things in a recent study:
Factor A has a causal effect on factor D and factor X.
Factor C has a causal effect on factor Y.
Factor D has a causal effect on factor H.
Factor E has a causal effect on factor A and factor F.
Factor F has a causal effect on factor B.
Factor G has a causal effect on factor C and factor H.
Factor X has a causal effect on factor B.
Factor Y has a causal effect on factor Z.
Factor Z has a causal effect on factor D."""

    cf_cr_text = """The following text describes the assumed causal relationship between things in a recent study:
The change of C happens if the change of A happens.
The change of D happens if the change of B happens.
The change of E happens if the change of C happens.
The change of F happens if the change of C happens.
The change of F happens if the change of D happens.
The change of G happens if the change of E happens and the change of F happens.
The change of H happens if the change of F not happen."""

    if query_type == "conf_ce_path":
        q_text = """
Question:
We want to estimate the causal effect of factor A and factor C on factor B and factor D.
Based on the information above, please identify all the causal paths between them.
Answer:
factor A -> factor X -> factor B
factor A -> factor D
factor C -> factor Y -> factor Z -> factor D"""
        return add_1_example(query_type) + '\n\n' + conf_cr_text + q_text

    elif query_type == "conf_conf_ctrl":
        q_text = """
Question:
We want to estimate the causal effect of factor A and factor C on factor B and factor D.
Based on the information above, please provide a set of factors that can block all backdoor paths between them.
Answer:
factor E"""
        return add_1_example(query_type) + "\n\n" + conf_cr_text + q_text

    elif query_type == "cf_f_infer":
        q_text = """
Question:
We have observed the change of A happened and the change of B happened.
What about the change of G and the change of H?
Answer:
The change of G happened.
The change of H didn't happen."""
        return add_1_example(query_type) + "\n\n" + cf_cr_text + q_text

    elif query_type == "cf_cf_infer":
        q_text = """
Question:
We have observed the change of A happened and the change of B happened.
What the change of G and the change of H would be if the change of C didn't happen and change of E didn't happen?
Answer:
The change of G will not happen.
The change of H will not happen."""
        return add_1_example(query_type) + "\n\n" + cf_cr_text + q_text

    else:
        return None


def add_zero_shot_cot():
    return "Let's think step by step."


def add_1_shot_cot(query_type):
    conf_cr_text = """The following text describes the assumed causal relationship between things in a recent study:
Factor A has a causal effect on factor B.
Factor B has a causal effect on factor C.
Factor D has a causal effect on factor A and factor E.
Factor C has a causal effect on factor E.
Factor F has a causal effect on factor A and factor C."""

    cf_cr_text = """The following text describes the assumed causal relationship between things in a recent study:
The change of B happens if the change of A happens.
The change of C happens if the change of B happens.
The change of D happens if the change of B happens.
The change of E happens if the change of C happens and the change of D happens."""

    if query_type == "conf_ce_path":
        q_text = """
Question:
We want to estimate the causal effect of factor A on factor C.
Based on the information above, please identify all the causal paths between them.
Answer:
Factor A only has a causal effect on factor B, and factor B only has a causal effect on factor C.
So all the causal paths between factor A and factor C are:
factor A -> factor B -> factor C"""
        return conf_cr_text + q_text

    elif query_type == "conf_conf_ctrl":
        q_text = """
Question:
We want to estimate the causal effect of factor A on factor C.
Based on the information above, please provide a set of factors that can block all backdoor paths between them.
Answer:
There are two paths with a factor has causal effect on factor A and end at factor B:
factor A <- factor D -> factor E <- factor C, in this path, since factor E is a collider and is not controlled, this path is naturally blocked.
factor A <- factor F -> factor C, in this path since no factor has been controlled, factor F need to be controlled to block this path.
So one answer is:
factor F"""
        return conf_cr_text + q_text

    elif query_type == "cf_f_infer":
        q_text = """
Question:
We have observed the change of A happened.
What about the change of E?
Answer:
The change of B happened because the change of A happened.
The change of C and the change of D happened because the change of B happened.
The change of E happened because the change of C and the change of D happened.
So the change of E happened."""
        return cf_cr_text + q_text

    elif query_type == "cf_cf_infer":
        q_text = """
Question:
We have observed the change of A happened.
What the change of E would be if the change of C didn't happen?
Answer:
The change of B happened because the change of A happened.
The change of D happened because the change of B happened.
The change of C didn't happen.
The change of E will not happen because the change of C didn't happen.
So the change of E will not happen."""
        return cf_cr_text + q_text

    else:
        return None


def add_2_shot_cot(query_type):
    conf_cr_text = """The following text describes the assumed causal relationship between things in a recent study:
Factor A has a causal effect on factor D and factor X.
Factor C has a causal effect on factor Y.
Factor D has a causal effect on factor H.
Factor E has a causal effect on factor A and factor F.
Factor F has a causal effect on factor B.
Factor G has a causal effect on factor C and factor H.
Factor X has a causal effect on factor B.
Factor Y has a causal effect on factor Z.
Factor Z has a causal effect on factor D."""

    cf_cr_text = """The following text describes the assumed causal relationship between things in a recent study:
The change of C happens if the change of A happens.
The change of D happens if the change of B happens.
The change of E happens if the change of C happens.
The change of F happens if the change of C happens.
The change of F happens if the change of D happens.
The change of G happens if the change of E happens and the change of F happens.
The change of H happens if the change of F not happen."""

    if query_type == "conf_ce_path":
        q_text = """
Question:
We want to estimate the causal effect of factor A and factor C on factor B and factor D.
Based on the information above, please identify all the causal paths between them.
Answer:
Factor A has a causal effect on factor X and factor X has a causal effect on factor B.
Factor A has a causal effect on factor D.
Factor C has a causal effect on factor Y, factor Y has a causal effect on factor Z and factor Z has a causal effect on factor D.
So all the causal paths between factor A and factor C are:
factor A -> factor X -> factor B
factor A -> factor D
factor C -> factor Y -> factor Z -> factor D"""
        return add_1_shot_cot(query_type) + "\n\n" + conf_cr_text + q_text

    elif query_type == "conf_conf_ctrl":
        q_text = """
Question:
We want to estimate the causal effect of factor A and factor C on factor B and factor D.
Based on the information above, please provide a set of factors that can block all backdoor paths between them.
Answer:
There are two paths with a factor has causal effect on factor A or factor C and end at factor B or factor D:
factor A <- factor E -> factor F -> factor B, in this path since no factor has been controlled, factor E or factor F need to be controlled to block this path.
factor C <- factor G -> factor H <- factor D,  in this path, since factor H is a collider and is not controlled, this path is naturally blocked.
So one answer is:
factor E"""
        return add_1_shot_cot(query_type) + "\n\n" + conf_cr_text + q_text

    elif query_type == "cf_f_infer":
        q_text = """
Question:
We have observed the change of A happened and the change of B happened.
What about the change of G and the change of H?
Answer:
The change of C happened because the change of A happened.
The change of D happened because the change of B happened.
The change of E happened because the change of C happened.
The change of F happened because the change of C happened.
The change of F happened because the change of D happened.
The change of G happened because the change of E and the change of F happened.
The change of H didn't happen because the change of F happened.
So the change of G happened, the change of H didn't happen."""
        return add_1_shot_cot(query_type) + "\n\n" + cf_cr_text + q_text

    elif query_type == "cf_cf_infer":
        q_text = """
Question:
We have observed the change of A happened and the change of B happened.
What the change of G and the change of H would be if the change of C didn't happen and change of E didn't happen?
Answer:
The change of C didn't happen.
The change of D happened because the change of B happened.
The change of E didn't happen.
The change of F happened because the change of D happened.
The change of G will not happen because the change of E didn't happen.
The change of H will not happen because the change of F happened.
So the change of G will not happen, the change of H will not happen."""
        return add_1_shot_cot(query_type) + "\n\n" + cf_cr_text + q_text

    else:
        return None


def add_mistake_hint(query_type):
    match query_type:
        case "conf_ce_path":
            return "Please carefully check before arriving at the final answer to avoid missing causal paths or including non-existent paths in the answer."
        
        case "conf_conf_ctrl":
            return "Please carefully check before arriving at the final answer to confirm whether all backdoor paths have been blocked, avoiding any omissions."
        
        case "cf_f_infer":
            return "Please carefully check before arriving at the final answer to confirm whether the reasoning aligns with the observed event states and the dependencies between events."
        
        case "cf_cf_infer":
            return "Please carefully check before arriving at the final answer to confirm whether the reasoning aligns with the observed event states and the dependencies between events, as updated based on counterfactual assumptions."


def test_llm(api_key, model, query_type, graph_shape_group, graph_shape, name_type, prompt_type, data_folder, output_path):
    f_qd = open(data_folder + "/" + query_type.split("_")[0] + "_query_data_" + graph_shape_group + ".pkl", 'rb')
    f_nd = open(data_folder + "/node_name_data_" + graph_shape_group + ".pkl", 'rb')
    f_gd = open(data_folder + "/graph_data_" + graph_shape_group + ".pkl", 'rb')
    f_out = open(output_path, 'w', encoding='utf-8')

    test_counter = 0
    f_infer_history = []
    current_gid = ""
    graph_dict = {}
    name_dict = {}
    retry_threshold = 3
    global_retry_threshold = retry_threshold * 20
    global_retried_cnt = 0
    if query_type[0:2] == "cf":
        if name_type != "specific":
            name_type = name_type + "_c"
    while True:
        try:
            query_dict = pickle.load(f_qd)
            if query_type[0:4] == "conf":
                query_item_id = query_dict['conf_id']
            else:
                query_item_id = query_dict['cf_id']
            test_counter += 1
            required_gid = query_item_id[:8]
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
                        sys.exit("Data incompatible.")

            if query_filter(qid=query_item_id, gs=graph_shape, f_infer_history=f_infer_history):
                print(datetime.now(), f"test process at {test_counter} | {query_item_id}", flush=True)
                if query_type[0:4] == "conf":
                    c_relation, ce_query = conf_d2t(name_dict[name_type], query_dict, graph_dict['mat'])
                    ce_path_query, conf_ctrl_query = get_conf_prompt(c_relation, ce_query, name_type)
                    if query_type == "conf_ce_path":
                        query = ce_path_query
                    else:
                        query = conf_ctrl_query

                else:
                    c_relation, clue, f_query, cf_query, what_if = cf_d2t(name_dict[name_type], query_dict, graph_dict['mat'])
                    f_infer_query, cf_infer_query = get_cf_prompt(c_relation, clue, f_query, cf_query, what_if, name_type)
                    if query_type == "cf_f_infer":
                        query = f_infer_query
                        f_infer_history.append(current_gid)
                    else:
                        query = cf_infer_query

                input_text = ""
                match prompt_type:
                    case "zero_shot":
                        input_text = query + "\nYour answer should be plain text and should not contain other formats such as markdown.\nAnswer:\n"
                    case "one_shot":
                        input_text = add_1_example(query_type) + "\n\n" + query + "\nAnswer:\n"
                    case "two_shot":
                        input_text = add_2_examples(query_type) + "\n\n" + query + "\nAnswer:\n"
                    case "zero_cot":
                        input_text = query + "\nYour answer should be plain text and should not contain other formats such as markdown.\nAnswer:\n" + add_zero_shot_cot()
                    case "one_cot":
                        input_text = add_1_shot_cot(query_type) + "\n\n" + query + "\nAnswer:\n"
                    case "two_cot":
                        input_text = add_2_shot_cot(query_type) + "\n\n" + query + "\nAnswer:\n"
                    case "mis_hint":
                        input_text = query + "\n" + add_mistake_hint(query_type) + "\nYour answer should be plain text and should not contain other formats such as markdown.\nAnswer:\n"

                retry_cnt = 0
                backoff_time = 10
                res_text = "[Network Error]"
                while retry_cnt < retry_threshold:
                    try:
                        res_text = get_response(api_key, model, input_text)['choices'][0]['message']['content']
                        global_retried_cnt = 0
                        break
                    except:
                        time.sleep(backoff_time)
                        backoff_time *= 1.5
                        retry_cnt += 1
                        global_retried_cnt += 1

                # print(f"======={query_item_id}=======", flush=True)
                # print(f"query:\n {input_text}\n", flush=True)
                # print(f"response:\n {res_text}\n", flush=True)
                response_item = {"query_id": query_item_id, "input_text": input_text, "query_text": query, "response_text": res_text}
                f_out.write(json.dumps(response_item, ensure_ascii=False) + '\n')
                f_out.flush()
                if global_retried_cnt >= global_retry_threshold:
                    f_qd.close()
                    f_gd.close()
                    f_nd.close()
                    f_out.close()
                    sys.exit("Failed to connect to llm api after many retries.")
        
        except EOFError:
            f_qd.close()
            f_gd.close()
            f_nd.close()
            f_out.close()
            break
