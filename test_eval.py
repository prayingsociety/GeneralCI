import os
import sys
from datetime import datetime
from settings import get_test_settings
from test_utils import test_llm
from eval_utils import extract_answer, eval_llm


data_folder = "./generated_data/pickle"
output_folder = "./result"
settings = get_test_settings(int(sys.argv[1]))
extractor_model = "gpt-4o"

print(datetime.now(), "work start...", flush=True)
for model in settings.keys():
    if settings[model]['enable']:
        test_api_key = settings[model]['test_api_key']
        extractor_api_key = settings[model]['extractor_api_key']
        graph_shape_group = settings[model]['graph_shape_group']
        graph_shape = settings[model]['graph_shape']
        model_folder = output_folder + '/' + model
        test_folder = model_folder + '/test'
        ans_ex_folder = model_folder + '/ans_ex'
        eval_folder = model_folder + '/eval'
        os.makedirs(test_folder, exist_ok=True)
        os.makedirs(ans_ex_folder, exist_ok=True)
        os.makedirs(eval_folder, exist_ok=True)
    
        for t in settings[model]['task']:
            for n in settings[model]['name_type']:
                for p in settings[model]['prompt']:
                    indicators = [t, graph_shape_group, n, p]
                    file_name = "_".join(indicators)
                    print('─' * 60)
                    print(datetime.now(), f"currently at: {model} | {file_name}", flush=True)
                    
                    print(datetime.now(), "start test...", flush=True)
                    if settings[model]['test']:
                        output_path = test_folder + "/" + file_name + ".json"
                        test_llm(test_api_key, model, t, graph_shape_group, graph_shape, n, p, data_folder, output_path)
                    print(datetime.now(), "test done", flush=True)
                    
                    print(datetime.now(), "start answer extraction...", flush=True)
                    if settings[model]['ans_ex']:
                        res_path = test_folder + "/" + file_name + ".json"
                        output_path = ans_ex_folder + "/" + file_name + ".json"
                        extract_answer(extractor_api_key, extractor_model, t, res_path, output_path)
                    print(datetime.now(), "answer extraction done", flush=True)
                    
                    print(datetime.now(), "start evaluation...", flush=True)
                    if settings[model]['eval']:
                        ans_ex_path = ans_ex_folder + "/" + file_name + ".json"
                        output_path = eval_folder + "/" + file_name + ".json"
                        eval_llm(t, graph_shape_group, n, data_folder, ans_ex_path, output_path)
                    print(datetime.now(), "evaluation done", flush=True)

print('─' * 60)
print(datetime.now(), "all finished", flush=True)
