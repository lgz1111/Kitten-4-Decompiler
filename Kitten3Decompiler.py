from BlockShadowCreator import SHADOW_ALL_TYPES
import xml.etree.ElementTree as ET
import json

# 基础反编译器类
class BlockDecompiler:
    def __init__(self, compiled_block: dict):
        self.compiled_block = compiled_block
        self.type = compiled_block.get("type", "unknown_type")
        self.id = compiled_block.get("id", "unknown_id")
        self.params = compiled_block.get("params", {})
        self.child_block = compiled_block.get("child_block", [])
        self.next_block = compiled_block.get("next_block", {})

    def create_field(self, name, value) -> ET.Element:
        """生成 field 元素"""
        field = ET.Element("field", {"name": name})
        field.text = str(value)
        return field

    def toxml(self):
        """将块转换为 XML"""
        label = "shadow" if self.type in SHADOW_ALL_TYPES else "block"
        block = ET.Element(label, {"type": self.type, "id": self.id})

        # 处理 params
        self.parms(block)

        # 处理子块
        self.children(block)

        # 处理下一个块
        self.nexts(block)

        return block

    def nexts(self, block):
        if self.next_block:
            next_element = ET.SubElement(block, "next")
            next_element.append(getBlockDecompiler(self.next_block).toxml())

    def children(self, block):
        if isinstance(self.child_block, list) and self.child_block:
            statement = ET.SubElement(block, "statement", {"name": "DO"})
            for child in self.child_block:
                statement.append(getBlockDecompiler(child).toxml())

    def parms(self, block):
        for key, value in self.params.items():
            if isinstance(value, str):
                block.append(self.create_field(key, value))
            elif isinstance(value, dict):
                value_element = ET.SubElement(block, "value", {"name": key})
                value_element.append(getBlockDecompiler(value).toxml())

# 特殊积木反编译器：ControlsIfDecompiler
class ControlsIfDecompiler(BlockDecompiler):
    def toxml(self):
        block = super().toxml()
        mutation = ET.SubElement(block, "mutation", {
            "elseif": str(len(self.compiled_block.get("conditions", [])) - 1),
            "else": "1"
        })
        return block

# 特殊积木反编译器：TextJoinDecompiler
class TextJoinDecompiler(BlockDecompiler):
    def toxml(self):
        block = super().toxml()
        mutation = ET.SubElement(block, "mutation", {
            "items": str(len(self.params))
        })
        return block

# 特殊积木反编译器：Procedures2CallDecompiler
class Procedures2CallDecompiler(BlockDecompiler):
    def toxml(self):
        block = super().toxml()
        mutation = ET.SubElement(block, "mutation", {
            "name": self.compiled_block.get("procedure_name", ""),
            "def_id": self.compiled_block.get("id", "")
        })
        return block

# 特殊积木映射表
SPECIAL_DECOMPILER_MAP = {
    "controls_if": ControlsIfDecompiler,
    "text_join": TextJoinDecompiler,
    "procedures_2_callnoreturn": Procedures2CallDecompiler,
    "procedures_2_callreturn": Procedures2CallDecompiler
}

# 根据积木类型获取对应的反编译器
def getBlockDecompiler(compiled_block: dict) -> BlockDecompiler:
    block_type = compiled_block.get("type", "unknown_type")
    decompiler_class = SPECIAL_DECOMPILER_MAP.get(block_type, BlockDecompiler)
    return decompiler_class(compiled_block)

class ActorDecompiler:

    def __init__(self, work, actor:dict, compiledBlocks:dict) -> None:
        self.work = work
        self.actor: dict = actor
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
        decompiler = getBlockDecompiler(compiledFunction)
        return ET.tostring(decompiler.toxml(), encoding="unicode")

    def decompileBlock(self, compiledBlock):
        # 反编译单个积木，返回字符串
        decompiler = getBlockDecompiler(compiledBlock)
        return ET.tostring(decompiler.toxml(), encoding="unicode")

    # 钩子方法，提供扩展点
    def onPrepare(self): pass
    def onPrepareFunction(self, name): pass
    def onStart(self): pass
    def onStartFunction(self, name): pass

class KittenWorkDecompiler:

    def __init__(self, workInfo:dict, compiledWork:dict) -> None:
        self.workInfo:dict = workInfo
        self.work:dict = compiledWork

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

    def getActor(self, actorID:str) -> dict:
        # 获取角色或场景信息
        theatre: dict = self.work["theatre"]
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

def block_test():
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

if False:
    block_test()

def work_test():
    test_txt = """{
    "version": 16,
    "application_version": "3.8.17",
    "work_type": "KITTEN",
    "width": 620,
    "height": 900,
    "type": 1,
    "project_name": "春风得意-5",
    "theatre": {
        "current_entity": "aafed029-7038-4f39-a000-f33497a21390",
        "current_scene": "b5e60282-a2d1-478b-802d-a30e77d67e6b",
        "scenes_order": [
            "b5e60282-a2d1-478b-802d-a30e77d67e6b"
        ],
        "scenes": {
            "b5e60282-a2d1-478b-802d-a30e77d67e6b": {
                "id": "b5e60282-a2d1-478b-802d-a30e77d67e6b",
                "current_style_id": "75bde55d-e11c-4fa3-87c9-dd6d7da53fd3",
                "name": "背景",
                "styles": [
                    "75bde55d-e11c-4fa3-87c9-dd6d7da53fd3"
                ],
                "actors": [
                    "aafed029-7038-4f39-a000-f33497a21390"
                ],
                "x": 0,
                "y": 0,
                "scale": 100,
                "rotation": 0,
                "rotation_type": 0,
                "draggable": false,
                "visible": true,
                "screen_name": "屏幕",
                "workspace_offset": {
                    "x": 100,
                    "y": 50
                }
            }
        },
        "actors": {
            "aafed029-7038-4f39-a000-f33497a21390": {
                "id": "aafed029-7038-4f39-a000-f33497a21390",
                "current_style_id": "01033c29-f6d5-442a-a9db-db3ee9637075",
                "name": "新角色",
                "styles": [
                    "01033c29-f6d5-442a-a9db-db3ee9637075"
                ],
                "x": 0,
                "y": 0,
                "scale": 100,
                "rotation": 0,
                "rotation_type": 0,
                "draggable": false,
                "visible": true,
                "lock": false,
                "workspace_offset": {
                    "x": 206,
                    "y": 132
                }
            }
        },
        "videos": {},
        "styles": {
            "75bde55d-e11c-4fa3-87c9-dd6d7da53fd3": {
                "id": "75bde55d-e11c-4fa3-87c9-dd6d7da53fd3",
                "name": "春风得意",
                "rotate_center": {
                    "x": 0,
                    "y": 0
                },
                "pivot": {
                    "x": 0,
                    "y": 0
                },
                "url": "https://static.codemao.cn/kitten/BJ2dhh8MU",
                "cdn_url": "https://static.codemao.cn/kitten/BJ2dhh8MU"
            },
            "01033c29-f6d5-442a-a9db-db3ee9637075": {
                "id": "01033c29-f6d5-442a-a9db-db3ee9637075",
                "name": "新角色",
                "rotate_center": {
                    "x": 0,
                    "y": 0
                },
                "url": "https://creation.bcmcdn.com/120/kitten/d2ViXzIwMDJfODE2MDgxMDYxXzBfMTc4MTMyNTA3NjE2OF8wZDJjYjAxOQ==",
                "cdn_url": "https://creation.bcmcdn.com/120/kitten/d2ViXzIwMDJfODE2MDgxMDYxXzBfMTc4MTMyNTA3NjE2OF8wZDJjYjAxOQ=="
            }
        },
        "style_collections": {}
    },
    "variables": {
        "3ee108a2-79e2-4aa9-8db0-f26352952380": {
            "id": "3ee108a2-79e2-4aa9-8db0-f26352952380",
            "type": "any",
            "is_global": false,
            "scale": 1,
            "visible": true,
            "theme": "common",
            "value": 0,
            "name": "my_value1",
            "offset": {
                "x": 0,
                "y": 0
            },
            "current_entity": "aafed029-7038-4f39-a000-f33497a21390",
            "position": {
                "x": 10,
                "y": 10
            }
        }
    },
    "variable_order": [
        "3ee108a2-79e2-4aa9-8db0-f26352952380"
    ],
    "cloud_variables": {},
    "audio": {
        "0ba8b9d3-715c-467f-8598-97f9b21827bd": {
            "id": "0ba8b9d3-715c-467f-8598-97f9b21827bd",
            "name": "爱心",
            "effects": [],
            "playback_rate": 1,
            "volume": 1,
            "cdn_url": "https://static.codemao.cn/kitten/material_060918_cn/sound/1_sound_effect/34闪亮04.mp3",
            "url": "https://static.codemao.cn/kitten/material_060918_cn/sound/1_sound_effect/34闪亮04.mp3"
        },
        "74ea05ef-f1cb-47ac-846b-404d00c07b75": {
            "id": "74ea05ef-f1cb-47ac-846b-404d00c07b75",
            "name": "春日出游",
            "effects": [],
            "playback_rate": 1,
            "volume": 1,
            "cdn_url": "https://static.codemao.cn/kitten/ryb42bOGU.audio/mp3",
            "url": "https://static.codemao.cn/kitten/ryb42bOGU.audio/mp3"
        }
    },
    "audio_order": [
        "74ea05ef-f1cb-47ac-846b-404d00c07b75",
        "0ba8b9d3-715c-467f-8598-97f9b21827bd"
    ],
    "matrix": {},
    "models": {},
    "toolbox": {
        "block_ai_classification": false,
        "block_ai_game": false,
        "block_hardware_arduino": false,
        "block_hardware_weeemake": false,
        "block_hardware_microbit": false,
        "block_hardware_ideali": false,
        "block_hardware_ideali_asr": false,
        "block_hardware_ideali_smartcar": false,
        "block_hardware_grovezero": false,
        "cloud_variable": false,
        "cloud_list": false,
        "advanced": false,
        "camera": false,
        "video": false,
        "wood": false,
        "cognitive": false,
        "ai_lab": false,
        "physics": false
    },
    "hardware_type": "",
    "is_partial": false,
    "compile_result": [
        {
            "id": "b5e60282-a2d1-478b-802d-a30e77d67e6b",
            "procedures": {},
            "compiled_block_map": {}
        },
        {
            "id": "aafed029-7038-4f39-a000-f33497a21390",
            "procedures": {},
            "compiled_block_map": {
                "RPZP5Dcp7fS6MlhmlQLc": {
                    "params": {},
                    "kind": "domain_block",
                    "type": "start_on_click",
                    "id": "RPZP5Dcp7fS6MlhmlQLc",
                    "next_block": {
                        "params": {},
                        "kind": "repeat_forever",
                        "type": "repeat_forever",
                        "id": "N1HcY1OEnjiHBMIhHPNu",
                        "child_block": [
                            {
                                "params": {},
                                "kind": "controls_if",
                                "type": "controls_if",
                                "id": "dIQA0cl6wcLUG11U7BZY",
                                "child_block": [
                                    {
                                        "params": {},
                                        "kind": "domain_block",
                                        "type": "self_next_style",
                                        "id": "rB1obtMq0MZ0IYN8DZTU",
                                        "child_block": [],
                                        "first_evaluation": true,
                                        "done_evaluating": false,
                                        "output_type": 0,
                                        "disabled": false,
                                        "conditions": [],
                                        "procedure_name": "",
                                        "times_left": 0
                                    },
                                    {
                                        "params": {
                                            "time": {
                                                "params": {
                                                    "NUM": "0"
                                                },
                                                "kind": "domain_block",
                                                "type": "math_number",
                                                "id": "W3syZzqTEb0ocQSS0KSd",
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
                                        "type": "wait",
                                        "id": "sjJC00tNQiKa883W8M4b",
                                        "child_block": [],
                                        "first_evaluation": true,
                                        "done_evaluating": false,
                                        "output_type": 0,
                                        "disabled": false,
                                        "conditions": [],
                                        "procedure_name": "",
                                        "times_left": 0
                                    },
                                    {
                                        "params": {
                                            "color": "#cc66cc"
                                        },
                                        "kind": "domain_block",
                                        "type": "self_set_pen_color",
                                        "id": "3TaMO346r7t8QgPs8UIr",
                                        "child_block": [],
                                        "first_evaluation": true,
                                        "done_evaluating": false,
                                        "output_type": 0,
                                        "disabled": false,
                                        "conditions": [],
                                        "procedure_name": "",
                                        "times_left": 0
                                    },
                                    {
                                        "params": {
                                            "steps": {
                                                "params": {
                                                    "NUM": "10"
                                                },
                                                "kind": "domain_block",
                                                "type": "math_number",
                                                "id": "nd3S6ct23nMrgsgSQQMT",
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
                                        "type": "self_go_forward",
                                        "id": "IRiVBIA1NAAaTDyLxph4",
                                        "child_block": [],
                                        "first_evaluation": true,
                                        "done_evaluating": false,
                                        "output_type": 0,
                                        "disabled": false,
                                        "conditions": [],
                                        "procedure_name": "",
                                        "times_left": 0
                                    }
                                ],
                                "first_evaluation": true,
                                "done_evaluating": false,
                                "output_type": 0,
                                "disabled": false,
                                "conditions": [
                                    {
                                        "params": {
                                            "BOOL": "TRUE"
                                        },
                                        "kind": "domain_block",
                                        "type": "logic_boolean",
                                        "id": "rkuI1moKQ9G6uvNgYIG5",
                                        "child_block": [],
                                        "first_evaluation": true,
                                        "done_evaluating": false,
                                        "output_type": 2,
                                        "disabled": false,
                                        "conditions": [],
                                        "procedure_name": "",
                                        "times_left": 0
                                    },
                                    {
                                        "params": {
                                            "BOOL": "TRUE"
                                        },
                                        "kind": "domain_block",
                                        "type": "logic_boolean",
                                        "id": "sllWUlb2LIh4g1OJB8T1",
                                        "child_block": [],
                                        "first_evaluation": true,
                                        "done_evaluating": false,
                                        "output_type": 2,
                                        "disabled": false,
                                        "conditions": [],
                                        "procedure_name": "",
                                        "times_left": 0
                                    },
                                    {
                                        "params": {
                                            "BOOL": "TRUE"
                                        },
                                        "kind": "domain_block",
                                        "type": "logic_boolean",
                                        "id": "Xb6n8AJcNv1EYmeiHPOr",
                                        "child_block": [],
                                        "first_evaluation": true,
                                        "done_evaluating": false,
                                        "output_type": 2,
                                        "disabled": false,
                                        "conditions": [],
                                        "procedure_name": "",
                                        "times_left": 0
                                    }
                                ],
                                "procedure_name": "",
                                "times_left": 0
                            }
                        ],
                        "first_evaluation": true,
                        "done_evaluating": false,
                        "output_type": 0,
                        "disabled": false,
                        "conditions": [],
                        "procedure_name": "",
                        "times_left": 0
                    },
                    "child_block": [],
                    "first_evaluation": true,
                    "done_evaluating": false,
                    "output_type": 0,
                    "disabled": false,
                    "conditions": [],
                    "procedure_name": "",
                    "times_left": 0
                }
            }
        }
    ],
    "ai_lab": {}
}"""

    compiled_work = json.loads(test_txt)
    decompiler = KittenWorkDecompiler({"name": "测试作品"}, compiled_work)
    decompiled_work = decompiler.start()
    with open("decompiled_work.json", "w", encoding="utf-8") as f:
        json.dump(decompiled_work, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    # 测试反编译器
    work_test()
