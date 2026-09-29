"""转职觉醒系统"""
import time
from dataclasses import dataclass, field

MIN_CHANGE_LEVEL = 50
CHANGE_COOLDOWN = 7 * 24 * 3600  # 7 天
SKILL_REFUND_POINTS = 10         # 每个旧技能返还的技能点
AWAKEN_BONUS = 100

JOB_SKILLS = {
    "warrior": ["slash", "charge", "shield_wall"],
    "mage": ["fireball", "frostbolt", "teleport"],
    "priest": ["heal", "smite", "blessing"],
    "rogue": ["backstab", "stealth", "evasion"],
}

# 装备 -> 装备类型；职业 -> 可穿戴类型
EQUIPMENT_TYPES = {
    "sword": "sword", "shield": "shield", "plate_armor": "heavy",
    "staff": "staff", "wand": "wand", "robe": "cloth",
    "dagger": "dagger", "leather_armor": "leather",
}
JOB_EQUIPMENT_TYPES = {
    "warrior": {"sword", "shield", "heavy"},
    "mage": {"staff", "wand", "cloth"},
    "priest": {"staff", "wand", "cloth"},
    "rogue": {"dagger", "leather"},
}

AWAKENING_TASK_CHAIN = ["awaken_trial_1", "awaken_trial_2", "awaken_trial_3"]


@dataclass
class Player:
    pid: str
    job: str
    level: int
    stat_points: int          # 未分配属性点
    skills: list
    equipment: list
    allocated: dict = field(default_factory=dict)   # 已分配属性点
    inventory: list = field(default_factory=list)   # 背包
    mailbox: list = field(default_factory=list)     # 邮件(背包满时)
    inventory_cap: int = 100


class JobChangeSystem:
    def __init__(self):
        self.players: dict[str, Player] = {}
        self.last_change: dict[str, float] = {}       # pid -> 上次转职时间
        self.awakening_tasks: dict[str, dict] = {}    # pid -> {task: done}
        self.awakened: set[str] = set()               # 已觉醒(防重复刷)
        self.history: list[dict] = []                 # 转职记录

    # ---- 转职 ----
    def can_change(self, pid, now=None):
        """等级 + 时间冷却双重条件"""
        p = self.players[pid]
        if p.level < MIN_CHANGE_LEVEL:
            return False
        now = time.time() if now is None else now
        last = self.last_change.get(pid)
        if last is not None and now - last < CHANGE_COOLDOWN:
            return False
        return True

    def change_job(self, pid, new_job, reason="", now=None):
        if new_job not in JOB_SKILLS:
            return False
        if not self.can_change(pid, now=now):
            return False
        p = self.players[pid]
        now = time.time() if now is None else now
        old_job = p.job

        # bug1: 替换为新职业技能树，旧技能按规则返还技能点
        p.stat_points += SKILL_REFUND_POINTS * len(p.skills)
        p.skills = list(JOB_SKILLS[new_job])

        # bug2: 已分配属性点全部回收为未分配状态
        p.stat_points += sum(p.allocated.values())
        p.allocated.clear()

        # bug5: 不兼容装备自动卸下 -> 背包，背包满 -> 邮件
        allowed = JOB_EQUIPMENT_TYPES.get(new_job, set())
        kept = []
        for item in p.equipment:
            if EQUIPMENT_TYPES.get(item) in allowed:
                kept.append(item)
            elif len(p.inventory) < p.inventory_cap:
                p.inventory.append(item)
            else:
                p.mailbox.append(item)
        p.equipment = kept

        p.job = new_job
        self.last_change[pid] = now

        # bug6: 保存转职记录(历史职业、时间、原因)
        self.history.append({
            "pid": pid, "from_job": old_job, "to_job": new_job,
            "time": now, "reason": reason,
        })
        return True

    def get_history(self, pid):
        return [r for r in self.history if r["pid"] == pid]

    # ---- 觉醒 ----
    def start_awakening(self, pid):
        """开启觉醒任务链"""
        self.awakening_tasks[pid] = {t: False for t in AWAKENING_TASK_CHAIN}

    def complete_awakening_task(self, pid, task):
        tasks = self.awakening_tasks.get(pid)
        if tasks is None or task not in tasks:
            return False
        tasks[task] = True
        return True

    def unlock_awakening(self, pid):
        """bug4: 必须完成整条觉醒任务链"""
        tasks = self.awakening_tasks.get(pid)
        return bool(tasks) and all(tasks.values())

    def awaken(self, pid):
        """bug7: 只能觉醒一次，重复觉醒无效"""
        if pid in self.awakened:
            return False
        if not self.unlock_awakening(pid):
            return False
        p = self.players[pid]
        p.stat_points += AWAKEN_BONUS
        self.awakened.add(pid)
        return True
