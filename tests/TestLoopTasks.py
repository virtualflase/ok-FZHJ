import unittest
import sys
import types
from unittest.mock import Mock

if "ok" not in sys.modules:
    ok_stub = types.ModuleType("ok")

    class TriggerTask:
        def __init__(self, *args, **kwargs):
            self.default_config = {}
            self.config_type = {}

    ok_stub.TriggerTask = TriggerTask
    sys.modules["ok"] = ok_stub

from src.tasks.AlchemyTriggerTask import AlchemyTriggerTask
from src.tasks.AutoApTriggerTask import AutoApTriggerTask
from src.tasks.AutoSkipTriggerTask import AutoSkipTriggerTask
from src.tasks.MaterialStageTriggerTask import MaterialStageTriggerTask


class FakeBox:
    def __init__(self, name, center=(0.5, 0.5)):
        self.name = name
        self._center = center

    def center(self):
        return self._center


def make_task(task_cls, config=None):
    task = object.__new__(task_cls)
    task.default_config = {}
    task.config_type = {}
    task.init_base_task()
    task.setup_task()
    task.config = dict(task.default_config)
    if config:
        task.config.update(config)
    task.log_debug = Mock()
    task.log_info = Mock()
    task.log_error = Mock()
    task.click_box = Mock(return_value=True)
    task.click_relative = Mock(return_value=True)
    task.sleep = Mock()
    task.feature_exists = Mock(return_value=True)
    task.screen_width = 1
    task.screen_height = 1
    return task


class TestAutoSkipTriggerTask(unittest.TestCase):

    def test_priority_uses_skip_before_continue(self):
        task = make_task(AutoSkipTriggerTask)
        feature_boxes = {
            "skip_button": FakeBox("skip_button"),
            "blank_continue_primary": FakeBox("blank_continue_primary"),
            "blank_continue_secondary": FakeBox("blank_continue_secondary"),
        }
        task.find_one = Mock(side_effect=lambda name: feature_boxes.get(name))

        task.run()

        self.assertEqual(
            [call.args[0] for call in task.find_one.call_args_list],
            ["skip_button"],
        )
        task.click_box.assert_called_once()
        self.assertEqual(task.click_box.call_args.args[0].name, "skip_button")

    def test_secondary_continue_used_when_primary_missing(self):
        task = make_task(AutoSkipTriggerTask)
        feature_boxes = {
            "blank_continue_secondary": FakeBox("blank_continue_secondary"),
        }
        task.find_one = Mock(side_effect=lambda name: feature_boxes.get(name))

        task.run()

        self.assertEqual(
            [call.args[0] for call in task.find_one.call_args_list],
            ["skip_button", "blank_continue_primary", "blank_continue_secondary"],
        )
        self.assertEqual(task.click_box.call_args.args[0].name, "blank_continue_secondary")


class TestAutoApTriggerTask(unittest.TestCase):

    def test_ap_flow_clicks_entry_confirms_and_exit_buttons(self):
        task = make_task(AutoApTriggerTask, {"max_use_clicks": 2})
        feature_state = {
            "ap_tip": [FakeBox("ap_tip")],
            "ap_use_entry": [FakeBox("ap_use_entry")],
            "ap_use_confirm": [FakeBox("ap_use_confirm"), FakeBox("ap_use_confirm"), None],
            "back_button": [FakeBox("back_button"), FakeBox("back_button")],
            "next_stage_button": [FakeBox("next_stage_button")],
        }

        def find_one(name):
            values = feature_state.get(name, [None])
            if len(values) > 1:
                return values.pop(0)
            return values[0]

        task.find_one = Mock(side_effect=find_one)

        task.run()

        clicked = [call.args[0].name for call in task.click_box.call_args_list]
        self.assertEqual(
            clicked,
            [
                "ap_use_entry",
                "ap_use_confirm",
                "ap_use_confirm",
                "back_button",
                "back_button",
                "next_stage_button",
            ],
        )


class TestMaterialStageTriggerTask(unittest.TestCase):

    def test_material_stage_prioritizes_support_entry(self):
        task = make_task(MaterialStageTriggerTask, {"enabled": True})
        feature_boxes = {
            "support_entry": FakeBox("support_entry"),
            "battle_again_button": FakeBox("battle_again_button"),
        }
        task.find_one = Mock(side_effect=lambda name: feature_boxes.get(name))

        task.run()

        task.click_box.assert_called_once()
        self.assertEqual(task.click_box.call_args.args[0].name, "support_entry")


class TestAlchemyTriggerTask(unittest.TestCase):

    def test_switches_mode_once_then_starts_round(self):
        task = make_task(AlchemyTriggerTask, {"max_rounds": 2})
        task.change_mode = False

        def first_run_find(name):
            feature_boxes = {
                "alchemy_one_click_select": FakeBox("alchemy_one_click_select"),
                "alchemy_mode_switch": FakeBox("alchemy_mode_switch"),
            }
            return feature_boxes.get(name)

        task.find_one = Mock(side_effect=first_run_find)
        task.run()

        self.assertTrue(task.change_mode)
        self.assertEqual(task.click_box.call_args.args[0].name, "alchemy_mode_switch")
        task.click_relative.assert_called_once_with(*AlchemyTriggerTask.MODE_OPTION_POINT, after_sleep=0.6)

        task.click_box.reset_mock()
        task.click_relative.reset_mock()

        def second_run_find(name):
            feature_boxes = {
                "alchemy_item_count_mode": FakeBox("alchemy_item_count_mode"),
                "alchemy_white_material": FakeBox("alchemy_white_material", center=(0.6, 0.6)),
                "alchemy_one_click_select": FakeBox("alchemy_one_click_select"),
                "alchemy_confirm": FakeBox("alchemy_confirm"),
            }
            return feature_boxes.get(name)

        task.find_one = Mock(side_effect=second_run_find)
        task.run()

        clicked = [call.args[0].name for call in task.click_box.call_args_list]
        self.assertEqual(clicked, ["alchemy_one_click_select", "alchemy_confirm"])
        task.click_relative.assert_called_once_with(*AlchemyTriggerTask.ALCHEMY_START_POINT, after_sleep=2.0)
        self.assertEqual(task.round_count, 1)

    def test_stops_when_white_material_reaches_threshold(self):
        task = make_task(AlchemyTriggerTask)
        task.find_one = Mock(side_effect=lambda name: {
            "alchemy_item_count_mode": FakeBox("alchemy_item_count_mode"),
            "alchemy_white_material": FakeBox("alchemy_white_material", center=(0.2, 0.2)),
            "alchemy_cancel": FakeBox("alchemy_cancel"),
            "back_button": FakeBox("back_button"),
        }.get(name))

        task.run()

        clicked = [call.args[0].name for call in task.click_box.call_args_list]
        self.assertEqual(clicked, ["alchemy_cancel", "back_button"])

    def test_obtain_flow_finishes_after_max_rounds(self):
        task = make_task(AlchemyTriggerTask, {"max_rounds": 1})
        task.round_count = 1
        task.find_one = Mock(side_effect=lambda name: {
            "alchemy_obtain": FakeBox("alchemy_obtain"),
            "alchemy_cancel": FakeBox("alchemy_cancel"),
            "back_button": FakeBox("back_button"),
        }.get(name))

        task.run()

        task.click_relative.assert_called_once_with(*AlchemyTriggerTask.ALCHEMY_OBTAIN_POINT, after_sleep=0.6)
        clicked = [call.args[0].name for call in task.click_box.call_args_list]
        self.assertEqual(clicked, ["alchemy_cancel", "back_button"])


class TestSharedSceneOwnership(unittest.TestCase):

    def test_blank_continue_owned_by_auto_skip_only(self):
        shared_box = FakeBox("blank_continue_primary")

        skip_task = make_task(AutoSkipTriggerTask)
        skip_task.find_one = Mock(side_effect=lambda name: shared_box if name == "blank_continue_primary" else None)

        material_task = make_task(MaterialStageTriggerTask, {"enabled": True})
        material_task.find_one = Mock(return_value=None)

        skip_task.run()
        material_task.run()

        skip_task.click_box.assert_called_once()
        material_task.click_box.assert_not_called()


if __name__ == "__main__":
    unittest.main()
