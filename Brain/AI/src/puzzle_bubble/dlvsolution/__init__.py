from languages.asp.asp_mapper import ASPMapper

from AI.src.puzzle_bubble.dlvsolution.helpers import Bubble,Move, PlayerBubble



ASPMapper.get_instance().register_class(Bubble)
ASPMapper.get_instance().register_class(PlayerBubble)
ASPMapper.get_instance().register_class(Move)