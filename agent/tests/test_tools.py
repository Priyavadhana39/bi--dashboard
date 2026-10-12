"""
Tests for Agent Tools (Database, ML, RAG)
"""

import pytest
from unittest.mock import Mock, patch
from agent.tools.database_tools import DatabaseTools
from agent.tools.ml_tools import MLTools
from agent.tools.rag_tools import RAGTools


class TestDatabaseTools:
    """Test database tool functions"""
    
    @patch('agent.tools.database_tools.psycopg2.connect')
    def test_get_supplier_info(self, mock_connect):
        """Test getting supplier information"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            (1, 'Alpha_Inc', 100, 50000, 45000, 5000, 8.5, 10.5, 2.5, 95.0)
        ]
        mock_cursor.description = [
            ('supplier_id',), ('supplier',), ('total_orders',), 
            ('total_quantity',), ('total_spend',), ('total_savings',),
            ('avg_savings_pct',), ('avg_lead_time',), ('avg_defect_rate',), ('compliance_rate',)
        ]
        
        mock_conn = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        db = DatabaseTools()
        result = db.get_supplier_info('Alpha_Inc')
        
        assert result is not None
        assert result['supplier'] == 'Alpha_Inc'
        assert result['total_orders'] == 100
    
    def test_parameterized_sql(self):
        """Verify SQL queries use parameterized format"""
        db = DatabaseTools()
        
        # Check that get_supplier_info uses parameterized query
        with patch.object(db, '_execute_query') as mock_exec:
            db.get_supplier_info('TestSupplier')
            
            # Verify parameterized call was made
            call_args = mock_exec.call_args
            assert call_args[0][1] == ('TestSupplier',)


class TestMLTools:
    """Test ML tool functions"""
    
    @patch('agent.tools.ml_tools.psycopg2.connect')
    def test_get_supplier_scores(self, mock_connect):
        """Test getting supplier scores"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            ('Alpha_Inc', 80.5, 1, 'Excellent', 8.2, 10.5, 2.5, 95.0, 85.0, '2024-01-01')
        ]
        mock_cursor.description = [
            ('supplier',), ('supplier_score',), ('supplier_rank',),
            ('performance_category',), ('avg_savings_percentage',),
            ('avg_lead_time_days',), ('avg_defect_rate',), ('compliance_rate',),
            ('data_completeness_pct',), ('created_at',)
        ]
        
        mock_conn = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        ml = MLTools()
        results = ml.get_supplier_scores()
        
        assert len(results) > 0
        assert results[0]['supplier'] == 'Alpha_Inc'
    
    @patch('agent.tools.ml_tools.psycopg2.connect')
    def test_get_price_anomalies(self, mock_connect):
        """Test getting price anomalies"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_cursor.description = []
        
        mock_conn = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        ml = MLTools()
        results = ml.get_price_anomalies(limit=50)
        
        assert isinstance(results, list)


class TestRAGTools:
    """Test RAG tool functions"""
    
    def test_rag_tools_initialization(self):
        """Test RAG tools can be initialized"""
        rag = RAGTools()
        assert rag is not None
    
    @patch('agent.tools.rag_tools.retriever')
    def test_retrieve_policy_disabled(self, mock_retriever):
        """Test policy retrieval when RAG is disabled"""
        with patch('agent.tools.rag_tools.config') as mock_config:
            mock_config.ENABLE_RAG = False
            
            rag = RAGTools()
            result = rag.retrieve_policy("test query")
            
            assert not result['has_results']
            assert 'disabled' in result['message'].lower()
    
    def test_get_status(self):
        """Test getting RAG status"""
        rag = RAGTools()
        status = rag.get_status()
        
        assert 'enabled' in status
        assert 'available' in status
        assert 'document_count' in status
