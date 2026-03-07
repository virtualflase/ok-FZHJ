from src.tasks.GameTriggerTaskBase import GameTriggerTaskBase


class MaterialStageTriggerTask(GameTriggerTaskBase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setup_task()

    def setup_task(self):
        self.name = "自动材料本"
        self.description = "处理材料本助战、开战和再次挑战"
        self.default_config.update({
            "enabled": False,
            "trigger_interval": 0.6,
        })

    def run(self):
        if not self.is_enabled():
            return
        self.click_first_present(
            "support_entry",
            "material_stage_start",
            "material_stage_battle_start",
            "battle_again_button",
            after_sleep=0.4,
        )
