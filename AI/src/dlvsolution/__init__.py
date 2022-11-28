from languages.asp.asp_mapper import ASPMapper

from AI.src.dlvsolution.helpers import Edge, InputBomb, InputNode, InputHorizontal, InputVertical, \
    AtLeast3Adjacent, Swap

ASPMapper.get_instance().register_class(Swap)
ASPMapper.get_instance().register_class(Edge)
ASPMapper.get_instance().register_class(InputNode)
ASPMapper.get_instance().register_class(InputBomb)
ASPMapper.get_instance().register_class(InputHorizontal)
ASPMapper.get_instance().register_class(InputVertical)
ASPMapper.get_instance().register_class(AtLeast3Adjacent)
