"""
Impact analyzer for dependency analysis.

This module analyzes the potential impact of changes to files, providing risk
assessment and recommendations for testing and mitigation.
"""

import logging
from ..core.logging_service import get_logger
from typing import List, Dict, Set, Optional, Any
from pathlib import Path

from .models import ImpactReport, BreakingChangeRisk
from .advanced_dependency_graph import AdvancedDependencyGraph

logger = get_logger(__name__)


class ImpactAnalyzer:
    """Analyzes the potential impact of changes to files in the dependency graph."""

    def __init__(self, dependency_graph: AdvancedDependencyGraph):
        """Initialize the impact analyzer.

        Args:
            dependency_graph: AdvancedDependencyGraph instance to analyze
        """
        self.graph = dependency_graph
        self.cache: Dict[str, ImpactReport] = {}
        self.cache_enabled = True

        logger.debug("ImpactAnalyzer initialized")

    def analyze_change_impact(self, changed_files: List[str]) -> ImpactReport:
        """Analyze the potential impact of changes to files.

        Args:
            changed_files: List of file paths that are being changed

        Returns:
            ImpactReport with comprehensive impact analysis
        """
        if not changed_files:
            return ImpactReport(
                changed_files=[],
                affected_files=[],
                risk_score=0.0,
                impact_summary="No files specified for change",
            )

        logger.info(f"Analyzing impact of changes to {len(changed_files)} files")

        try:
            # Find all affected files
            affected_files = self._find_affected_files(changed_files)

            # Calculate risk scores
            risk_score = self._calculate_overall_risk_score(
                changed_files, affected_files
            )

            # Assess breaking change potential
            breaking_change_potential = self._assess_breaking_change_potential(
                changed_files
            )

            # Suggest test files
            suggested_tests = self._suggest_test_files(changed_files, affected_files)

            # Generate impact summary
            impact_summary = self._generate_impact_summary(
                changed_files, affected_files, risk_score, breaking_change_potential
            )

            # Create impact report
            impact_report = ImpactReport(
                changed_files=changed_files,
                affected_files=list(affected_files),
                risk_score=risk_score,
                direct_impact=changed_files,
                transitive_impact=list(affected_files - set(changed_files)),
                breaking_change_potential=breaking_change_potential,
                suggested_tests=suggested_tests,
                impact_summary=impact_summary,
            )

            # Cache the result
            if self.cache_enabled:
                cache_key = self._get_cache_key(changed_files)
                self.cache[cache_key] = impact_report

            logger.info(
                f"Impact analysis complete: {len(affected_files)} files affected, risk score: {risk_score:.2f}"
            )
            return impact_report

        except Exception as e:
            logger.error(f"Error analyzing change impact: {e}")
            return ImpactReport(
                changed_files=changed_files,
                affected_files=[],
                risk_score=1.0,  # High risk if analysis fails
                impact_summary=f"Error during impact analysis: {e}",
            )

    def _find_affected_files(self, changed_files: List[str]) -> Set[str]:
        """Find all files that would be affected by changes to the specified files.

        Args:
            changed_files: List of files being changed

        Returns:
            Set of all affected file paths
        """
        affected_files = set(changed_files)

        try:
            for changed_file in changed_files:
                if changed_file in self.graph.nodes:
                    # Get transitive dependents (files that depend on this file)
                    transitive_dependents = self.graph.calculate_transitive_dependents(
                        changed_file
                    )
                    affected_files.update(transitive_dependents)

                    # Also consider function call dependencies
                    if self.graph.call_graph:
                        function_dependents = self.graph._get_file_function_dependents(
                            changed_file
                        )
                        for func_name in function_dependents:
                            if func_name in self.graph.call_graph.function_locations:
                                dependent_file = (
                                    self.graph.call_graph.function_locations[func_name]
                                )
                                if dependent_file != changed_file:
                                    affected_files.add(dependent_file)

            return affected_files

        except Exception as e:
            logger.error(f"Error finding affected files: {e}")
            return set(changed_files)

    def _calculate_overall_risk_score(
        self, changed_files: List[str], affected_files: Set[str]
    ) -> float:
        """Calculate the overall risk score for the changes.

        Args:
            changed_files: List of files being changed
            affected_files: Set of all affected files

        Returns:
            Risk score between 0.0 (low risk) and 1.0 (high risk)
        """
        try:
            if not changed_files:
                return 0.0

            # Base risk factors
            base_risk = 0.3

            # Risk based on number of changed files
            file_count_risk = min(len(changed_files) * 0.1, 0.3)

            # Risk based on number of affected files
            affected_count_risk = min(len(affected_files) * 0.05, 0.4)

            # Risk based on centrality of changed files
            centrality_risk = self._calculate_centrality_risk(changed_files)

            # Risk based on breaking change potential
            breaking_change_risk = self._calculate_breaking_change_risk(changed_files)

            # Combine risk factors
            total_risk = (
                base_risk
                + file_count_risk
                + affected_count_risk
                + centrality_risk
                + breaking_change_risk
            )

            # Cap at 1.0
            return min(total_risk, 1.0)

        except Exception as e:
            logger.error(f"Error calculating risk score: {e}")
            return 0.8  # High risk if calculation fails

    def _calculate_centrality_risk(self, changed_files: List[str]) -> float:
        """Calculate risk based on the centrality of changed files.

        Args:
            changed_files: List of files being changed

        Returns:
            Centrality risk score between 0.0 and 0.3
        """
        try:
            centrality_risk = 0.0

            for changed_file in changed_files:
                if changed_file in self.graph.nodes:
                    # Check if file is a dependency hotspot
                    if changed_file in self.graph.identify_hotspots():
                        centrality_risk += 0.15

                    # Check dependency depth
                    depth = self.graph.calculate_dependency_depth(changed_file)
                    if depth > 3:
                        centrality_risk += 0.1

                    # Check stability metric
                    stability = self.graph.calculate_stability_metric(changed_file)
                    if stability > 0.7:  # Very stable file
                        centrality_risk += 0.1

            return min(centrality_risk, 0.3)

        except Exception as e:
            logger.error(f"Error calculating centrality risk: {e}")
            return 0.1

    def _calculate_breaking_change_risk(self, changed_files: List[str]) -> float:
        """Calculate risk based on potential for breaking changes.

        Args:
            changed_files: List of files being changed

        Returns:
            Breaking change risk score between 0.0 and 0.2
        """
        try:
            breaking_change_risk = 0.0

            for changed_file in changed_files:
                if changed_file in self.graph.nodes:
                    # Check if file has many dependents
                    dependents = self.graph.get_dependents(changed_file)
                    if len(dependents) > 5:
                        breaking_change_risk += 0.1

                    # Check if file is part of circular dependencies
                    cycles = self.graph.find_cycles()
                    for cycle in cycles:
                        if changed_file in cycle:
                            breaking_change_risk += 0.1
                            break

            return min(breaking_change_risk, 0.2)

        except Exception as e:
            logger.error(f"Error calculating breaking change risk: {e}")
            return 0.1

    def _assess_breaking_change_potential(
        self, changed_files: List[str]
    ) -> Dict[str, str]:
        """Assess the potential for breaking changes in each changed file.

        Args:
            changed_files: List of files being changed

        Returns:
            Dictionary mapping file paths to risk levels
        """
        try:
            breaking_change_potential = {}

            for changed_file in changed_files:
                if changed_file not in self.graph.nodes:
                    breaking_change_potential[changed_file] = "UNKNOWN"
                    continue

                risk_level = "LOW"

                # Check number of dependents
                dependents = self.graph.get_dependents(changed_file)
                if len(dependents) > 10:
                    risk_level = "HIGH"
                elif len(dependents) > 5:
                    risk_level = "MEDIUM"

                # Check if it's a hotspot
                if changed_file in self.graph.identify_hotspots():
                    risk_level = "HIGH"

                # Check circular dependencies
                cycles = self.graph.find_cycles()
                for cycle in cycles:
                    if changed_file in cycle:
                        risk_level = "HIGH"
                        break

                # Check function call dependencies
                if self.graph.call_graph:
                    func_dependents = self.graph._get_file_function_dependents(
                        changed_file
                    )
                    if len(func_dependents) > 8:
                        risk_level = "HIGH"
                    elif len(func_dependents) > 4:
                        risk_level = "MEDIUM"

                breaking_change_potential[changed_file] = risk_level

            return breaking_change_potential

        except Exception as e:
            logger.error(f"Error assessing breaking change potential: {e}")
            return {file: "UNKNOWN" for file in changed_files}

    def _suggest_test_files(
        self, changed_files: List[str], affected_files: Set[str]
    ) -> List[str]:
        """Suggest test files that should be run to validate the changes.

        Args:
            changed_files: List of files being changed
            affected_files: Set of all affected files

        Returns:
            List of suggested test file paths
        """
        try:
            suggested_tests = set()

            # Add tests for changed files
            for changed_file in changed_files:
                test_file = self._find_test_file(changed_file)
                if test_file:
                    suggested_tests.add(test_file)

            # Add tests for high-risk affected files
            for affected_file in affected_files:
                if affected_file in self.graph.nodes:
                    # Check if this is a high-risk file
                    dependents = self.graph.get_dependents(affected_file)
                    if len(dependents) > 3:
                        test_file = self._find_test_file(affected_file)
                        if test_file:
                            suggested_tests.add(test_file)

            return list(suggested_tests)

        except Exception as e:
            logger.error(f"Error suggesting test files: {e}")
            return []

    def _find_test_file(self, source_file: str) -> Optional[str]:
        """Find the corresponding test file for a source file.

        Args:
            source_file: Path to the source file

        Returns:
            Path to the test file if found, None otherwise
        """
        try:
            source_path = Path(source_file)

            # Common test file patterns
            test_patterns = [
                f"test_{source_path.stem}.py",
                f"{source_path.stem}_test.py",
                f"test_{source_path.stem}.js",
                f"{source_path.stem}.test.js",
                f"test_{source_path.stem}.ts",
                f"{source_path.stem}.test.ts",
            ]

            # Look in common test directories
            test_dirs = [
                source_path.parent / "tests",
                source_path.parent / "test",
                source_path.parent.parent / "tests",
                source_path.parent.parent / "test",
            ]

            for test_dir in test_dirs:
                if test_dir.exists() and test_dir.is_dir():
                    for pattern in test_patterns:
                        test_file = test_dir / pattern
                        if test_file.exists():
                            return str(test_file)

            return None

        except Exception as e:
            logger.debug(f"Error finding test file for {source_file}: {e}")
            return None

    def _generate_impact_summary(
        self,
        changed_files: List[str],
        affected_files: Set[str],
        risk_score: float,
        breaking_change_potential: Dict[str, str],
    ) -> str:
        """Generate a human-readable impact summary.

        Args:
            changed_files: List of files being changed
            affected_files: Set of all affected files
            risk_score: Overall risk score
            breaking_change_potential: Breaking change risk for each file

        Returns:
            Human-readable impact summary
        """
        try:
            summary_parts = []

            # Overall impact
            summary_parts.append(
                f"Changes to {len(changed_files)} file(s) will affect {len(affected_files)} file(s) total."
            )

            # Risk assessment
            if risk_score > 0.8:
                risk_level = "HIGH"
            elif risk_score > 0.5:
                risk_level = "MEDIUM"
            else:
                risk_level = "LOW"

            summary_parts.append(
                f"Overall risk level: {risk_level} (score: {risk_score:.2f})"
            )

            # Breaking change assessment
            high_risk_files = [
                f for f, risk in breaking_change_potential.items() if risk == "HIGH"
            ]
            if high_risk_files:
                summary_parts.append(
                    f"High breaking change potential in {len(high_risk_files)} file(s)."
                )

            # Recommendations
            if risk_score > 0.7:
                summary_parts.append(
                    "Recommend comprehensive testing and careful review."
                )
            elif risk_score > 0.4:
                summary_parts.append("Recommend focused testing of affected areas.")
            else:
                summary_parts.append(
                    "Low risk changes, standard testing should suffice."
                )

            return " ".join(summary_parts)

        except Exception as e:
            logger.error(f"Error generating impact summary: {e}")
            return "Error generating impact summary"

    def _get_cache_key(self, changed_files: List[str]) -> str:
        """Generate a cache key for the changed files.

        Args:
            changed_files: List of file paths

        Returns:
            Cache key string
        """
        # Sort files for consistent cache keys
        sorted_files = sorted(changed_files)
        return "|".join(sorted_files)

    def get_cached_impact_report(
        self, changed_files: List[str]
    ) -> Optional[ImpactReport]:
        """Get a cached impact report if available.

        Args:
            changed_files: List of file paths being changed

        Returns:
            Cached ImpactReport if available, None otherwise
        """
        if not self.cache_enabled:
            return None

        cache_key = self._get_cache_key(changed_files)
        return self.cache.get(cache_key)

    def clear_cache(self) -> None:
        """Clear the impact analysis cache."""
        self.cache.clear()
        logger.info("Impact analysis cache cleared")

    def disable_cache(self) -> None:
        """Disable caching for impact analysis."""
        self.cache_enabled = False
        logger.info("Impact analysis caching disabled")

    def enable_cache(self) -> None:
        """Enable caching for impact analysis."""
        self.cache_enabled = True
        logger.info("Impact analysis caching enabled")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get statistics about the impact analysis cache.

        Returns:
            Dictionary with cache statistics
        """
        return {
            "cache_enabled": self.cache_enabled,
            "cache_size": len(self.cache),
            "cached_analyses": list(self.cache.keys()),
        }
