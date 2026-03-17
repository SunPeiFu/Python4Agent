from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_text_splitters import Language

# 定义py代码 
GAME_CODE = """
class CombatSystem:
   def __init__(self):
       self.health = 100
       self.stamina = 100
       self.state = "IDLE"
       self.attack_patterns = {
           "NORMAL": 10,
           "SPECIAL": 30,
           "ULTIMATE": 50
       }
   def update(self, delta_time):
       self._update_stats(delta_time)
       self._handle_combat()
   def _update_stats(self, delta_time):
       self.stamina = min(100, self.stamina + 5 * delta_time)
   def _handle_combat(self):
       if self.state == "ATTACKING":
           self._execute_attack()
   def _execute_attack(self):
       if self.stamina >= self.attack_patterns["SPECIAL"]:
           damage = 50
           self.stamina -= self.attack_patterns["SPECIAL"]
           return damage
       return self.attack_patterns["NORMAL"]
class InventorySystem:
   def __init__(self):
       self.items = {}
       self.capacity = 20
       self.gold = 0
   def add_item(self, item_id, quantity):
       if len(self.items) < self.capacity:
           if item_id in self.items:
               self.items[item_id] += quantity
           else:
               self.items[item_id] = quantity
   def remove_item(self, item_id, quantity):
       if item_id in self.items:
           self.items[item_id] -= quantity
           if self.items[item_id] <= 0:
               del self.items[item_id]
   def get_item_count(self, item_id):
       return self.items.get(item_id, 0)
class QuestSystem:
   def __init__(self):
       self.active_quests = {}
       self.completed_quests = set()
       self.quest_log = []
   def add_quest(self, quest_id, quest_data):
       if quest_id not in self.active_quests:
           self.active_quests[quest_id] = quest_data
           self.quest_log.append(f"Started quest: {quest_data['name']}")
   def complete_quest(self, quest_id):
       if quest_id in self.active_quests:
           self.completed_quests.add(quest_id)
           del self.active_quests[quest_id]
   def get_active_quests(self):
       return list(self.active_quests.keys())
"""

# 使用语言规则(分隔符)切分 而不是纯数字切分 目的是保持chunk后代码结构 
    # 按代码结构 class切
    # 在按照def方法切
    # 在按照空行
    # 在按照字符
language_split = RecursiveCharacterTextSplitter.from_language(
    language = Language.PYTHON,
    chunk_size = 500,
    chunk_overlap = 15,
)

docs = language_split.create_documents([GAME_CODE])
for i,doc in enumerate(docs):
    print("当前索引:",i)
    print("当前pagecontent:",doc.page_content)
    print("-"*50)