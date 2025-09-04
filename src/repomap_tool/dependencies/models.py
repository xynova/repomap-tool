"""
Data models for dependency analysis.

This module defines the core data structures used throughout the dependency analysis system.
"""

from typing import List, Dict, Set, Optional, Any, Tuple
from pathlib import Path
from pydantic import BaseModel, Field
from enum import Enum


class ImportType(str, Enum):
    """Types of import statements."""
    ABSOLUTE = "absolute"
    RELATIVE = "relative"
    EXTERNAL = "external"
    UNKNOWN = "unknown"


class Import(BaseModel):
    """Represents a single import statement."""
    
    module: str = Field(description="Module name being imported")
    alias: Optional[str] = Field(default=None, description="Alias if imported as something else")
    is_relative: bool = Field(description="Whether this is a relative import")
    import_type: ImportType = Field(default=ImportType.UNKNOWN, description="Type of import")
    resolved_path: Optional[str] = Field(default=None, description="Resolved absolute file path")
    line_number: Optional[int] = Field(default=None, description="Line number of import")
    symbols: List[str] = Field(default_factory=list, description="Specific symbols imported")
    
    def __str__(self) -> str:
        if self.alias:
            return f"import {self.module} as {self.alias}"
        elif self.symbols:
            return f"from {self.module} import {', '.join(self.symbols)}"
        else:
            return f"import {self.module}"


class FileImports(BaseModel):
    """Represents all imports for a single file."""
    
    file_path: str = Field(description="Path to the file")
    imports: List[Import] = Field(default_factory=list, description="List of imports in this file")
    language: Optional[str] = Field(default=None, description="Programming language of the file")
    total_imports: int = Field(default=0, description="Total number of import statements")
    
    def model_post_init(self, __context):
        self.total_imports = len(self.imports)
    
    def get_absolute_imports(self) -> List[Import]:
        """Get only absolute imports."""
        return [imp for imp in self.imports if not imp.is_relative]
    
    def get_relative_imports(self) -> List[Import]:
        """Get only relative imports."""
        return [imp for imp in self.imports if imp.is_relative]
    
    def get_external_imports(self) -> List[Import]:
        """Get only external imports."""
        return [imp for imp in self.imports if imp.import_type == ImportType.EXTERNAL]


class ProjectImports(BaseModel):
    """Represents all imports found in a project."""
    
    project_path: str = Field(description="Path to the project root")
    file_imports: Dict[str, FileImports] = Field(default_factory=dict, description="Imports by file path")
    total_files: int = Field(default=0, description="Total number of files analyzed")
    total_imports: int = Field(default=0, description="Total number of import statements")
    language_stats: Dict[str, int] = Field(default_factory=dict, description="Count of files by language")
    
    def __len__(self) -> int:
        """Return the number of files with imports."""
        return len(self.file_imports)
        
    def __getitem__(self, key: str) -> FileImports:
        """Allow subscripting to access file_imports."""
        return self.file_imports[key]
        
    def get_files_importing(self, module_name: str) -> List[str]:
        """Get a list of files that import a specific module."""
        importing_files = []
        for file_path, file_imports in self.file_imports.items():
            for imp in file_imports.imports:
                if imp.module == module_name:
                    importing_files.append(file_path)
        return importing_files
    
    def model_post_init(self, __context):
        self.total_files = len(self.file_imports)
        self.total_imports = sum(len(fi.imports) for fi in self.file_imports.values())
        
        # Count files by language
        for file_imports in self.file_imports.values():
            lang = file_imports.language or "unknown"
            self.language_stats[lang] = self.language_stats.get(lang, 0) + 1
    
    def get_file_by_path(self, file_path: str) -> Optional[FileImports]:
        """Get imports for a specific file."""
        return self.file_imports.get(file_path)
    
    def get_all_imported_modules(self) -> Set[str]:
        """Get all unique modules that are imported."""
        modules = set()
        for file_imports in self.file_imports.values():
            for imp in file_imports.imports:
                modules.add(imp.module)
        return modules


class FunctionCall(BaseModel):
    """Represents a function call."""
    
    caller: str = Field(description="Name of the calling function")
    callee: str = Field(description="Name of the called function")
    file_path: str = Field(description="File where the call occurs")
    line_number: int = Field(description="Line number of the call")
    is_method_call: bool = Field(default=False, description="Whether this is a method call")
    object_name: Optional[str] = Field(default=None, description="Object name for method calls")
    resolved_callee: Optional[str] = Field(default=None, description="Resolved function path if cross-file")
    
    def __str__(self) -> str:
        if self.is_method_call and self.object_name:
            return f"{self.object_name}.{self.callee}()"
        else:
            return f"{self.callee}()"


class CallGraph(BaseModel):
    """Represents the function call graph for a project."""
    
    project_path: str = Field(description="Path to the project root")
    function_calls: List[FunctionCall] = Field(default_factory=list, description="All function calls")
    function_locations: Dict[str, str] = Field(default_factory=dict, description="File location of each function")
    call_relationships: Dict[str, List[str]] = Field(default_factory=dict, description="Functions called by each function")
    total_calls: int = Field(default=0, description="Total number of function calls")
    
    def model_post_init(self, __context):
        self.total_calls = len(self.function_calls)
        
        # Build call relationships
        for call in self.function_calls:
            if call.caller not in self.call_relationships:
                self.call_relationships[call.caller] = []
            self.call_relationships[call.caller].append(call.callee)
    
    def get_functions_called_by(self, function_name: str) -> List[str]:
        """Get all functions called by a specific function."""
        return self.call_relationships.get(function_name, [])
    
    def get_functions_calling(self, function_name: str) -> List[str]:
        """Get all functions that call a specific function."""
        callers = []
        for caller, callees in self.call_relationships.items():
            if function_name in callees:
                callers.append(caller)
        return callers


class DependencyNode(BaseModel):
    """Represents a node in the dependency graph."""
    
    file_path: str = Field(description="Path to the file")
    imports: List[str] = Field(default_factory=list, description="Files this file imports")
    imported_by: List[str] = Field(default_factory=list, description="Files that import this file")
    functions: List[str] = Field(default_factory=list, description="Functions defined in this file")
    classes: List[str] = Field(default_factory=list, description="Classes defined in this file")
    language: Optional[str] = Field(default=None, description="Programming language")
    centrality_score: Optional[float] = Field(default=None, description="Centrality importance score")
    dependency_depth: Optional[int] = Field(default=None, description="Depth in dependency chain")
    structural_info: Dict[str, Any] = Field(default_factory=dict, description="Additional structural information")
    
    def get_total_dependencies(self) -> int:
        """Get total number of dependencies (imports + imported_by)."""
        return len(self.imports) + len(self.imported_by)
    
    def is_leaf_node(self) -> bool:
        """Check if this is a leaf node (no outgoing dependencies)."""
        return len(self.imports) == 0
    
    def is_root_node(self) -> bool:
        """Check if this is a root node (no incoming dependencies)."""
        return len(self.imported_by) == 0


class ImpactReport(BaseModel):
    """Report on the impact of potential changes to files."""
    
    changed_files: List[str] = Field(description="Files that are being changed")
    affected_files: List[str] = Field(description="Files that would be affected")
    risk_score: float = Field(ge=0.0, le=1.0, description="Overall risk score (0=low, 1=high)")
    direct_impact: List[str] = Field(default_factory=list, description="Files directly affected")
    transitive_impact: List[str] = Field(default_factory=list, description="Files transitively affected")
    breaking_change_potential: Dict[str, str] = Field(default_factory=dict, description="Risk level for each changed file")
    suggested_tests: List[str] = Field(default_factory=list, description="Test files that should be run")
    impact_summary: str = Field(description="Human-readable impact summary")
    
    def get_total_impact_count(self) -> int:
        """Get total number of affected files."""
        return len(self.affected_files)
    
    def get_high_risk_files(self) -> List[str]:
        """Get files with high breaking change potential."""
        return [f for f, risk in self.breaking_change_potential.items() if risk == "HIGH"]


class BreakingChangeRisk(str, Enum):
    """Risk levels for breaking changes."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RefactoringOpportunity(BaseModel):
    """Represents an opportunity for refactoring."""
    
    file_path: str = Field(description="File that could benefit from refactoring")
    opportunity_type: str = Field(description="Type of refactoring opportunity")
    description: str = Field(description="Description of the opportunity")
    priority: str = Field(description="Priority level (LOW, MEDIUM, HIGH)")
    affected_files: List[str] = Field(default_factory=list, description="Files that would be affected")
    estimated_effort: str = Field(description="Estimated effort required")
    benefits: List[str] = Field(default_factory=list, description="Benefits of refactoring")
