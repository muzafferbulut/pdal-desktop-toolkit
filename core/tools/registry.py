from typing import Dict, Type
from core.tools.base import BaseTool

class ToolRegistry:
    _tools: Dict[str, Type[BaseTool]] = {}

    @classmethod
    def register(cls, tool_cls:Type[BaseTool]):
        cls._tools[tool_cls.name] = tool_cls
        return tool_cls
    
    @classmethod
    def get_tool(cls, name:str) -> Type[BaseTool]:
        tool = cls._tools.get(name)
        if not tool:
            raise ValueError(f"Tool not found: {name}")
        return tool
    
    @classmethod
    def get_all_tools(cls):
        return cls._tools
    

# decoratörü kısaltmak için kullanılan helper func
def register_tool(cls):
    return ToolRegistry.register(cls)