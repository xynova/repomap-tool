"""Code analysis data models for tree-sitter parsing."""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any, Set
from enum import Enum
from pydantic import Field


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
    rel_fname: Optional[str] = None  # Relative file path (for compatibility)
    comment: Optional[str] = None  # Associated comment

    def __hash__(self) -> int:
        return hash((self.name, self.kind, self.file, self.line, self.column))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CodeTag):
            return NotImplemented
        return (
            self.name == other.name
            and self.kind == other.kind
            and self.file == other.file
            and self.line == other.line
            and self.column == other.column
        )


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
    symbols: Optional[List[str]] = None


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
    callee: Optional[str] = None
    is_method_call: bool = False
    object_name: Optional[str] = None
    resolved_callee: Optional[str] = None


@dataclass
@dataclass
class CallGraph:
    """Function call graph."""

    function_calls: List[FunctionCall]
    function_locations: Dict[str, str]
    relationships: Optional[Dict[str, List[str]]] = None


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
    functions: Optional[List[str]] = None
    structural_info: Optional[Dict[str, Any]] = None

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
    changed_files: Optional[List[str]] = None
    risk_score: Optional[float] = None
    impact_summary: Optional[str] = None
    direct_impact: Optional[List[str]] = None
    transitive_impact: Optional[List[str]] = None
    breaking_change_potential: Optional[bool] = None
    suggested_tests: Optional[List[str]] = None


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
    defined_functions: List[str] = Field(default_factory=list)
    defined_classes: List[str] = Field(default_factory=list)
    defined_methods: List[str] = Field(default_factory=list)
    function_calls: List[FunctionCall] = Field(default_factory=list)
    used_variables: List[str] = Field(default_factory=list)
    line_count: int = Field(..., ge=0)
    analysis_errors: List[str] = Field(default_factory=list)
    used_classes: Optional[List[str]] = None


@dataclass
class CrossFileRelationship:
    """Relationship between files."""

    source_file: str
    target_file: str
    relationship_type: str
    strength: float
    line_number: Optional[int] = None
    details: Optional[str] = None


@dataclass
class FileImpactAnalysis:
    """File impact analysis result."""

    file_path: str
    impact_score: float
    affected_files: List[str]
    risk_factors: List[str]
    mitigation_suggestions: List[str]
    dependency_chain_length: Optional[int] = None
    risk_level: Optional[str] = None
    impact_categories: Optional[List[str]] = None
    suggested_tests: Optional[List[str]] = None
    direct_dependencies: Optional[List[Dict[str, Any]]] = None
    reverse_dependencies: Optional[List[Dict[str, Any]]] = None
    function_call_analysis: Optional[List[Dict[str, Any]]] = None
    structural_impact: Optional[Dict[str, Any]] = None
    risk_assessment: Optional[Dict[str, Any]] = None


@dataclass
class FileCentralityAnalysis:
    """File centrality analysis result."""

    file_path: str
    centrality_score: float
    rank: int
    total_files: int
    dependency_analysis: Dict[str, Any]
    function_call_analysis: Dict[str, Any]
    structural_impact: Dict[str, Any]
    centrality_breakdown: Optional[Dict[str, Any]] = None
