import warnings
import os
import importlib
from transformers import AutoConfig
from flashrag.dataset.dataset import Dataset

def get_dataset(config):
    dataset_path = config['dataset_path']
    all_split = config['split']

    split_dict = {
                'train': None,
                'dev': None,
                'test': None
            }
    for split in all_split:
        split_path = os.path.join(dataset_path, f'{split}.jsonl')
        if not os.path.exists(split_path):
            print(f"{split} file not exists!")
            continue
        if split == "test" or split == 'dev':
            split_dict[split] = Dataset(config, 
                                        split_path, 
                                        sample_num = config['test_sample_num'], 
                                        random_sample = config['random_sample'])
        else:
            split_dict[split] = Dataset(config, split_path)
     
    return split_dict

def get_generator(config, **params):
    r"""Automatically select generator class based on config."""
    if "t5" in config['generator_model'] or "bart" in config['generator_model']:
        return getattr(
            importlib.import_module("flashrag.generator"), 
            "EncoderDecoderGenerator"
        )(config, **params)
    else:
        if config['use_vllm']:
            return getattr(
                importlib.import_module("flashrag.generator"), 
                "VLLMGenerator"
            )(config, **params)
        else:
            return getattr(
                    importlib.import_module("flashrag.generator"), 
                    "CausalLMGenerator"
                )(config, **params)

def get_retriever(config):
    r"""Automatically select retriever class based on config's retrieval method

    Args:
        config (dict): configuration with 'retrieval_method' key

    Returns:
        Retriever: retriever instance
    """
    if config['retrieval_method'] == "bm25":
        return getattr(
            importlib.import_module("flashrag.retriever"), 
            "BM25Retriever"
        )(config)
    else:
        return getattr(
            importlib.import_module("flashrag.retriever"), 
            "DenseRetriever"
        )(config)

def get_judger(config):
    judger_name = config['judger_name']
    if 'skr' in judger_name.lower():
        return getattr(
                importlib.import_module("flashrag.judger"), 
                "SKRJudger"
            )(config)
    else:
        assert False, "No implementation!"

def get_refiner(config):
    refiner_name = config['refiner_name']
    refiner_path = config['refiner_model_path']

    default_path_dict = {
        'recomp_abstractive_nq': 'fangyuan/nq_abstractive_compressor',
        'recomp:abstractive_tqa': 'fangyuan/tqa_abstractive_compressor',
        'recomp:abstractive_hotpotqa': 'fangyuan/hotpotqa_abstractive',
    }

    if refiner_path is None:
        if refiner_name in default_path_dict:
            refiner_path = default_path_dict[refiner_name]
        else:
            assert False, "refiner_model_path is empty!"
    
    model_config = AutoConfig.from_pretrained(refiner_path)

    if "recomp" in refiner_name.lower() or "recomp" in refiner_path:
        if model_config.model_type == "t5" :
            return getattr(
                importlib.import_module("flashrag.refiner"), 
                "AbstractiveRecompRefiner"
            )(config)
        else:
            return getattr(
                importlib.import_module("flashrag.refiner"), 
                "ExtractiveRefiner"
            )(config)
    elif "lingua" in refiner_name.lower():
        return getattr(
                importlib.import_module("flashrag.refiner"), 
                "LLMLinguaRefiner"
            )(config)
    elif "selective-context" in refiner_name.lower() or "sc" in refiner_name.lower():
        return getattr(
                importlib.import_module("flashrag.refiner"), 
                "SelectiveContextRefiner"
            )(config)
    else:
        assert False, "No implementation!"