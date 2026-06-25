"""
Integration Testing Script for Multi-Platform Delay Analysis.
Tests GitHub and JIRA adapters, analysis engine, and FAQ generator.
"""

import sys
from datetime import datetime, timedelta
from backend.integrations.github.github_adapter import GitHubAdapter
from backend.integrations.jira.jira_adapter import JiraAdapter
from backend.analysis.semantic_delay_analyzer import SemanticDelayAnalyzer
from backend.analysis.faq_generator import FAQGenerator
from backend.analysis.project_chatbot import ProjectChatbot


def test_github_adapter():
    """Test GitHub adapter (requires valid PAT and repo access)."""
    print("\n" + "="*60)
    print("TEST 1: GitHub Adapter")
    print("="*60)
    
    # Example: octocat/Hello-World (public repo)
    try:
        adapter = GitHubAdapter(
            owner="octocat",
            repo="Hello-World",
            pat_token="YOUR_GITHUB_PAT_HERE"  # Replace with valid token
        )
        
        if not adapter.authenticate():
            print("❌ GitHub authentication failed")
            return False
        
        print("✓ GitHub authentication successful")
        
        platform_data = adapter.execute()
        if not platform_data:
            print("❌ Failed to fetch platform data")
            return False
        
        print(f"✓ Fetched GitHub data:")
        print(f"  - Features (PRs): {len(platform_data.features)}")
        print(f"  - Contributors: {len(platform_data.contributors)}")
        print(f"  - Timeline events: {len(platform_data.timeline_events)}")
        print(f"  - Platform key: {platform_data.platform_key}")
        
        return True
    
    except Exception as e:
        print(f"❌ GitHub adapter error: {e}")
        return False


def test_jira_adapter():
    """Test JIRA adapter (requires valid credentials)."""
    print("\n" + "="*60)
    print("TEST 2: JIRA Adapter")
    print("="*60)
    
    try:
        adapter = JiraAdapter(
            project_key="YOUR_PROJECT_KEY",  # Replace
            domain="YOUR_DOMAIN.atlassian.net",  # Replace
            api_token="YOUR_JIRA_API_TOKEN",  # Replace
            email="YOUR_EMAIL@company.com"  # Replace
        )
        
        if not adapter.authenticate():
            print("❌ JIRA authentication failed")
            return False
        
        print("✓ JIRA authentication successful")
        
        platform_data = adapter.execute()
        if not platform_data:
            print("❌ Failed to fetch platform data")
            return False
        
        print(f"✓ Fetched JIRA data:")
        print(f"  - Issues (Stories): {len(platform_data.features)}")
        print(f"  - Contributors: {len(platform_data.contributors)}")
        print(f"  - Timeline events: {len(platform_data.timeline_events)}")
        print(f"  - Sprints: {len(platform_data.sprints)}")
        print(f"  - Platform key: {platform_data.platform_key}")
        
        return True
    
    except Exception as e:
        print(f"❌ JIRA adapter error: {e}")
        return False


def test_semantic_analyzer():
    """Test semantic delay analyzer with mock data."""
    print("\n" + "="*60)
    print("TEST 3: Semantic Delay Analyzer")
    print("="*60)
    
    try:
        from backend.integrations.core.unified_schema import (
            PlatformData, PlatformType, Feature, FeatureStatus,
            Contributor, TimelineEvent
        )
        
        # Create mock platform data
        platform_data = PlatformData(
            platform=PlatformType.GITHUB,
            platform_key="test/repo",
            platform_url="https://github.com/test/repo",
            auth_type="pat"
        )
        
        # Add contributors
        platform_data.contributors = [
            Contributor(id="dev1", name="Developer 1", commits_count=50),
            Contributor(id="dev2", name="Developer 2", commits_count=20),
        ]
        
        # Add features with various statuses
        now = datetime.utcnow()
        platform_data.features = [
            # Completed features
            Feature(
                id="FEAT-1",
                name="Authentication System",
                description="User auth",
                status=FeatureStatus.DONE,
                assigned_to="dev1",
                created_date=now - timedelta(days=30),
                completed_date=now - timedelta(days=5)
            ),
            # In progress features
            Feature(
                id="FEAT-2",
                name="Dashboard",
                description="Main dashboard",
                status=FeatureStatus.IN_PROGRESS,
                assigned_to="dev2",
                created_date=now - timedelta(days=20),
                due_date=now + timedelta(days=5)
            ),
            # Unassigned feature
            Feature(
                id="FEAT-3",
                name="Reporting Module",
                description="Reports",
                status=FeatureStatus.TODO,
                assigned_to=None,
                created_date=now - timedelta(days=10)
            ),
            # Blocked feature
            Feature(
                id="FEAT-4",
                name="API Integration",
                description="External API",
                status=FeatureStatus.BLOCKED,
                assigned_to="dev1",
                created_date=now - timedelta(days=15)
            ),
        ]
        
        # Add timeline events
        platform_data.timeline_events = [
            TimelineEvent(
                timestamp=now - timedelta(days=20),
                event_type="commit",
                description="Initial auth commit",
                contributor_id="dev1",
                feature_id="FEAT-1"
            ),
            TimelineEvent(
                timestamp=now - timedelta(days=10),
                event_type="commit",
                description="Dashboard WIP",
                contributor_id="dev2",
                feature_id="FEAT-2"
            ),
            TimelineEvent(
                timestamp=now - timedelta(days=5),
                event_type="status_changed",
                description="status: In Progress → Done",
                contributor_id="dev1",
                feature_id="FEAT-1"
            ),
        ]
        
        # Run analyzer
        analyzer = SemanticDelayAnalyzer(platform_data)
        result = analyzer.analyze()
        
        print(f"✓ Analysis complete:")
        print(f"  - Total features: {result.total_features}")
        print(f"  - Completed: {result.completed_features}")
        print(f"  - In progress: {result.in_progress_features}")
        print(f"  - Blocked: {result.blocked_features}")
        print(f"  - Unassigned: {result.unassigned_features}")
        print(f"  - Severity score: {result.severity_score:.2f}")
        print(f"  - Primary causes: {result.primary_causes}")
        print(f"  - Evidence items: {len(result.evidence)}")
        
        print("\n  Evidence breakdown:")
        for evidence in result.evidence:
            print(f"    - {evidence.category.value}: {evidence.description} (severity: {evidence.severity:.2f})")
        
        return True, platform_data, result
    
    except Exception as e:
        print(f"❌ Semantic analyzer error: {e}")
        import traceback
        traceback.print_exc()
        return False, None, None


def test_faq_generator(result):
    """Test FAQ generator."""
    print("\n" + "="*60)
    print("TEST 4: FAQ Auto-Generator")
    print("="*60)
    
    try:
        faq_gen = FAQGenerator(result)
        faqs = faq_gen.generate()
        
        print(f"✓ Generated {len(faqs)} FAQs:")
        
        for i, faq in enumerate(faqs, 1):
            print(f"\n  FAQ {i}:")
            print(f"    Q: {faq.question}")
            print(f"    Category: {faq.category}")
            print(f"    Relevance: {faq.relevance_score:.2f}")
            # Print first line of answer
            answer_preview = faq.answer.split('\n')[0]
            print(f"    A: {answer_preview}...")
        
        return True
    
    except Exception as e:
        print(f"❌ FAQ generator error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_chatbot(platform_data, result):
    """Test chatbot Q&A."""
    print("\n" + "="*60)
    print("TEST 5: Semantic Chatbot")
    print("="*60)
    
    try:
        chatbot = ProjectChatbot(platform_data, result)
        
        # Test various questions
        test_questions = [
            "Who caused the delay?",
            "Why is the project delayed?",
            "Which features are delayed?",
            "What's the overall status?",
        ]
        
        print(f"✓ Chatbot initialized")
        
        for question in test_questions:
            answer = chatbot.chat(question)
            print(f"\n  Q: {question}")
            print(f"  A: {answer.split(chr(10))[0]}...")  # First line
        
        print(f"\n✓ Conversation history: {len(chatbot.get_history())} messages")
        
        return True
    
    except Exception as e:
        print(f"❌ Chatbot error: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all integration tests."""
    print("\n" + "="*70)
    print("MULTI-PLATFORM DELAY ANALYSIS - INTEGRATION TESTS")
    print("="*70)
    
    results = {
        "GitHub Adapter": False,  # Requires valid credentials
        "JIRA Adapter": False,    # Requires valid credentials
        "Semantic Analyzer": False,
        "FAQ Generator": False,
        "Chatbot": False
    }
    
    # Test 1 & 2: Adapters (skip if no credentials)
    print("\n⏭️  Skipping GitHub/JIRA adapter tests (requires valid credentials)")
    print("   In production, replace credentials and run:")
    print("   - test_github_adapter()")
    print("   - test_jira_adapter()")
    
    # Test 3: Semantic Analyzer
    analyzer_success, platform_data, result = test_semantic_analyzer()
    results["Semantic Analyzer"] = analyzer_success
    
    if not analyzer_success:
        print("\n❌ Cannot proceed without semantic analyzer")
        return results
    
    # Test 4: FAQ Generator
    faq_success = test_faq_generator(result)
    results["FAQ Generator"] = faq_success
    
    # Test 5: Chatbot
    chatbot_success = test_chatbot(platform_data, result)
    results["Chatbot"] = chatbot_success
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    for test_name, success in results.items():
        status = "✓ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")
    
    return results


if __name__ == "__main__":
    run_all_tests()
