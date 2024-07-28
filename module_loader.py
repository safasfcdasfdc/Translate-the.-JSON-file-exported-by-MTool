import importlib.util
import os

def load_custom_module(script_file_path):
    spec = importlib.util.spec_from_file_location("custom_module", script_file_path)
    custom_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(custom_module)
    return custom_module

def load_translator_and_processor(config):
    translator = None
    custom_processing_instance = None
    
    custom_translation_config = config.get('custom_translation', {})
    if custom_translation_config.get('enable', False):
        custom_script_path = custom_translation_config['script_file_path']
        if os.path.exists(custom_script_path):
            custom_translator = load_custom_module(custom_script_path)
            translator = custom_translator.CustomTranslator(config)

        processing_script_path = custom_translation_config.get('processing_script_path', None)
        if processing_script_path and os.path.exists(processing_script_path):
            custom_processing = load_custom_module(processing_script_path)
            custom_processing_instance = custom_processing.CustomProcessing(config)
    
    return translator, custom_processing_instance
