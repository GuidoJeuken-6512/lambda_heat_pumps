"""Tests for robustness features in utils.py."""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock

from custom_components.lambda_heat_pumps.utils import async_read_holding_registers_with_backoff


class TestAsyncReadHoldingRegistersWithBackoff:
    """Test cases for async_read_holding_registers_with_backoff function."""

    @pytest.mark.asyncio
    async def test_successful_read_first_attempt(self):
        """Test successful read on first attempt."""
        mock_client = AsyncMock()
        mock_result = Mock()
        mock_result.registers = [1234]
        mock_client.read_holding_registers.return_value = mock_result
        
        result = await async_read_holding_registers_with_backoff(
            mock_client, 1000, 1, 1, 10
        )
        
        assert result == mock_result
        mock_client.read_holding_registers.assert_called_once_with(1000, count=1, slave=1)

    @pytest.mark.asyncio
    async def test_successful_read_after_retries(self):
        """Test successful read after some retries."""
        mock_client = AsyncMock()
        mock_result = Mock()
        mock_result.registers = [5678]
        
        # First two calls fail, third succeeds
        mock_client.read_holding_registers.side_effect = [
            ConnectionError("Network error"),
            asyncio.TimeoutError("Timeout"),
            mock_result
        ]
        
        with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
            result = await async_read_holding_registers_with_backoff(
                mock_client, 2000, 1, 1, 10
            )
        
        assert result == mock_result
        assert mock_client.read_holding_registers.call_count == 3
        assert mock_sleep.call_count == 2  # Two retries

    @pytest.mark.asyncio
    async def test_all_retries_fail(self):
        """Test that exception is raised when all retries fail."""
        mock_client = AsyncMock()
        mock_client.read_holding_registers.side_effect = ConnectionError("Persistent network error")
        
        with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
            with pytest.raises(ConnectionError, match="Persistent network error"):
                await async_read_holding_registers_with_backoff(
                    mock_client, 3000, 1, 1, 10
                )
        
        assert mock_client.read_holding_registers.call_count == 3  # Max retries
        assert mock_sleep.call_count == 2  # Two retries

    @pytest.mark.asyncio
    async def test_exponential_backoff_timing(self):
        """Test that exponential backoff timing is correct."""
        mock_client = AsyncMock()
        mock_client.read_holding_registers.side_effect = [
            ConnectionError("Error 1"),
            ConnectionError("Error 2"),
            Mock(registers=[9999])
        ]
        
        with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
            await async_read_holding_registers_with_backoff(
                mock_client, 4000, 1, 1, 10
            )
        
        # Check that sleep was called with exponential backoff
        sleep_calls = mock_sleep.call_args_list
        
        # First retry: 5 * (2^0) = 5 seconds (with jitter)
        first_delay = sleep_calls[0][0][0]
        assert 4 <= first_delay <= 6  # 5 ± 20% jitter
        
        # Second retry: 5 * (2^1) = 10 seconds (with jitter)
        second_delay = sleep_calls[1][0][0]
        assert 8 <= second_delay <= 12  # 10 ± 20% jitter

    @pytest.mark.asyncio
    async def test_max_delay_cap(self):
        """Test that delay is capped at maximum value."""
        mock_client = AsyncMock()
        mock_client.read_holding_registers.side_effect = [
            ConnectionError("Error 1"),
            ConnectionError("Error 2"),
            Mock(registers=[1111])
        ]
        
        with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
            await async_read_holding_registers_with_backoff(
                mock_client, 5000, 1, 1, 10
            )
        
        # Check that delays don't exceed 30 seconds (max_delay)
        sleep_calls = mock_sleep.call_args_list
        for call in sleep_calls:
            delay = call[0][0]
            assert delay <= 30

    @pytest.mark.asyncio
    async def test_minimum_delay(self):
        """Test that delay is never less than 1 second."""
        mock_client = AsyncMock()
        mock_client.read_holding_registers.side_effect = [
            ConnectionError("Error 1"),
            Mock(registers=[2222])
        ]
        
        with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
            await async_read_holding_registers_with_backoff(
                mock_client, 6000, 1, 1, 10
            )
        
        # Check that delay is at least 1 second
        sleep_calls = mock_sleep.call_args_list
        for call in sleep_calls:
            delay = call[0][0]
            assert delay >= 1

    @pytest.mark.asyncio
    async def test_jitter_variation(self):
        """Test that jitter adds variation to delays."""
        mock_client = AsyncMock()
        mock_client.read_holding_registers.side_effect = [
            ConnectionError("Error 1"),
            Mock(registers=[3333])
        ]
        
        delays = []
        for _ in range(10):  # Run multiple times to test jitter variation
            mock_client.reset_mock()
            mock_client.read_holding_registers.side_effect = [
                ConnectionError("Error 1"),
                Mock(registers=[3333])
            ]
            
            with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
                await async_read_holding_registers_with_backoff(
                    mock_client, 7000, 1, 1, 10
                )
            
            if mock_sleep.call_args_list:
                delays.append(mock_sleep.call_args_list[0][0][0])
        
        # Check that delays vary (jitter is working)
        if len(delays) > 1:
            assert min(delays) != max(delays)  # Should have variation

    @pytest.mark.asyncio
    async def test_timeout_parameter(self):
        """Test that timeout parameter is passed correctly."""
        mock_client = AsyncMock()
        mock_result = Mock()
        mock_result.registers = [4444]
        mock_client.read_holding_registers.return_value = mock_result
        
        with patch('asyncio.wait_for') as mock_wait_for:
            mock_wait_for.return_value = mock_result
            
            await async_read_holding_registers_with_backoff(
                mock_client, 8000, 1, 1, 15  # Custom timeout
            )
        
        # Check that wait_for was called with correct timeout
        mock_wait_for.assert_called_once()
        call_args = mock_wait_for.call_args
        assert call_args[1]['timeout'] == 15

    @pytest.mark.asyncio
    async def test_different_exception_types(self):
        """Test handling of different exception types."""
        mock_client = AsyncMock()
        mock_result = Mock()
        mock_result.registers = [5555]
        
        # Test with different exception types
        exceptions = [
            ConnectionError("Connection failed"),
            asyncio.TimeoutError("Operation timed out"),
            OSError("Network unreachable"),
            RuntimeError("Unexpected error")
        ]
        
        for exception in exceptions:
            mock_client.reset_mock()
            mock_client.read_holding_registers.side_effect = [
                exception,
                mock_result
            ]
            
            with patch('asyncio.sleep', new_callable=AsyncMock):
                result = await async_read_holding_registers_with_backoff(
                    mock_client, 9000, 1, 1, 10
                )
            
            assert result == mock_result
            assert mock_client.read_holding_registers.call_count == 2

    @pytest.mark.asyncio
    async def test_parameter_validation(self):
        """Test that function parameters are passed correctly."""
        mock_client = AsyncMock()
        mock_result = Mock()
        mock_result.registers = [6666]
        mock_client.read_holding_registers.return_value = mock_result
        
        await async_read_holding_registers_with_backoff(
            mock_client, 10000, 5, 2, 20  # address=10000, count=5, slave=2, timeout=20
        )
        
        # Check that read_holding_registers was called with correct parameters
        mock_client.read_holding_registers.assert_called_once_with(
            10000, count=5, slave=2
        )

    @pytest.mark.asyncio
    async def test_logging_on_retries(self):
        """Test that appropriate logging occurs during retries."""
        mock_client = AsyncMock()
        mock_client.read_holding_registers.side_effect = [
            ConnectionError("Network error"),
            Mock(registers=[7777])
        ]
        
        with patch('asyncio.sleep', new_callable=AsyncMock):
            with patch('custom_components.lambda_heat_pumps.utils._LOGGER') as mock_logger:
                await async_read_holding_registers_with_backoff(
                    mock_client, 11000, 1, 1, 10
                )
        
        # Check that debug logging occurred for retry
        debug_calls = [call for call in mock_logger.debug.call_args_list 
                      if "retrying in" in str(call)]
        assert len(debug_calls) == 1

    @pytest.mark.asyncio
    async def test_logging_on_final_failure(self):
        """Test that error logging occurs on final failure."""
        mock_client = AsyncMock()
        mock_client.read_holding_registers.side_effect = ConnectionError("Persistent error")
        
        with patch('asyncio.sleep', new_callable=AsyncMock):
            with patch('custom_components.lambda_heat_pumps.utils._LOGGER') as mock_logger:
                with pytest.raises(ConnectionError):
                    await async_read_holding_registers_with_backoff(
                        mock_client, 12000, 1, 1, 10
                    )
        
        # Check that error logging occurred
        error_calls = [call for call in mock_logger.error.call_args_list 
                      if "failed after" in str(call)]
        assert len(error_calls) == 1
