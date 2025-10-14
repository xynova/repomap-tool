"""
Test file with relative imports.
"""

from ..parent import ParentClass, parent_function
from ..parent.child import ChildClass, child_function
from ..parent.child.grandchild import GrandChildClass
from ...grandparent import GrandParentClass
from ...grandparent.parent import ParentClass as GParentClass
from ..sibling import SiblingClass
from ..sibling.cousin import CousinClass
from ...uncle import UncleClass
from ...aunt import AuntClass
from ..nephew import NephewClass
from ..niece import NieceClass
from ...grandmother import GrandmotherClass
from ...grandfather import GrandfatherClass
from ..brother import BrotherClass
from ..sister import SisterClass
from ...cousin import CousinClass as GCousinClass
from ...nephew import NephewClass as GNephewClass
from ...niece import NieceClass as GNieceClass
from ...uncle import UncleClass as GUncleClass
from ...aunt import AuntClass as GAuntClass
from ...grandmother import GrandmotherClass as GGrandmotherClass
from ...grandfather import GrandfatherClass as GGrandfatherClass
from ...brother import BrotherClass as GBrotherClass
from ...sister import SisterClass as GSisterClass
