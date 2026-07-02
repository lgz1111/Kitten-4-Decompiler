import xml.etree.ElementTree as ET
import json
from BlockShadowCreator import SHADOW_ALL_TYPES

class BlockDecompiler:
    def __init__(self, compiled_block):
        self.compiled_block = compiled_block
        self.type = compiled_block.get("type", "unknown_type")
        self.id = compiled_block.get("id", "unknown_id")
        self.params = compiled_block.get("params", {})
        self.child_block = compiled_block.get("child_block")
        self.next_block = compiled_block.get("next_block")

    def create_field(self, name, value):
        """生成 field 元素"""
        field = ET.Element("field", {"name": name})
        field.text = str(value)
        return field

    def toxml(self):
        """将块转换为 XML"""
        if self.type in SHADOW_ALL_TYPES:
            if self.type == "logic_empty":
                lable = "empty"
            else:
                lable = "shadow"
        else:
            lable = "block"
        block = ET.Element(lable, {"type": self.type, "id": self.id})
        # 处理 params 中的字段
        for key, value in self.params.items():
            if isinstance(value, str):  # 如果是字符串，生成 field
                block.append(self.create_field(key, value))
            elif isinstance(value, dict):  # 如果是嵌套 block，递归处理
                value_element = ET.SubElement(block, "value", {"name": key})
                value_element.append(BlockDecompiler(value).toxml())

        # 处理子块
        if self.child_block:
            statement = ET.SubElement(block, "statement", {"name": "DO"})
            statement.append(BlockDecompiler(self.child_block).toxml())

        # 处理下一个块
        if self.next_block:
            next_element = ET.SubElement(block, "next")
            next_element.append(BlockDecompiler(self.next_block).toxml())

        return block

class ActorDecompiler:

    def __init__(self, work, actor, compiledBlocks) -> None:
        self.work = work
        self.actor = actor
        self.compiled = compiledBlocks
        self.blocks = {}
        self.connections = {}

    def prepare(self):
        # 准备角色的积木数据
        self.onPrepare()

        # 将积木数据与角色关联
        self.actor["block_data_json"] = {
            "blocks": self.blocks,
            "connections": self.connections,
            "comments": {}
        }

        # 将角色中的函数添加到作品的函数集合中
        for name, compiledFunction in self.compiled["procedures"].items():
            self.work.functions[name] = compiledFunction

    def start(self):
        # 开始反编译角色
        self.onStart()

        # 反编译角色的所有函数
        for name, compiledFunction in self.compiled["procedures"].items():
            self.onStartFunction(name)
            self.blocks[name] = self.decompileFunction(compiledFunction)

        # 反编译角色的其余积木
        for id, compiledBlock in self.compiled["compiled_block_map"].items():
            self.blocks[id] = self.decompileBlock(compiledBlock)

    def decompileFunction(self, compiledFunction):
        # 反编译函数，返回字符串
        self.onPrepareFunction(compiledFunction["id"])
        decompiler = BlockDecompiler(compiledFunction)
        return ET.tostring(decompiler.toxml(), encoding="unicode")

    def decompileBlock(self, compiledBlock):
        # 反编译单个积木，返回字符串
        decompiler = BlockDecompiler(compiledBlock)
        return ET.tostring(decompiler.toxml(), encoding="unicode")

    # 钩子方法，提供扩展点
    def onPrepare(self): pass
    def onPrepareFunction(self, name): pass
    def onStart(self): pass
    def onStartFunction(self, name): pass

class KittenWorkDecompiler:

    def __init__(self, workInfo, compiledWork) -> None:
        self.workInfo = workInfo
        self.work = compiledWork
        self.functions = {}

    def start(self):
        # 开始反编译流程
        self.onStart()

        # 创建角色反编译器
        decompilers = []
        for actorCompiledBlocks in self.work["compile_result"]:
            actor = ActorDecompiler(self, self.getActor(actorCompiledBlocks["id"]), actorCompiledBlocks)
            self.onCreateActor(actor)
            decompilers.append(actor)

        # 准备所有角色
        self.onPrepareActors()
        for decompiler in decompilers:
            decompiler.prepare()

        # 开始反编译所有角色
        self.onStartActors()
        for decompiler in decompilers:
            decompiler.start()

        # 写入作品信息
        self.writeWorkInfo()

        # 清理不必要的数据
        self.clean()

        # 完成反编译
        self.onFinish()
        return self.work

    def getActor(self, actorID):
        # 获取角色或场景信息
        theatre = self.work["theatre"]
        try:
            return theatre["actors"][actorID]
        except KeyError:
            return theatre["scenes"][actorID]

    def clean(self):
        # 清理不必要的字段
        self.onClean()
        for key in {"compile_result", "preview", "author_nickname"}:
            self.work.pop(key, None)

    def writeWorkInfo(self):
        # 写入作品信息
        self.onWriteWorkInfo()
        self.work["hidden_toolbox"] = {
            "toolbox": [],
            "blocks": []
        }
        self.work["work_source_label"] = 0
        self.work["sample_id"] = ""
        self.work["project_name"] = self.workInfo["name"]
        self.work["toolbox_order"] = self.work["last_toolbox_order"] = [
            "event", "control", "action", "appearance", "audio", "pen", "sensing",
            "operator", "data", "data", "procedure", "mobile_control", "physic",
            "physics2", "cloud_variable", "cloud_list", "advanced", "ai_lab",
            "ai_game", "cognitive", "camera", "video", "wood", "arduino", "weeemake",
            "microbit", "ai", "midimusic"
        ]

    # 可扩展的钩子方法
    def onStart(self): pass
    def onCreateActor(self, actor): pass
    def onPrepareActors(self): pass
    def onStartActors(self): pass
    def onWriteWorkInfo(self): pass
    def onClean(self): pass
    def onFinish(self): pass

if __name__ == "__main__":
    test_text = """
{
    "params": {
        "OP": "ADD",
        "A": {
            "params": {
                "VALUE": {
                    "params": {
                        "NUM": "0"
                    },
                    "kind": "domain_block",
                    "type": "math_number",
                    "id": "0sT0zksYkF6v6IE7gVjm",
                    "child_block": [],
                    "first_evaluation": true,
                    "done_evaluating": false,
                    "output_type": 2,
                    "disabled": false,
                    "conditions": [],
                    "procedure_name": "",
                    "times_left": 0
                }
            },
            "kind": "domain_block",
            "type": "shadow_number",
            "id": "dGV30mbqhJriShMjfV6p",
            "child_block": [],
            "first_evaluation": true,
            "done_evaluating": false,
            "output_type": 2,
            "disabled": false,
            "conditions": [],
            "procedure_name": "",
            "times_left": 0
        },
        "B": {
            "params": {
                "NUM": "0"
            },
            "kind": "domain_block",
            "type": "math_number",
            "id": "z0r7LnFzuhdJ0SCz19yL",
            "child_block": [],
            "first_evaluation": true,
            "done_evaluating": false,
            "output_type": 2,
            "disabled": false,
            "conditions": [],
            "procedure_name": "",
            "times_left": 0
        }
    },
    "kind": "domain_block",
    "type": "math_arithmetic",
    "id": "T3tFIoiTx6euaUrBYW44",
    "child_block": [],
    "first_evaluation": true,
    "done_evaluating": false,
    "output_type": 2,
    "disabled": false,
    "conditions": [],
    "procedure_name": "",
    "times_left": 0
}
"""
    
    compiled_block = json.loads(test_text)
    decompiler = BlockDecompiler(compiled_block)
    print(ET.tostring(decompiler.toxml(), encoding="unicode"))
