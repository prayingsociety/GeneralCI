def get_test_settings(idx):
    settings = [
        {
            "gpt-3.5-turbo": {  # 0
                "enable": True,
                "test_api_key": "",
                "extractor_api_key": "",
                "task": ["conf_ce_path", "conf_conf_ctrl", "cf_f_infer", "cf_cf_infer"],
                "graph_shape_group": "00",
                "graph_shape": ["00", "01", "02"],
                "name_type": ["specific"],
                "prompt": [
                    "zero_shot",
                    "one_shot",
                    "two_shot",
                    "zero_cot",
                    "one_cot",
                    "two_cot",
                    "mis_hint",
                ],
                "test": True,
                "ans_ex": True,
                "eval": True,
            }
        },
        {
            "gpt-3.5-turbo": {  # 1
                "enable": True,
                "test_api_key": "",
                "extractor_api_key": "",
                "task": ["conf_ce_path", "conf_conf_ctrl", "cf_f_infer", "cf_cf_infer"],
                "graph_shape_group": "00",
                "graph_shape": ["00", "01", "02"],
                "name_type": ["bio", "che", "eco", "phy"],
                "prompt": [
                    "zero_shot",
                ],
                "test": True,
                "ans_ex": True,
                "eval": True,
            }
        },
    ]
    return settings[idx]


def get_data_gen_settings(idx):
    settings = [
        {
            "gs_indicator": 0,
            "graph_shape": [[1, 1, 1, 1, 1], [2, 2, 2, 2, 2], [3, 3, 3, 3, 3]],
            "graph_shape_group": "00",
            "path_iter_n": [3, 4, 5, 6],
            "graph_p": [[0.1, 0.1, 0.1]],
            "graph_n_per_condition": 50,
            "conf_ce_d": [1],
            "cf_whatif_n": [1, 2, 3],
            "name_type": ["bio", "che", "eco", "phy"],
        },
        {
            "gs_indicator": 1,
            "graph_shape": [[1, 1, 1, 1, 1, 1], [2, 2, 2, 2, 2, 2], [3, 3, 3, 3, 3, 3]],
            "graph_shape_group": "10",
            "path_iter_n": [3, 4, 5, 6],
            "graph_p": [[0.1, 0.1, 0.1]],
            "graph_n_per_condition": 50,
            "conf_ce_d": [1, 0.5],
            "cf_whatif_n": [1, 2, 3],
            "name_type": ["bio", "che", "eco", "phy"],
        },
        {
            "gs_indicator": 2,
            "graph_shape": [[1, 1, 1, 1, 1, 1, 1], [2, 2, 2, 2, 2, 2, 2]],
            "graph_shape_group": "20",
            "path_iter_n": [3, 4, 5, 6],
            "graph_p": [[0.1, 0.1, 0.1]],
            "graph_n_per_condition": 50,
            "conf_ce_d": [1, 0.5],
            "cf_whatif_n": [1, 2, 3],
            "name_type": ["bio", "che", "eco", "phy"],
        },
        {
            "gs_indicator": 3,
            "graph_shape": [[1, 1, 1, 1, 1, 1, 1, 1], [2, 2, 2, 2, 2, 2, 2, 2]],
            "graph_shape_group": "30",
            "path_iter_n": [3, 4, 5, 6],
            "graph_p": [[0.1, 0.1, 0.1]],
            "graph_n_per_condition": 50,
            "conf_ce_d": [1, 0.75, 0.5],
            "cf_whatif_n": [1, 2, 3],
            "name_type": ["bio", "che", "eco", "phy"],
        },
    ]
    return settings[idx]
