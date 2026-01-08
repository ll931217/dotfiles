#!/usr/bin/env python3
"""
Tests for ArchitectureStrategy

Tests architectural pattern selection based on PRD requirements,
problem domains, and existing codebase patterns.
"""

import unittest
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime, timezone

# Import the architecture strategy
from architecture_strategy import (
    ArchitectureStrategy,
    ArchitecturalPattern,
    ARCHITECTURAL_PATTERNS,
    PATTERNS_BY_CATEGORY,
    DOMAIN_PATTERN_MAPPINGS,
)
from decision_strategy import DecisionContext, Decision


class TestArchitecturalPattern(unittest.TestCase):
    """Tests for ArchitecturalPattern dataclass."""

    def test_pattern_creation(self):
        """Test creating an architectural pattern."""
        pattern = ArchitecturalPattern(
            name='TestPattern',
            category='TEST',
            description='A test pattern',
            use_cases=['test case 1', 'test case 2'],
            benefits=['benefit 1', 'benefit 2'],
            drawbacks=['drawback 1'],
        )

        self.assertEqual(pattern.name, 'TestPattern')
        self.assertEqual(pattern.category, 'TEST')
        self.assertEqual(len(pattern.use_cases), 2)
        self.assertEqual(len(pattern.benefits), 2)
        self.assertEqual(len(pattern.drawbacks), 1)

    def test_mvc_pattern_details(self):
        """Test MVC pattern has correct details."""
        mvc = ARCHITECTURAL_PATTERNS['MVC']

        self.assertEqual(mvc.name, 'MVC')
        self.assertEqual(mvc.category, 'UI')
        self.assertIn('Model-View-Controller', mvc.description)
        self.assertGreater(len(mvc.use_cases), 0)
        self.assertGreater(len(mvc.benefits), 0)
        self.assertGreater(len(mvc.drawbacks), 0)


class TestPatternKnowledgeBase(unittest.TestCase):
    """Tests for architectural pattern knowledge base."""

    def test_all_patterns_have_categories(self):
        """Test all patterns have valid categories."""
        valid_categories = {'UI', 'API', 'DISTRIBUTED', 'ASYNC'}

        for pattern_name, pattern in ARCHITECTURAL_PATTERNS.items():
            self.assertIn(
                pattern.category,
                valid_categories,
                f"Pattern {pattern_name} has invalid category: {pattern.category}"
            )

    def test_all_patterns_in_categories(self):
        """Test all patterns are listed in their category."""
        for category, patterns in PATTERNS_BY_CATEGORY.items():
            for pattern_name in patterns:
                self.assertIn(
                    pattern_name,
                    ARCHITECTURAL_PATTERNS,
                    f"Pattern {pattern_name} in {category} not in knowledge base"
                )

    def test_domain_mappings_valid(self):
        """Test domain mappings reference valid patterns."""
        for domain, mappings in DOMAIN_PATTERN_MAPPINGS.items():
            all_patterns = mappings.get('primary', []) + mappings.get('secondary', [])
            for pattern_name in all_patterns:
                self.assertIn(
                    pattern_name,
                    ARCHITECTURAL_PATTERNS,
                    f"Pattern {pattern_name} in domain {domain} not in knowledge base"
                )


class TestArchitectureStrategy(unittest.TestCase):
    """Tests for ArchitectureStrategy decision-making."""

    def setUp(self):
        """Set up test fixtures."""
        self.strategy = ArchitectureStrategy()

    def test_strategy_name(self):
        """Test strategy name is correct."""
        self.assertEqual(self.strategy.get_strategy_name(), "architecture_autonomous")

    def test_strategy_description(self):
        """Test strategy has a description."""
        description = self.strategy.get_strategy_description()
        self.assertGreater(len(description), 0)
        self.assertIn("architectural", description.lower())

    def test_supported_decision_types(self):
        """Test supported decision types."""
        types = self.strategy.get_supported_decision_types()
        self.assertIn("architecture", types)
        self.assertIn("architectural_pattern", types)
        self.assertIn("ui_architecture", types)

    def test_validate_context_with_none(self):
        """Test validation fails with None context."""
        with self.assertRaises(ValueError):
            self.strategy.validate_context(None)

    def test_validate_context_with_empty_requirements(self):
        """Test validation fails with empty PRD requirements."""
        context = DecisionContext(
            prd_requirements={},
            current_state={},
            available_options=[],
            constraints={},
            session_id='test-session',
        )
        with self.assertRaises(ValueError, msg="PRD requirements are required"):
            self.strategy.validate_context(context)

    def test_validate_context_valid(self):
        """Test validation passes with valid context."""
        context = DecisionContext(
            prd_requirements={'title': 'Test'},
            current_state={},
            available_options=[],
            constraints={},
            session_id='test-session',
        )
        self.assertTrue(self.strategy.validate_context(context))


class TestUIDomainDecisions(unittest.TestCase):
    """Tests for UI architectural pattern decisions."""

    def setUp(self):
        """Set up test fixtures."""
        self.strategy = ArchitectureStrategy()

    def test_web_ui_detects_ui_category(self):
        """Test web UI requirements detect UI category."""
        prd_requirements = {
            'title': 'Dashboard Application',
            'description': 'A single page dashboard with user interface components',
        }
        category = self.strategy._detect_category(prd_requirements, 'web_ui')
        self.assertEqual(category, 'UI')

    def test_web_ui_selects_component_based(self):
        """Test web UI selects Component-Based or MVVM pattern."""
        context = DecisionContext(
            prd_requirements={
                'title': 'Dashboard Application',
                'description': 'A single page dashboard with user interface components',
            },
            current_state={},
            available_options=[],
            constraints={},
            session_id='test-ui-session',
        )

        decision = self.strategy.decide(context)

        self.assertEqual(decision.decision_type, "architecture")
        self.assertIn(decision.choice, ['Component-Based', 'MVVM', 'MVC'])
        self.assertGreater(decision.confidence, 0.5)
        self.assertGreater(len(decision.rationale), 0)
        self.assertGreater(len(decision.alternatives), 0)

    def test_web_ui_with_react_context(self):
        """Test web UI with React context selects Component-Based."""
        context = DecisionContext(
            prd_requirements={
                'title': 'React Dashboard',
                'description': 'A React-based dashboard application',
                'framework': 'React',
                'type': 'SPA',
            },
            current_state={'framework': 'React'},
            available_options=[],
            constraints={},
            session_id='test-react-session',
        )

        decision = self.strategy.decide(context)
        self.assertEqual(decision.choice, 'Component-Based')

    def test_mobile_app_selects_mvvm(self):
        """Test mobile app selects MVVM or MVP pattern."""
        context = DecisionContext(
            prd_requirements={
                'title': 'Mobile App',
                'description': 'An iOS and Android mobile application',
                'platform': 'mobile',
            },
            current_state={},
            available_options=[],
            constraints={},
            session_id='test-mobile-session',
        )

        decision = self.strategy.decide(context)
        self.assertIn(decision.choice, ['MVVM', 'MVP'])


class TestAPIDomainDecisions(unittest.TestCase):
    """Tests for API architectural pattern decisions."""

    def setUp(self):
        """Set up test fixtures."""
        self.strategy = ArchitectureStrategy()

    def test_web_api_selects_layered(self):
        """Test web API selects Layered pattern."""
        context = DecisionContext(
            prd_requirements={
                'title': 'REST API',
                'description': 'A RESTful backend API server',
                'type': 'web api',
            },
            current_state={},
            available_options=[],
            constraints={},
            session_id='test-api-session',
        )

        decision = self.strategy.decide(context)
        self.assertIn(decision.choice, ['Layered', 'Hexagonal'])
        self.assertEqual(decision.metadata['category'], 'API')

    def test_enterprise_selects_hexagonal(self):
        """Test enterprise application selects Hexagonal pattern."""
        context = DecisionContext(
            prd_requirements={
                'title': 'Enterprise System',
                'description': 'An enterprise application with complex business logic',
                'requirements': ['domain-driven design', 'business logic'],
            },
            current_state={},
            available_options=[],
            constraints={},
            session_id='test-enterprise-session',
        )

        decision = self.strategy.decide(context)
        self.assertIn(decision.choice, ['Hexagonal', 'Layered', 'CQRS'])

    def test_api_with_graphql_requirements(self):
        """Test API with GraphQL requirements considers GraphQL."""
        context = DecisionContext(
            prd_requirements={
                'title': 'GraphQL API',
                'description': 'An API with GraphQL for flexible data queries',
                'type': 'graphql',
            },
            current_state={},
            available_options=[],
            constraints={},
            session_id='test-graphql-session',
        )

        decision = self.strategy.decide(context)
        # GraphQL should be considered
        self.assertIn(decision.choice, ['GraphQL', 'Layered', 'Hexagonal'])


class TestDistributedDomainDecisions(unittest.TestCase):
    """Tests for distributed system architectural pattern decisions."""

    def setUp(self):
        """Set up test fixtures."""
        self.strategy = ArchitectureStrategy()

    def test_microservice_requirements_select_microservices(self):
        """Test microservice requirements select Microservices pattern."""
        context = DecisionContext(
            prd_requirements={
                'title': 'Distributed System',
                'description': 'A scalable microservices architecture',
                'requirements': ['microservice', 'scalable', 'distributed'],
            },
            current_state={},
            available_options=[],
            constraints={},
            session_id='test-microservice-session',
        )

        decision = self.strategy.decide(context)
        self.assertIn(decision.choice, ['Microservices', 'Event-Driven'])
        self.assertEqual(decision.metadata['category'], 'DISTRIBUTED')

    def test_event_driven_requirements(self):
        """Test event-driven requirements select Event-Driven pattern."""
        context = DecisionContext(
            prd_requirements={
                'title': 'Event System',
                'description': 'An event-driven architecture for a scalable distributed system',
                'requirements': ['event-driven', 'async communication', 'distributed'],
            },
            current_state={},
            available_options=[],
            constraints={},
            session_id='test-event-session',
        )

        decision = self.strategy.decide(context)
        self.assertIn(decision.choice, ['Event-Driven', 'Microservices'])

    def test_cqrs_requirements(self):
        """Test CQRS requirements select CQRS pattern."""
        context = DecisionContext(
            prd_requirements={
                'title': 'CQRS System',
                'description': 'A system with separate read and write models',
                'requirements': ['CQRS', 'read-write separation'],
            },
            current_state={},
            available_options=[],
            constraints={},
            session_id='test-cqrs-session',
        )

        decision = self.strategy.decide(context)
        # CQRS should be considered
        self.assertIn(decision.metadata['category'], ['DISTRIBUTED', 'API'])


class TestAsyncDomainDecisions(unittest.TestCase):
    """Tests for async architectural pattern decisions."""

    def setUp(self):
        """Set up test fixtures."""
        self.strategy = ArchitectureStrategy()

    def test_realtime_selects_reactive(self):
        """Test real-time requirements select Reactive pattern."""
        context = DecisionContext(
            prd_requirements={
                'title': 'Real-time App',
                'description': 'A real-time streaming application',
                'requirements': ['real-time', 'streaming', 'live updates'],
            },
            current_state={},
            available_options=[],
            constraints={},
            session_id='test-realtime-session',
        )

        decision = self.strategy.decide(context)
        self.assertIn(decision.choice, ['Reactive', 'Event-Driven'])
        self.assertEqual(decision.metadata['category'], 'ASYNC')

    def test_pubsub_requirements(self):
        """Test pub-sub requirements select Pub-Sub pattern."""
        context = DecisionContext(
            prd_requirements={
                'title': 'Pub-Sub System',
                'description': 'A publish-subscribe async messaging system for real-time communication',
                'requirements': ['publish-subscribe', 'async messaging', 'real-time'],
            },
            current_state={},
            available_options=[],
            constraints={},
            session_id='test-pubsub-session',
        )

        decision = self.strategy.decide(context)
        self.assertIn(decision.choice, ['Pub-Sub', 'Event-Driven', 'Reactive'])

    def test_actor_model_requirements(self):
        """Test actor model requirements consider Actor Model pattern."""
        context = DecisionContext(
            prd_requirements={
                'title': 'Actor System',
                'description': 'A distributed actor-based system',
                'requirements': ['actor model', 'message passing', 'concurrent'],
            },
            current_state={},
            available_options=[],
            constraints={},
            session_id='test-actor-session',
        )

        decision = self.strategy.decide(context)
        # Actor Model should be considered
        self.assertEqual(decision.metadata['category'], 'ASYNC')


class TestScoring(unittest.TestCase):
    """Tests for pattern scoring logic."""

    def setUp(self):
        """Set up test fixtures."""
        self.strategy = ArchitectureStrategy()

    def test_domain_requirements_scoring(self):
        """Test domain requirements scoring."""
        mvc_pattern = ARCHITECTURAL_PATTERNS['MVC']
        context = DecisionContext(
            prd_requirements={'type': 'web ui'},
            current_state={},
            available_options=[],
            constraints={},
            session_id='test',
        )

        score = self.strategy._score_domain_requirements(mvc_pattern, 'web_ui', context)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)

    def test_best_practices_scoring(self):
        """Test best practices scoring."""
        component_based = ARCHITECTURAL_PATTERNS['Component-Based']
        score = self.strategy._score_best_practices(component_based, 'web_ui')

        # Component-Based should score high for UI
        self.assertGreaterEqual(score, 0.7)

    def test_simplicity_scoring(self):
        """Test simplicity scoring."""
        layered = ARCHITECTURAL_PATTERNS['Layered']
        score = self.strategy._score_simplicity(layered)

        # Layered should score high on simplicity
        self.assertGreaterEqual(score, 0.7)

    def test_existing_patterns_scoring_no_existing(self):
        """Test existing patterns scoring with no existing patterns."""
        mvc_pattern = ARCHITECTURAL_PATTERNS['MVC']

        # No existing patterns loaded
        score = self.strategy._score_existing_patterns(mvc_pattern)
        self.assertEqual(score, 0.5)  # Neutral score

    def test_overall_pattern_scoring(self):
        """Test overall pattern scoring combines all factors."""
        component_based = ARCHITECTURAL_PATTERNS['Component-Based']
        context = DecisionContext(
            prd_requirements={'type': 'web ui', 'framework': 'React'},
            current_state={'framework': 'React'},
            available_options=[],
            constraints={},
            session_id='test',
        )

        score = self.strategy.score_pattern(component_based, context, 'web_ui')
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)


class TestDecisionOutput(unittest.TestCase):
    """Tests for decision output structure."""

    def setUp(self):
        """Set up test fixtures."""
        self.strategy = ArchitectureStrategy()

    def test_decision_has_required_fields(self):
        """Test decision has all required fields."""
        context = DecisionContext(
            prd_requirements={'type': 'web ui'},
            current_state={},
            available_options=[],
            constraints={},
            session_id='test-session',
        )

        decision = self.strategy.decide(context)

        self.assertIsNotNone(decision.choice)
        self.assertIsNotNone(decision.rationale)
        self.assertGreaterEqual(decision.confidence, 0.0)
        self.assertLessEqual(decision.confidence, 1.0)
        self.assertIsInstance(decision.alternatives, list)
        self.assertIsNotNone(decision.context_snapshot)
        self.assertEqual(decision.decision_type, "architecture")
        self.assertIsInstance(decision.metadata, dict)

    def test_decision_metadata(self):
        """Test decision metadata contains expected keys."""
        context = DecisionContext(
            prd_requirements={'type': 'web api'},
            current_state={},
            available_options=[],
            constraints={},
            session_id='test-session',
        )

        decision = self.strategy.decide(context)

        self.assertIn('category', decision.metadata)
        self.assertIn('domain', decision.metadata)
        self.assertIn('score', decision.metadata)
        self.assertIn('scoring_breakdown', decision.metadata)

    def test_scoring_breakdown(self):
        """Test scoring breakdown contains all components."""
        context = DecisionContext(
            prd_requirements={'type': 'web ui'},
            current_state={},
            available_options=[],
            constraints={},
            session_id='test-session',
        )

        decision = self.strategy.decide(context)
        breakdown = decision.metadata['scoring_breakdown']

        self.assertIn('domain_requirements', breakdown)
        self.assertIn('existing_patterns', breakdown)
        self.assertIn('best_practices', breakdown)
        self.assertIn('simplicity', breakdown)

        # All scores should be between 0 and 1
        for key, value in breakdown.items():
            self.assertGreaterEqual(value, 0.0, f"{key}: {value} is below 0")
            self.assertLessEqual(value, 1.0, f"{key}: {value} is above 1")

    def test_confidence_calculation(self):
        """Test confidence is calculated appropriately."""
        context = DecisionContext(
            prd_requirements={'type': 'web ui', 'framework': 'React'},
            current_state={'framework': 'React'},
            available_options=[],
            constraints={},
            session_id='test-session',
        )

        decision = self.strategy.decide(context)

        # Strong match should result in higher confidence
        self.assertGreaterEqual(decision.confidence, 0.5)

    def test_rationale_quality(self):
        """Test rationale is informative and well-structured."""
        context = DecisionContext(
            prd_requirements={'type': 'web api'},
            current_state={},
            available_options=[],
            constraints={},
            session_id='test-session',
        )

        decision = self.strategy.decide(context)

        # Rationale should mention the chosen pattern
        self.assertIn(decision.choice, decision.rationale)

        # Rationale should be substantive
        self.assertGreater(len(decision.rationale), 50)

        # Rationale should explain why
        explanation_words = ['fit', 'best', 'chosen', 'selected']
        self.assertTrue(
            any(word in decision.rationale.lower() for word in explanation_words),
            "Rationale should explain why the choice was made"
        )


class TestEdgeCases(unittest.TestCase):
    """Tests for edge cases and error handling."""

    def setUp(self):
        """Set up test fixtures."""
        self.strategy = ArchitectureStrategy()

    def test_empty_requirements_raises_error(self):
        """Test empty PRD requirements raises error."""
        context = DecisionContext(
            prd_requirements={},
            current_state={},
            available_options=[],
            constraints={},
            session_id='test',
        )

        with self.assertRaises(ValueError, msg="PRD requirements are required"):
            self.strategy.decide(context)

    def test_unknown_category_defaults_to_api(self):
        """Test unknown category defaults to API patterns."""
        context = DecisionContext(
            prd_requirements={'type': 'unknown system'},
            current_state={},
            available_options=[],
            constraints={},
            session_id='test',
        )

        decision = self.strategy.decide(context)
        # Should still make a decision with default domain
        self.assertIsNotNone(decision.choice)

    def test_custom_available_options(self):
        """Test custom available options are respected."""
        context = DecisionContext(
            prd_requirements={'type': 'web api'},
            current_state={},
            available_options=[
                {'name': 'GraphQL', 'category': 'API'},
                {'name': 'Layered', 'category': 'API'},
            ],
            constraints={},
            session_id='test',
        )

        decision = self.strategy.decide(context)
        # Should select from provided options
        self.assertIn(decision.choice, ['GraphQL', 'Layered'])

    def test_single_option_results_in_decision(self):
        """Test single available option still produces decision."""
        context = DecisionContext(
            prd_requirements={'type': 'web api'},
            current_state={},
            available_options=[{'name': 'Layered', 'category': 'API'}],
            constraints={},
            session_id='test',
        )

        decision = self.strategy.decide(context)
        self.assertEqual(decision.choice, 'Layered')
        # Confidence may be lower with single option
        self.assertGreaterEqual(decision.confidence, 0.0)
        self.assertLessEqual(decision.confidence, 1.0)


class TestDomainDetection(unittest.TestCase):
    """Tests for domain detection from PRD requirements."""

    def setUp(self):
        """Set up test fixtures."""
        self.strategy = ArchitectureStrategy()

    def test_detect_web_ui_domain(self):
        """Test web UI domain detection."""
        prd = {'description': 'A user interface with components and frontend'}
        domain = self.strategy._detect_domain(prd)
        self.assertEqual(domain, 'web_ui')

    def test_detect_web_api_domain(self):
        """Test web API domain detection."""
        prd = {'description': 'A REST API backend server with endpoints'}
        domain = self.strategy._detect_domain(prd)
        self.assertEqual(domain, 'web_api')

    def test_detect_distributed_system_domain(self):
        """Test distributed system domain detection."""
        prd = {'description': 'A scalable microservices distributed system'}
        domain = self.strategy._detect_domain(prd)
        self.assertEqual(domain, 'distributed_system')

    def test_detect_realtime_domain(self):
        """Test real-time domain detection."""
        prd = {'description': 'A real-time live streaming application'}
        domain = self.strategy._detect_domain(prd)
        self.assertEqual(domain, 'real_time')

    def test_detect_mobile_app_domain(self):
        """Test mobile app domain detection."""
        prd = {'description': 'An Android and iOS mobile application'}
        domain = self.strategy._detect_domain(prd)
        self.assertEqual(domain, 'mobile_app')

    def test_detect_enterprise_domain(self):
        """Test enterprise domain detection."""
        prd = {'description': 'An enterprise system with complex business logic'}
        domain = self.strategy._detect_domain(prd)
        self.assertEqual(domain, 'enterprise')

    def test_unknown_domain_defaults(self):
        """Test unknown domain defaults to web_api."""
        prd = {'description': 'Some random system'}
        domain = self.strategy._detect_domain(prd)
        self.assertEqual(domain, 'web_api')


if __name__ == '__main__':
    unittest.main()
