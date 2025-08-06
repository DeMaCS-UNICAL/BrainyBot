# Release Candidate da testare
import math
from languages.predicate import Predicate

SQRT3 = math.sqrt(3)


def axial_from_pixel(x, y, size, offset, orientation):
    """Converti coordinate cartesiane in coordinate assiali (q,r)."""
    x = (x - offset[0]) / size
    y = (y - offset[1]) / size
    if orientation == "pointy-top":
        q = (SQRT3 / 3) * x - (1 / 3) * y
        r = (2 / 3) * y
    else:  # flat-top
        q = (2 / 3) * x
        r = (-1 / 3) * x + (SQRT3 / 3) * y
    return q, r


def cube_round(q, r):
    """Arrotonda coordinate assiali (q, r) al centro dell’esagono più vicino."""
    x = q
    z = r
    y = -x - z
    rx = round(x)
    ry = round(y)
    rz = round(z)

    x_diff = abs(rx - x)
    y_diff = abs(ry - y)
    z_diff = abs(rz - z)

    if x_diff > y_diff and x_diff > z_diff:
        rx = -ry - rz
    elif y_diff > z_diff:
        ry = -rx - rz
    else:
        rz = -rx - ry
    return rx, rz  # restituisce q, r arrotondati


class ObjectHexCell(Predicate):
    predicate_name = "hex_cell"

    def __init__(self, idx, q, r, value, x, y):
        Predicate.__init__(self, [("id", int), ("q", int), ("r", int), ("value", str)])
        self.__id = idx
        self.__q = q
        self.__r = r
        self.__value = value if value is not None else ""
        self.x = x
        self.y = y

    def get_id(self):
        return self.__id

    def get_q(self):
        return self.__q

    def get_r(self):
        return self.__r

    def get_value(self):
        return self.__value

    def __eq__(self, other):
        return (
            isinstance(other, ObjectHexCell)
            and self.__id == other.__id
            and self.__q == other.__q
            and self.__r == other.__r
            and self.__value == other.__value
        )


class ObjectHexMatrix:
    """Gestisce una matrice esagonale di oggetti."""

    def __init__(self, objects, orientation="auto", offset=(0, 0), size=1.0):
        """
        objects: iterable di dict/oggetti con campi x, y, value
        orientation: 'pointy-top', 'flat-top' o 'auto'
        offset: origine (x0, y0)
        size: raggio dell’esagono in pixel
        """
        self.offset = offset
        self.size = size
        self.objects = list(objects)
        self.orientation = (
            self._guess_orientation() if orientation == "auto" else orientation
        )
        self.cells = self._to_cells()

    def _guess_orientation(self):
        """Scegli l’orientamento con l’errore medio più basso rispetto ai centri teorici."""
        score = {}
        for orientation in ("pointy-top", "flat-top"):
            err = 0.0
            for obj in self.objects:
                q, r = axial_from_pixel(obj.x, obj.y, self.size, self.offset, orientation)
                rq, rr = cube_round(q, r)
                cx, cy = self._pixel_from_axial(rq, rr, orientation)
                dx = obj.x - cx
                dy = obj.y - cy
                err += dx * dx + dy * dy
            score[orientation] = err
        return min(score, key=score.get)

    def _pixel_from_axial(self, q, r, orientation):
        """Centro dell’esagono (q, r) in coordinate cartesiane."""
        if orientation == "pointy-top":
            x = self.size * (SQRT3 * q + SQRT3 / 2 * r) + self.offset[0]
            y = self.size * (3 / 2 * r) + self.offset[1]
        else:  # flat-top
            x = self.size * (3 / 2 * q) + self.offset[0]
            y = self.size * (SQRT3 / 2 * q + SQRT3 * r) + self.offset[1]
        return x, y

    def _to_cells(self):
        """Converte gli oggetti in celle esagonali."""
        cells = []
        for idx, obj in enumerate(self.objects):
            q, r = axial_from_pixel(obj.x, obj.y, self.size, self.offset, self.orientation)
            q, r = cube_round(q, r)
            x, y = self._pixel_from_axial(q, r, self.orientation)
            cells.append(ObjectHexCell(idx, q, r, obj.value, x, y))
        return cells

    def get_cells(self):
        return self.cells
