import unittest
from djl_python.properties_manager.properties import Properties
from djl_python.properties_manager.tnx_properties import TransformerNeuronXProperties
from djl_python.properties_manager.trt_properties import TensorRtLlmProperties

common_properties = {
    "model_id": "model_id",
    "model_dir": "model_dir",
    "rolling_batch": "auto",
    "tensor_parallel_degree": "4",
}


class TestConfigManager(unittest.TestCase):

    def test_common_configs(self):
        configs = Properties(**common_properties)
        self.assertEqual(common_properties['model_id'],
                         configs.model_id_or_path)
        self.assertEqual(common_properties['rolling_batch'],
                         configs.rolling_batch)
        self.assertEqual(int(common_properties['tensor_parallel_degree']),
                         configs.tensor_parallel_degree)

        self.assertEqual(configs.batch_size, 1)
        self.assertEqual(configs.max_rolling_batch_size, 32)
        self.assertEqual(configs.enable_streaming.value, 'true')

        self.assertFalse(configs.trust_remote_code)
        self.assertIsNone(configs.dtype)
        self.assertIsNone(configs.revision)

    def test_common_configs_error_case(self):
        other_properties = common_properties
        other_properties["rolling_batch"] = "disable"
        other_properties["enable_streaming"] = "true"
        other_properties["batch_size"] = 2
        with self.assertRaises(ValueError):
            Properties(**other_properties)

    def test_tnx_configs(self):
        common_props = common_properties
        common_props["rolling_batch"] = "disable"
        common_props['batch_size'] = 4
        common_props['max_rolling_batch_size'] = 2
        common_props['enable_streaming'] = 'False'
        properties = {
            "n_positions": "256",
            "load_split_model": "true",
            "quantize": "bitsandbytes8",
            "compiled_graph_path": "s3://test/bucket/folder"
        }
        tnx_configs = TransformerNeuronXProperties(**common_props,
                                                   **properties)
        self.assertFalse(tnx_configs.low_cpu_mem_usage)
        self.assertTrue(tnx_configs.load_split_model)
        self.assertEqual(int(properties['n_positions']),
                         tnx_configs.n_positions)
        self.assertEqual(tnx_configs.tensor_parallel_degree,
                         int(common_properties['tensor_parallel_degree']))
        self.assertEqual(tnx_configs.quantize.value, properties['quantize'])
        self.assertTrue(tnx_configs.load_in_8bit)
        self.assertEqual(tnx_configs.batch_size, 4)
        self.assertEqual(tnx_configs.max_rolling_batch_size, 2)
        self.assertEqual(tnx_configs.enable_streaming.value, 'false')
        self.assertEqual(tnx_configs.compiled_graph_path,
                         str(properties['compiled_graph_path']))

    def test_tnx_configs_error_case(self):
        common_props = common_properties
        common_props["rolling_batch"] = "disable"
        common_props['batch_size'] = 4
        common_props['max_rolling_batch_size'] = 2
        common_props['enable_streaming'] = 'False'
        properties = {
            "n_positions": "256",
            "load_split_model": "true",
            "quantize": "bitsandbytes8",
        }

        def test_url_not_s3_uri(url):
            properties['compiled_graph_path'] = url
            with self.assertRaises(ValueError):
                TransformerNeuronXProperties(**common_props, **properties)
            del properties['compiled_graph_path']

        def test_non_existent_directory(directory):
            properties['compiled_graph_path'] = directory
            with self.assertRaises(ValueError):
                TransformerNeuronXProperties(**common_props, **properties)
            del properties['compiled_graph_path']

        test_url_not_s3_uri("https://random.url.address/")
        test_non_existent_directory("not_a_directory")

    def test_trtllm_configs(self):
        properties = {
            "model_id": "model_id",
            "model_dir": "model_dir",
            "rolling_batch": "auto",
        }
        trt_configs = TensorRtLlmProperties(**properties)
        self.assertEqual(trt_configs.model_id_or_path, properties['model_id'])
        self.assertEqual(trt_configs.rolling_batch.value,
                         properties['rolling_batch'])

    def test_trtllm_error_cases(self):
        properties = {
            "model_id": "model_id",
            "model_dir": "model_dir",
        }

        def test_trtllm_rb_disable():
            properties['rolling_batch'] = 'disable'
            with self.assertRaises(ValueError):
                TensorRtLlmProperties(**properties)

        def test_trtllm_rb_invalid():
            properties['rolling_batch'] = 'lmi-dist'
            with self.assertRaises(ValueError):
                TensorRtLlmProperties(**properties)

        test_trtllm_rb_invalid()
        test_trtllm_rb_disable()


if __name__ == '__main__':
    unittest.main()