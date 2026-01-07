#!/usr/bin/env python3
"""
Unit tests for Architecture Pattern Matcher

Tests complexity assessment, pattern matching, and scalability evaluation.
"""

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add scripts directory to path
scripts_dir = Path(__file__).parent
sys.path.insert(0, str(scripts_dir))

from architecture_pattern_matcher import (
    ArchitecturePatternMatcher,
    ComplexityAssessor,
    ScalabilityEvaluator,
    PATTERN_KNOWLEDGE_BASE,
)


class TestComplexityAssessor(unittest.TestCase):
    """Test complexity assessment from natural language descriptions."""

    def test_low_complexity_simple(self):
        """Test low complexity detection with simple keywords."""
        description = "Implement simple password validation"
        complexity = ComplexityAssessor.assess(description)
        self.assertEqual(complexity, 'low')

    def test_low_complexity_format(self):
        """Test low complexity with format/conversion keywords."""
        description = "Convert date format to ISO"
        complexity = ComplexityAssessor.assess(description)
        self.assertEqual(complexity, 'low')

    def test_medium_complexity_crud(self):
        """Test medium complexity with CRUD operations."""
        description = "Create user management API endpoints"
        complexity = ComplexityAssessor.assess(description)
        self.assertEqual(complexity, 'medium')

    def test_medium_complexity_business_logic(self):
        """Test medium complexity with business logic."""
        description = "Process order with business rules"
        complexity = ComplexityAssessor.assess(description)
        self.assertEqual(complexity, 'medium')

    def test_high_complexity_orchestration(self):
        """Test high complexity with orchestration keywords."""
        description = "Orchestrate complex workflow across multiple services"
        complexity = ComplexityAssessor.assess(description)
        self.assertEqual(complexity, 'high')

    def test_high_complexity_async(self):
        """Test high complexity with async/event-driven keywords."""
        description = "Implement real-time async event processing pipeline"
        complexity = ComplexityAssessor.assess(description)
        self.assertEqual(complexity, 'high')

    def test_default_complexity(self):
        """Test default complexity when no keywords match."""
        description = "Implement feature"
        complexity = ComplexityAssessor.assess(description)
        self.assertEqual(complexity, 'medium')


class TestScalabilityEvaluator(unittest.TestCase):
    """Test scalability evaluation for patterns."""

    def test_simple_function_scalability(self):
        """Test scalability assessment for simple function."""
        scalability = ScalabilityEvaluator.evaluate('simple_function')
        self.assertIn('high', scalability)
        self.assertIn('stateless', scalability)

    def test_service_layer_scalability(self):
        """Test scalability assessment for service layer."""
        scalability = ScalabilityEvaluator.evaluate('service_layer')
        self.assertIn('medium', scalability)
        self.assertIn('dependency', scalability)

    def test_repository_scalability(self):
        """Test scalability assessment for repository."""
        scalability = ScalabilityEvaluator.evaluate('repository')
        self.assertIn('medium', scalability)
        self.assertIn('abstraction', scalability)

    def test_factory_scalability(self):
        """Test scalability assessment for factory."""
        scalability = ScalabilityEvaluator.evaluate('factory')
        self.assertIn('high', scalability)

    def test_unknown_pattern_scalability(self):
        """Test scalability assessment for unknown pattern."""
        scalability = ScalabilityEvaluator.evaluate('unknown_pattern')
        self.assertEqual(scalability, 'unknown')


class TestArchitecturePatternMatcher(unittest.TestCase):
    """Test pattern matching logic."""

    def setUp(self):
        """Set up test fixtures."""
        # Use a mock project root
        self.project_root = "/tmp/test_project"
        self.matcher = ArchitecturePatternMatcher(self.project_root)

    @patch('architecture_pattern_matcher.subprocess.run')
    def test_load_existing_patterns_success(self, mock_run):
        """Test loading existing patterns from detect_patterns.py."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps({
                'service-layer': {'total_matches': 5, 'patterns': {'service': 5}},
                'repository': {'total_matches': 3, 'patterns': {'Repository': 3}},
            }),
        )

        matcher = ArchitecturePatternMatcher(self.project_root)
        self.assertIn('service-layer', matcher.existing_patterns)
        self.assertIn('repository', matcher.existing_patterns)

    @patch('architecture_pattern_matcher.subprocess.run')
    def test_load_existing_patterns_failure(self, mock_run):
        """Test handling when detect_patterns.py fails."""
        mock_run.return_value = MagicMock(returncode=1)

        matcher = ArchitecturePatternMatcher(self.project_root)
        self.assertEqual(matcher.existing_patterns, {})

    def test_score_pattern_match_complexity_alignment(self):
        """Test pattern scoring with complexity alignment."""
        # Service layer with medium complexity should score high
        score, rationale = self.matcher._score_pattern_match(
            'service_layer',
            'Implement user registration',
            'medium',
            {},
        )
        self.assertGreater(score, 0)
        self.assertTrue(any('complexity' in r.lower() for r in rationale))

    def test_score_pattern_match_use_when(self):
        """Test pattern scoring with use_when indicators."""
        # Repository for database operations
        score, rationale = self.matcher._score_pattern_match(
            'repository',
            'Create database access layer for user queries',
            'medium',
            {},
        )
        self.assertGreater(score, 0)
        self.assertTrue(any('use case' in r.lower() for r in rationale))

    def test_score_pattern_match_existing_pattern(self):
        """Test pattern scoring with existing patterns."""
        # Mock existing service layer
        self.matcher.existing_patterns = {'service-layer': {'total_matches': 10}}

        score, rationale = self.matcher._score_pattern_match(
            'service_layer',
            'Implement order processing',
            'medium',
            self.matcher.existing_patterns,
        )
        self.assertGreater(score, 0)
        self.assertTrue(any('existing pattern' in r.lower() for r in rationale))

    def test_score_pattern_match_avoid_when(self):
        """Test pattern scoring with avoid_when penalty."""
        # Repository should be avoided for simple queries
        score, rationale = self.matcher._score_pattern_match(
            'repository',
            'Implement simple queries',
            'medium',
            {},
        )
        # Should have reduced score due to avoid_when (contains "simple queries")
        self.assertTrue(any('warning' in r.lower() or 'avoid' in r.lower() for r in rationale))

    def test_match_pattern_simple_validation(self):
        """Test pattern matching for simple validation."""
        result = self.matcher.match_pattern("Implement simple password validation")

        self.assertEqual(result['decision_type'], 'architecture_pattern')
        self.assertIn('decision', result['output'])
        self.assertIn('confidence', result['output'])
        self.assertIn('rationale', result['output'])
        self.assertIn('context', result['output'])
        self.assertEqual(result['output']['context']['complexity'], 'low')

    def test_match_pattern_service_layer(self):
        """Test pattern matching for service layer."""
        result = self.matcher.match_pattern("Implement user registration with email verification")

        self.assertEqual(result['decision_type'], 'architecture_pattern')
        self.assertIn('decision', result['output'])
        self.assertIn('confidence', result['output'])
        self.assertIn('rationale', result['output'])

    def test_match_pattern_repository(self):
        """Test pattern matching for repository."""
        result = self.matcher.match_pattern("Create data access layer for user CRUD operations")

        self.assertEqual(result['decision_type'], 'architecture_pattern')
        self.assertIn('decision', result['output'])

    def test_match_pattern_complexity_override(self):
        """Test complexity override in pattern matching."""
        result = self.matcher.match_pattern("Implement feature", complexity='high')

        self.assertEqual(result['output']['context']['complexity'], 'high')

    def test_match_pattern_no_clear_match(self):
        """Test pattern matching with no clear match."""
        result = self.matcher.match_pattern("xyz")

        self.assertEqual(result['decision_type'], 'architecture_pattern')
        self.assertIn('decision', result['output'])

    @patch('architecture_pattern_matcher.subprocess.run')
    def test_match_pattern_with_existing_patterns(self, mock_run):
        """Test pattern matching considers existing patterns."""
        # Mock existing service layer
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps({
                'service-layer': {'total_matches': 5, 'patterns': {'service': 5}},
            }),
        )

        matcher = ArchitecturePatternMatcher(self.project_root)
        result = matcher.match_pattern("Implement business logic layer")

        # Should mention existing patterns in context
        self.assertIn('service-layer', result['output']['context']['existing_patterns_detected'])


class TestPatternKnowledgeBase(unittest.TestCase):
    """Test the pattern knowledge base structure."""

    def test_all_patterns_have_required_fields(self):
        """Test that all patterns have required fields."""
        required_fields = ['name', 'complexity', 'indicators', 'use_when', 'avoid_when', 'scalability', 'alternatives']

        for pattern_key, pattern_data in PATTERN_KNOWLEDGE_BASE.items():
            for field in required_fields:
                self.assertIn(field, pattern_data, f"Pattern {pattern_key} missing field {field}")

    def test_complexity_values(self):
        """Test that all patterns have valid complexity values."""
        valid_complexities = ['low', 'medium', 'high', 'low-medium']

        for pattern_key, pattern_data in PATTERN_KNOWLEDGE_BASE.items():
            complexity = pattern_data.get('complexity')
            self.assertIn(complexity, valid_complexities, f"Pattern {pattern_key} has invalid complexity")


class TestIntegration(unittest.TestCase):
    """Integration tests for the full workflow."""

    @patch('architecture_pattern_matcher.subprocess.run')
    def test_full_workflow_authentication(self, mock_run):
        """Test full workflow for authentication feature."""
        # Mock existing patterns
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps({
                'service-layer': {'total_matches': 3, 'patterns': {'service': 3}},
            }),
        )

        matcher = ArchitecturePatternMatcher('/tmp/project')
        result = matcher.match_pattern("Implement OAuth authentication for users")

        # Validate output structure
        self.assertEqual(result['decision_type'], 'architecture_pattern')
        self.assertEqual(result['input'], "Implement OAuth authentication for users")
        self.assertIn('decision', result['output'])
        self.assertIn('rationale', result['output'])
        self.assertIn('confidence', result['output'])
        self.assertIn('alternatives', result['output'])
        self.assertIn('context', result['output'])
        self.assertIn('complexity', result['output']['context'])
        self.assertIn('scalability_assessment', result['output']['context'])

    @patch('architecture_pattern_matcher.subprocess.run')
    def test_full_workflow_file_upload(self, mock_run):
        """Test full workflow for file upload feature."""
        mock_run.return_value = MagicMock(returncode=0, stdout=json.dumps({}))

        matcher = ArchitecturePatternMatcher('/tmp/project')
        result = matcher.match_pattern("Implement file upload service with validation")

        # Validate output structure
        self.assertEqual(result['decision_type'], 'architecture_pattern')
        self.assertIn('decision', result['output'])


def run_tests():
    """Run all tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test cases
    suite.addTests(loader.loadTestsFromTestCase(TestComplexityAssessor))
    suite.addTests(loader.loadTestsFromTestCase(TestScalabilityEvaluator))
    suite.addTests(loader.loadTestsFromTestCase(TestArchitecturePatternMatcher))
    suite.addTests(loader.loadTestsFromTestCase(TestPatternKnowledgeBase))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Return exit code
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())
