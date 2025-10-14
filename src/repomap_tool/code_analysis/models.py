"""Code analysis data models for tree-sitter parsing."""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any, Set
from enum import Enum


@dataclass
class CodeTag:
    """Universal code tag from tree-sitter parsing."""

    name: str  # Identifier name
    kind: str  # Tag kind (def, class, import, etc.)
    file: str  # Absolute file path
    line: int  # 1-based line number
    column: int = 0  # Column position
    end_line: Optional[int] = None
    end_column: Optional[int] = None
    rel_fname: Optional[str] = None  # Relative file path (for aider compat)


class AnalysisFormat(str, Enum):
    """Format options for analysis output."""

    TEXT = "text"
    JSON = "json"
    TABLE = "table"


class ImportType(str, Enum):
    """Types of import statements."""

    STANDARD = "standard"
    RELATIVE = "relative"
    ABSOLUTE = "absolute"
    THIRD_PARTY = "third_party"
    EXTERNAL = "external"


@dataclass
class Import:
    """Import statement information."""

    module: str
    alias: Optional[str] = None
    file_path: str = ""
    line_number: int = 0
    import_type: ImportType = ImportType.STANDARD
    is_relative: bool = False
    resolved_path: Optional[str] = None


@dataclass
class FileImports:
    """Import information for a single file."""

    file_path: str
    imports: List[Import]
    language: Optional[str] = None

    @property
    def total_imports(self) -> int:
        """Total number of imports in this file."""
        return len(self.imports)


@dataclass
class ProjectImports:
    """Import information for the entire project."""

    files: Dict[str, FileImports]
    project_path: Optional[str] = None
    file_imports: Optional[Dict[str, FileImports]] = None
    total_files: Optional[int] = None

    @property
    def total_imports(self) -> int:
        """Total number of imports across all files."""
        return sum(len(file_imports.imports) for file_imports in self.files.values())


@dataclass
class FunctionCall:
    """Function call information."""

    name: str
    file_path: str
    line_number: int
    arguments: Optional[List[str]] = None
    caller: Optional[str] = None


@dataclass
class CallGraph:
    """Function call graph."""

    calls: List[FunctionCall]
    relationships: Dict[str, List[str]]


@dataclass
class DependencyNode:
    """Dependency graph node."""

    file_path: str
    language: str
    dependencies: Optional[List[str]] = None
    dependents: Optional[List[str]] = None
    imports: Optional[List[str]] = None
    imported_by: Optional[List[str]] = None
    centrality_score: float = 0.0

    def __post_init__(self) -> None:
        if self.dependencies is None:
            self.dependencies = []
        if self.dependents is None:
            self.dependents = []
        if self.imports is None:
            self.imports = []
        if self.imported_by is None:
            self.imported_by = []


@dataclass
class ImpactReport:
    """Impact analysis report."""

    changed_file: str
    affected_files: List[str]
    impact_score: float
    risk_level: str


@dataclass
class BreakingChangeRisk:
    """Breaking change risk assessment."""

    file_path: str
    risk_level: str
    risk_factors: List[str]
    mitigation_suggestions: List[str]


@dataclass
class RefactoringOpportunity:
    """Refactoring opportunity identification."""

    file_path: str
    opportunity_type: str
    description: str
    potential_impact: str


@dataclass
class FileAnalysisResult:
    """Result of file analysis."""

    file_path: str
    imports: List[Import]
    defined_functions: List[str]
    defined_classes: List[str]
    function_calls: List[FunctionCall]
    used_variables: List[str]
    line_count: int
    analysis_errors: List[str]
    used_classes: Optional[List[str]] = None


@dataclass
class CrossFileRelationship:
    """Relationship between files."""

    source_file: str
    target_file: str
    relationship_type: str
    strength: float


@dataclass
class FileImpactAnalysis:
    """File impact analysis result."""

    file_path: str
    impact_score: float
    affected_files: List[str]
    risk_factors: List[str]
    mitigation_suggestions: List[str]


@dataclass
class FileCentralityAnalysis:
    """File centrality analysis result."""

    file_path: str
    centrality_score: float
    rank: int
    total_files: int
    dependency_analysis: Dict[str, Any]
    function_call_analysis: Dict[str, Any]
    centrality_breakdown: Dict[str, Any]
    structural_impact: Dict[str, Any]
