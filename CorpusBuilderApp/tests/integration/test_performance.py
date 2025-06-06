# tests/test_performance.py
import pytest
import time
import asyncio
import concurrent.futures
from unittest.mock import Mock, patch
import threading
import os

class TestPerformance:
    """Performance and load testing"""
    
    @pytest.mark.performance
    def test_concurrent_data_collection(self):
        """Test performance under concurrent data collection"""
        def mock_collect_data(source_id):
            # Simulate data collection with random delay
            time.sleep(0.1)  # Simulate network delay
            return f"data_from_{source_id}"
        
        start_time = time.time()
        
        # Test with ThreadPoolExecutor
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(mock_collect_data, i) for i in range(10)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete in reasonable time with concurrency
        assert len(results) == 10
        assert execution_time < 2.0  # Should be faster than sequential
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_async_performance(self):
        """Test async operation performance"""
        async def mock_async_operation(delay=0.1):
            await asyncio.sleep(delay)
            return "completed"
        
        start_time = time.time()
        
        # Run multiple async operations concurrently
        tasks = [mock_async_operation(0.1) for _ in range(10)]
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        assert len(results) == 10
        assert all(result == "completed" for result in results)
        # Should complete faster than sequential execution
        assert execution_time < 1.0
    
    @pytest.mark.performance
    def test_memory_usage_monitoring(self):
        """Test memory usage during data processing"""
        import psutil
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Simulate data processing
        large_data = [i for i in range(100000)]
        processed_data = [x * 2 for x in large_data]
        
        final_memory = process.memory_info().rss
        memory_growth = final_memory - initial_memory
        
        # Memory growth should be reasonable
        assert memory_growth < 100 * 1024 * 1024  # Less than 100MB
        
        # Cleanup
        del large_data, processed_data
    
    @pytest.mark.performance
    def test_file_processing_performance(self):
        """Test file processing performance"""
        import tempfile
        
        # Create test file
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp_file:
            # Write large amount of data
            for i in range(10000):
                tmp_file.write(f"Line {i}: This is test data for performance testing.\n")
            tmp_file.flush()
            
            start_time = time.time()
            
            # Process file
            line_count = 0
            with open(tmp_file.name, 'r') as f:
                for line in f:
                    line_count += 1
                    # Simulate processing
                    processed_line = line.strip().upper()
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            assert line_count == 10000
            assert processing_time < 5.0  # Should complete in reasonable time
            
            os.unlink(tmp_file.name)
