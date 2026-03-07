import unittest

_IMPORT_ERROR = None
try:
    from ok.test.TaskTestCase import TaskTestCase
    from src.config import config
    from src.tasks.AlchemyTriggerTask import AlchemyTriggerTask
    from src.tasks.AutoApTriggerTask import AutoApTriggerTask
    from src.tasks.AutoSkipTriggerTask import AutoSkipTriggerTask
    from src.tasks.MaterialStageTriggerTask import MaterialStageTriggerTask
except ModuleNotFoundError as exc:
    _IMPORT_ERROR = exc


if _IMPORT_ERROR is not None:
    @unittest.skip(f"Missing optional test dependency: {_IMPORT_ERROR.name}")
    class TestMigratedFeatureSmoke(unittest.TestCase):
        def test_missing_dependencies(self):
            self.fail("This test should be skipped")
else:
    class TestAutoSkipFeatureSmoke(TaskTestCase):
        task_class = AutoSkipTriggerTask
        config = config

        def test_skip_button_image_triggers_click(self):
            self.set_image('tests/images/loop_tasks/skip_button.png')
            clicked = []
            self.task.click_box = lambda box, **kwargs: clicked.append(box.name) or True

            self.task.run()

            self.assertEqual(clicked, ['skip_button'])


    class TestAutoApFeatureSmoke(TaskTestCase):
        task_class = AutoApTriggerTask
        config = config

        def test_ap_tip_feature_is_registered(self):
            self.set_image('tests/images/loop_tasks/ap_tip.png')

            self.assertIsNotNone(self.task.find_feature_box('ap_tip'))


    class TestMaterialStageFeatureSmoke(TaskTestCase):
        task_class = MaterialStageTriggerTask
        config = config

        def test_material_stage_image_triggers_click(self):
            self.set_image('tests/images/loop_tasks/material_stage_start.png')
            self.task.config = {**self.task.default_config, 'enabled': True}
            clicked = []
            self.task.click_box = lambda box, **kwargs: clicked.append(box.name) or True

            self.task.run()

            self.assertEqual(clicked, ['material_stage_start'])


    class TestAlchemyFeatureSmoke(TaskTestCase):
        task_class = AlchemyTriggerTask
        config = config

        def test_alchemy_entry_image_triggers_click(self):
            self.set_image('tests/images/loop_tasks/alchemy_entry.png')
            clicked = []
            self.task.click_box = lambda box, **kwargs: clicked.append(box.name) or True

            self.task.run()

            self.assertEqual(clicked, ['alchemy_entry'])


if __name__ == '__main__':
    unittest.main()
