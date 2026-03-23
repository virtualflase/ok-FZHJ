from src.tasks.GameTriggerTaskBase import GameTriggerTaskBase


class AlchemyTriggerTask(GameTriggerTaskBase):
    non_negative_int_keys = ("max_rounds",)
    # 这些点位来自旧脚本 1280x720 下的绝对坐标，迁移后改成了相对坐标以适配分辨率变化。
    MODE_OPTION_POINT = (0.59375, 0.27778)
    ALCHEMY_START_POINT = (0.78125, 0.83333)
    ALCHEMY_OBTAIN_POINT = (0.9375, 0.97222)
    WHITE_MATERIAL_STOP_THRESHOLD = (0.34375, 0.41667)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setup_task()

    def setup_task(self):
        self.name = "自动炼金"
        self.description = "切换炼金模式并按轮数自动炼金"
        # 这两个状态只跟当前任务实例有关，用来记住是否已切模式、已经炼了多少轮。
        self.change_mode = getattr(self, "change_mode", False)
        self.round_count = getattr(self, "round_count", 0)
        self.default_config.update({
            "enabled": True,
            "max_rounds": 1,
            "trigger_interval": 0.6,
        })

    def run(self):
        if not self.is_enabled():
            return

        max_rounds = self.get_int_setting("max_rounds", 1)

        # 先领已经完成的炼金结果，避免下一轮逻辑卡在奖励弹层。
        if self.handle_obtain(max_rounds):
            return

        # 达到轮数上限后不再继续选材，而是走统一退出流程。
        if self.round_count >= max_rounds:
            self.finish_alchemy_run("max_rounds_reached")
            return

        # 如果当前还停在炼金入口，优先先进入炼金界面。
        if self.click_feature("alchemy_entry", after_sleep=0.4):
            return

        # 首次进入时要先切到“按道具数量”模式，后续轮次直接沿用这个状态。
        if not self.change_mode and self.find_feature_box("alchemy_one_click_select") is not None:
            if self.click_feature("alchemy_mode_switch", after_sleep=0.6):
                self.click_relative(*self.MODE_OPTION_POINT, after_sleep=0.6)
                self.change_mode = True
                self.log_info("AlchemyTriggerTask switched to item-count mode")
                return

        # 没看到道具数量模式时说明界面还没准备好，这一轮先不继续推进。
        if self.find_feature_box("alchemy_item_count_mode") is None:
            return

        # 白材料被推到左上阈值后，说明旧脚本定义的停止条件已经满足。
        if self.should_stop_for_white_material():
            self.finish_alchemy_run("white_material_threshold")
            return

        # 进入正式炼金步骤：一键选材、确认，然后点击开始炼金。
        if not self.click_feature("alchemy_one_click_select", after_sleep=2.0):
            return
        if not self.click_feature("alchemy_confirm", after_sleep=0.4):
            return

        self.round_count += 1
        self.log_info(f"AlchemyTriggerTask round start={self.round_count}")
        self.click_relative(*self.ALCHEMY_START_POINT, after_sleep=2.0)

    def handle_obtain(self, max_rounds: int) -> bool:
        if self.find_feature_box("alchemy_obtain") is None:
            return False
        self.click_relative(*self.ALCHEMY_OBTAIN_POINT, after_sleep=0.6)
        self.log_debug("AlchemyTriggerTask clicked obtain")
        if self.round_count >= max_rounds:
            self.finish_alchemy_run("obtain_after_max_rounds")
        return True

    def should_stop_for_white_material(self) -> bool:
        # Box.center() 给的是像素坐标，这里要先换算成相对屏幕比例，再跟阈值比较才不会受分辨率影响。
        white_material = self.find_feature_box("alchemy_white_material")
        if white_material is None:
            return False
        center_x, center_y = white_material.center()
        screen_width = getattr(self, "screen_width", 1) or 1
        screen_height = getattr(self, "screen_height", 1) or 1
        return (
            center_x / screen_width < self.WHITE_MATERIAL_STOP_THRESHOLD[0]
            and center_y / screen_height < self.WHITE_MATERIAL_STOP_THRESHOLD[1]
        )

    def finish_alchemy_run(self, reason: str):
        # 旧脚本的退出路径就是“取消当前炼金界面，然后返回上一层”，这里保持同样的收尾方式。
        self.log_info(f"AlchemyTriggerTask finish reason={reason}")
        if self.click_feature("alchemy_cancel", after_sleep=0.6):
            self.click_feature("back_button", after_sleep=2.0)
