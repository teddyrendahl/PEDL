"""
PEDL uses a Qt inspired layout system. Not all of the feature set has been
implemented, but the basic concept is the same as well as much of the API.
There are three major layout types, :class:`.HBoxLayout`, :class:`.VBoxLayout`
and finally :class:`.StackLayout`. The two former layout types are borrowed
directly from Qt, you simply add widgets and they are aligned and placed in
such a way that they are either in a vertical or horizontal line. Finally,
because EDM widgets tend to need to be stacked on top of each other, the
:class:`.StackLayout` can be used to handle these kind of situations.

Far more complex layouts are possible by using :meth:`Layout.addLayout` to
nest layouts inside of each other. This allows the user to maintain a master
layout composed of widgets and smaller layouts that can then be applied to a
widget by using the :meth:`.Designer.setLayout`
"""
####################
# Standard Library #
####################
import copy
import logging

####################
#    Third Party   #
####################

####################
#     Package      #
####################
from .widget  import Widget, PedlObject
from .choices import AlignmentChoice
from .utils   import pedlproperty

logger = logging.getLogger(__name__)

class Layout(PedlObject):
    """
    Parameters
    ----------
    x : int, optional
        Starting X position of the layout

    y : int, optional
        Starting Y position of the layout
    """
#    x = copy.copy(PedlObject.x)
#    y = copy.copy(PedlObject.y)

    spacing   = pedlproperty(int, default=5,  doc='Spacing between widgets')
    alignment = pedlproperty(AlignmentChoice, doc='Alignment of Layout')

    def __init__(self, **kwargs):
        self.widgets = list()
        super().__init__(**kwargs)


    @property
    def w(self):
        """
        Width of the layout
        """
        if not self.widgets:
            return 0

        return (max([w.right for w in self.widgets]) - self.x)


    @property
    def h(self):
        """
        Height of the layout
        """
        if not self.widgets:
            return 0

        return (max([w.bottom for w in self.widgets]) - self.y)


    @property
    def x(self):
        if not self.widgets:
            return 0

        return min([w.x for w in self.widgets])


    @property
    def y(self):
        if not self.widgets:
            return 0

        return min([w.y for w in self.widgets])


    @x.setter
    def x(self, x):
        if self.widgets:
            #Find left most widget
            shift = x - self.x
            for w in self.widgets:
                w.x += shift


    @y.setter
    def y(self, y):
        if self.widgets:
            #Find left most widget
            shift = y - self.y
            for w in self.widgets:
                w.y += shift


    @alignment.callback
    def alignment(self):
        self.shuffle()
    
    @spacing.callback
    def spacing(self):
        self.shuffle()


    @property
    def count(self):
        """
        Number of items in layout
        """
        return len(self.widgets)


    def addWidget(self, widget):
        """
        Add a Widget to the Layout

        Parameters
        ----------
        widget : :class:`.Widget`
            EDM Widget
        """
        self.insertWidget(self.count, widget)


    def insertWidget(self, index, widget):
        """
        Insert a widget into the layout
        """
        if not isinstance(widget, Widget):
            raise TypeError('Must be an EDM Widget')

        #Note as child widget
        widget.parent = self

        #Add to widget
        self.widgets.insert(index, widget)

        #Redraw
        self.shuffle()
       

    def addLayout(self, layout):
        """
        Add a child layout

        Parameters
        ----------
        layout : :class:`.Layout`
            Nested layout to add
        """
        self.insertLayout(self.count, layout)

    
    def insertLayout(self, index, layout):
        """
        """
        if not isinstance(layout, Layout):
            raise TypeError('Must be an EDM Layout')

        if not len(layout.widgets) > 0:
            raise ValueError("Can not add an empty Layout")

        #Note as child layout
        layout.parent = self

        #Add to Widget
        self.widgets.insert(index, layout)

        #Redraw
        self.shuffle()


    def shuffle(self):
        """
        Rearrange all of the  child widgets
        """
        logger.debug("Rearranged layout {}".format(self))

        if self.parent:
            logger.debug("Triggered rearrangement of parent layout {}"
                         "".format(self.parent))
            self.parent.shuffle()


class HBoxLayout(Layout):
    """
    Layout for horizontally placed widgets
    """
    alignment = copy.copy(Layout.alignment)
    alignment.default = AlignmentChoice.Top

    def shuffle(self):
        next_widget = self.x

        if self.alignment not in (AlignmentChoice.Top,
                                  AlignmentChoice.Bottom,
                                  AlignmentChoice.Center):
            logger.warning('Unsupported alignment {} HBoxLayout'
                           ''.format(self.alignment))

        for widget in self.widgets:
            #Align Widget
            if self.alignment == AlignmentChoice.Top:
                widget.y = self.y

            elif self.alignment == AlignmentChoice.Bottom:
                widget.placeBottom(self.widgets[0].bottom)

            elif self.alignment == AlignmentChoice.Center:
                widget.recenter(y=self.widgets[0].center[1])

            #Place Widget
            widget.x = next_widget
            next_widget += widget.w + self.spacing
        
        #Rearrange parent layout
        super().shuffle()


class VBoxLayout(Layout):
    """
    Layout for vertically placed widgets
    """
    alignment = copy.copy(Layout.alignment)
    alignment.default = AlignmentChoice.Left

    def shuffle(self):
        next_widget = self.y
        
        if self.alignment not in (AlignmentChoice.Left,
                                  AlignmentChoice.Right,
                                  AlignmentChoice.Center):
            logger.warning('Unsupported alignment {} for VBoxLayout'
                           ''.format(self.alignment))

        for widget in self.widgets:
            if self.alignment == AlignmentChoice.Left:
                widget.x = self.x

            elif self.alignment == AlignmentChoice.Right:
                widget.placeRight(self.widgets[0].right)

            elif self.alignment == AlignmentChoice.Center:
                widget.recenter(x=self.widgets[0].center[0])

            widget.y = next_widget
            next_widget += widget.h + self.spacing

        #Rearrange parent layout
        super().shuffle()

class StackedLayout(Layout):
    """
    Layout for widgets placed on top of each other

    The alignment specification works slightly differently in the case of the
    stack layout, because there are two possible axes to specify. This
    means that you may enter an list of Alignment options to be more
    specific in your widget placement. By default, no option is given for
    an axis, the layout assumes you want the widgets centered

    Example
    -------
    .. code::

        #Centered on both axes
        layout.alignment = AlignmentChoice.Center

        #Top-Right Corner
        layout.alignment = [AlignmentChoice.Top, AlignmentChoice.Right]

        #Left-Side Aligned, Centered in Vertical
        layout.alignment = [AlignmentChoice.Left]
    """
    alignment = copy.copy(Layout.alignment)
    alignment.default = [AlignmentChoice.Center]

    spacing   = copy.copy(Layout.spacing)
    spacing.default = None

    @alignment.setter
    def alignment(self, align):

        try:
            align = [AlignmentChoice(a) for a in align]

        except TypeError:
            align = [AlignmentChoice(align)]

        if align != self.attributes.get('alignment'):
            self.attributes['alignment'] = align
            self.shuffle()


    @spacing.setter
    def spacing(self, spacing):
        if spacing:
            raise ValueError('Stacked Layout can not have non-zero spacing')

        self.attributes['spacing'] = spacing

    def shuffle(self):
        ld = self.widgets[0]

        for w in self.widgets:

            #Place X axis
            if AlignmentChoice.Left in self.alignment:
                w.x = ld.x

            elif AlignmentChoice.Right in self.alignment:
                w.placeRight(x=ld.right)

            else:
                w.recenter(x=ld.center[0])

            #Place Y axis
            if AlignmentChoice.Top in self.alignment:
                w.y = ld.y

            elif AlignmentChoice.Bottom in self.alignment:
                w.placeBottom(y=ld.bottom)

            else:
                w.recenter(y=ld.center[1])

        #Rearrange parent layout
        super().shuffle()
