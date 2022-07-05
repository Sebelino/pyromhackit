from dataclasses import dataclass
from typing import Tuple

from pyromhackit.semantics.semantics import Semantics


@dataclass(frozen=True)
class SearchResult:
    """ A set of semantics suggested by a Finder. """
    semantics_set: Tuple[Semantics]  # Order doesn't matter though
