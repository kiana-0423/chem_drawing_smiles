"""Graphics items used by the molecule editor scene."""

from __future__ import annotations

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QPainterPath, QPainterPathStroker, QPen
from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsItem, QGraphicsLineItem, QGraphicsSimpleTextItem

from chem_editor.core.models import Atom, Bond

ATOM_RADIUS = 18.0


class AtomItem(QGraphicsEllipseItem):
    """Selectable atom node item."""

    def __init__(self, atom: Atom) -> None:
        super().__init__(-ATOM_RADIUS, -ATOM_RADIUS, ATOM_RADIUS * 2, ATOM_RADIUS * 2)
        self.atom_id = atom.atom_id
        self.element = atom.element
        self.formal_charge = atom.formal_charge
        self.setPos(atom.x, atom.y)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)
        self.setZValue(2)

        self._label = QGraphicsSimpleTextItem(self._label_text(atom), self)
        self._label.setBrush(QColor("#0f172a"))
        self._center_label()
        self.update_style()

    def update_style(self) -> None:
        """Refresh the atom appearance based on selection state."""
        if self.isSelected():
            pen = QPen(QColor("#0f766e"), 3)
            brush = QColor("#ccfbf1")
        else:
            pen = QPen(QColor("#0f172a"), 2)
            brush = QColor("#ffffff")

        self.setPen(pen)
        self.setBrush(brush)

    def position(self) -> QPointF:
        """Return the scene position for the atom."""
        return self.scenePos()

    def _center_label(self) -> None:
        label_rect = self._label.boundingRect()
        self._label.setPos(-label_rect.width() / 2, -label_rect.height() / 2)

    @staticmethod
    def _label_text(atom: Atom) -> str:
        if atom.formal_charge == 0:
            return atom.element

        sign = "+" if atom.formal_charge > 0 else "-"
        magnitude = abs(atom.formal_charge)
        suffix = sign if magnitude == 1 else f"{sign}{magnitude}"
        return f"{atom.element}{suffix}"


class BondItem(QGraphicsLineItem):
    """Selectable bond edge item."""

    def __init__(self, bond: Bond, start_point: QPointF, end_point: QPointF) -> None:
        super().__init__()
        self.bond_id = bond.bond_id
        self.atom_a_id = bond.atom_a_id
        self.atom_b_id = bond.atom_b_id
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)
        self.setZValue(1)
        self.update_geometry(start_point, end_point)
        self.update_style()

    def update_geometry(self, start_point: QPointF, end_point: QPointF) -> None:
        """Update the displayed bond line."""
        self.setLine(start_point.x(), start_point.y(), end_point.x(), end_point.y())

    def update_style(self) -> None:
        """Refresh the bond appearance based on selection state."""
        if self.isSelected():
            pen = QPen(QColor("#0f766e"), 5)
        else:
            pen = QPen(QColor("#334155"), 4)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        self.setPen(pen)

    def shape(self) -> QPainterPath:
        """Widen the clickable area so bonds are easy to select."""
        path = QPainterPath()
        path.moveTo(self.line().p1())
        path.lineTo(self.line().p2())
        stroker = QPainterPathStroker()
        stroker.setWidth(14)
        return stroker.createStroke(path)
