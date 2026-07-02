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
class KittenWorkDecompiler():
    def __init__(self, workInfo, compiledWork) -> None:
        self.workInfo = workInfo
        self.work = compiledWork
        self.functions = {}
        
        

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