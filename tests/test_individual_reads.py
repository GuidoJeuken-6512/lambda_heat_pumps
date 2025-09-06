"""Tests for Individual-Reads and Timeout-Adjustment features."""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from custom_components.lambda_heat_pumps.const import (
    LAMBDA_INDIVIDUAL_READ_REGISTERS,
    LAMBDA_REGISTER_TIMEOUTS,
    LAMBDA_MODBUS_TIMEOUT
)
from custom_components.lambda_heat_pumps.modbus_utils import (
    async_read_modbus_with_robustness,
    check_dynamic_individual_read
)


class TestIndividualReadsConfiguration:
    """Test Individual-Reads configuration constants."""

    def test_individual_read_registers_configuration(self):
        """Test that Individual-Read registers are configured correctly."""
        assert LAMBDA_INDIVIDUAL_READ_REGISTERS == [0]
        assert isinstance(LAMBDA_INDIVIDUAL_READ_REGISTERS, list)
        assert 0 in LAMBDA_INDIVIDUAL_READ_REGISTERS

    def test_register_timeouts_configuration(self):
        """Test that register-specific timeouts are configured correctly."""
        assert LAMBDA_REGISTER_TIMEOUTS == {0: 2}
        assert isinstance(LAMBDA_REGISTER_TIMEOUTS, dict)
        assert 0 in LAMBDA_REGISTER_TIMEOUTS
        assert LAMBDA_REGISTER_TIMEOUTS[0] == 2

    def test_timeout_values_are_reasonable(self):
        """Test that timeout values are reasonable."""
        assert LAMBDA_MODBUS_TIMEOUT == 3
        assert LAMBDA_REGISTER_TIMEOUTS[0] < LAMBDA_MODBUS_TIMEOUT
        assert LAMBDA_REGISTER_TIMEOUTS[0] > 0


class TestAsyncReadModbusWithRobustness:
    """Test async_read_modbus_with_robustness function."""

    @pytest.mark.asyncio
    async def test_timeout_adjustment_for_configured_register(self):
        """Test that timeout is adjusted for configured register."""
        mock_client = AsyncMock()
        mock_result = Mock()
        mock_result.registers = [1234]

        sensor_info = {"relative_address": 0}

        with patch('custom_components.lambda_heat_pumps.modbus_utils.async_read_holding_registers_with_backoff') as mock_read:
            mock_read.return_value = mock_result

            result = await async_read_modbus_with_robustness(
                mock_client, 0, 1, 1, None, sensor_info, LAMBDA_MODBUS_TIMEOUT
            )

        # Check that timeout was adjusted
        mock_read.assert_called_once_with(mock_client, 0, 1, 1, 2)
        assert result == mock_result

    @pytest.mark.asyncio
    async def test_no_timeout_adjustment_for_unconfigured_register(self):
        """Test that timeout is not adjusted for unconfigured register."""
        mock_client = AsyncMock()
        mock_result = Mock()
        mock_result.registers = [5678]

        sensor_info = {"relative_address": 1}

        with patch('custom_components.lambda_heat_pumps.modbus_utils.async_read_holding_registers_with_backoff') as mock_read:
            mock_read.return_value = mock_result

            result = await async_read_modbus_with_robustness(
                mock_client, 1001, 1, 1, None, sensor_info, LAMBDA_MODBUS_TIMEOUT
            )

        # Check that default timeout was used
        mock_read.assert_called_once_with(
            mock_client, 1001, 1, 1, LAMBDA_MODBUS_TIMEOUT
        )
        assert result == mock_result

    @pytest.mark.asyncio
    async def test_timeout_adjustment_logging(self):
        """Test that timeout adjustment is logged correctly."""
        mock_client = AsyncMock()
        mock_result = Mock()
        mock_result.registers = [9999]

        sensor_info = {"relative_address": 0}

        with patch('custom_components.lambda_heat_pumps.modbus_utils.async_read_holding_registers_with_backoff') as mock_read:
            mock_read.return_value = mock_result

            with patch('custom_components.lambda_heat_pumps.modbus_utils._LOGGER') as mock_logger:
                await async_read_modbus_with_robustness(
                    mock_client, 0, 1, 1, None, sensor_info, LAMBDA_MODBUS_TIMEOUT
                )

        # Check that timeout adjustment was logged
        info_calls = [call for call in mock_logger.info.call_args_list
                     if "TIMEOUT-ADJUST" in str(call)]
        assert len(info_calls) == 1

    @pytest.mark.asyncio
    async def test_circuit_breaker_integration(self):
        """Test that circuit breaker is properly integrated."""
        mock_circuit_breaker = Mock()
        mock_circuit_breaker.can_execute.return_value = False

        with pytest.raises(Exception, match="Circuit breaker is OPEN"):
            await async_read_modbus_with_robustness(
                None, 0, 1, 1, mock_circuit_breaker, None,
                LAMBDA_MODBUS_TIMEOUT
            )

    @pytest.mark.asyncio
    async def test_circuit_breaker_success_recording(self):
        """Test that circuit breaker success is recorded."""
        mock_client = AsyncMock()
        mock_result = Mock()
        mock_result.registers = [1111]
        mock_circuit_breaker = Mock()
        mock_circuit_breaker.can_execute.return_value = True

        with patch('custom_components.lambda_heat_pumps.modbus_utils.async_read_holding_registers_with_backoff') as mock_read:
            mock_read.return_value = mock_result

            await async_read_modbus_with_robustness(
                mock_client, 0, 1, 1, mock_circuit_breaker, None,
                LAMBDA_MODBUS_TIMEOUT
            )

        mock_circuit_breaker.record_success.assert_called_once()

    @pytest.mark.asyncio
    async def test_circuit_breaker_failure_recording(self):
        """Test that circuit breaker failure is recorded."""
        mock_client = AsyncMock()
        mock_circuit_breaker = Mock()
        mock_circuit_breaker.can_execute.return_value = True

        with patch('custom_components.lambda_heat_pumps.modbus_utils.async_read_holding_registers_with_backoff') as mock_read:
            mock_read.side_effect = Exception("Test error")

            with pytest.raises(Exception):
                await async_read_modbus_with_robustness(
                    mock_client, 0, 1, 1, mock_circuit_breaker, None,
                    LAMBDA_MODBUS_TIMEOUT
                )

        mock_circuit_breaker.record_failure.assert_called_once()


class TestCheckDynamicIndividualRead:
    """Test check_dynamic_individual_read function."""

    def test_no_action_when_relative_addr_is_none(self):
        """Test that no action is taken when relative_addr is None."""
        dynamic_reads = set()
        timeout_counters = {}
        failure_counters = {}

        check_dynamic_individual_read(
            dynamic_reads, timeout_counters, failure_counters,
            1000, None, "timeout", 3, 5
        )

        assert len(dynamic_reads) == 0

    def test_no_action_when_already_in_individual_reads(self):
        """Test that no action is taken when register is already in Individual-Reads."""
        dynamic_reads = {1000}
        timeout_counters = {1000: 5}
        failure_counters = {}

        check_dynamic_individual_read(
            dynamic_reads, timeout_counters, failure_counters,
            1000, 0, "timeout", 3, 5
        )

        assert len(dynamic_reads) == 1
        assert 1000 in dynamic_reads

    def test_timeout_threshold_reached(self):
        """Test that register is added when timeout threshold is reached."""
        dynamic_reads = set()
        timeout_counters = {1000: 3}
        failure_counters = {}

        with patch('custom_components.lambda_heat_pumps.modbus_utils._LOGGER') as mock_logger:
            check_dynamic_individual_read(
                dynamic_reads, timeout_counters, failure_counters,
                1000, 0, "timeout", 3, 5
            )

        assert 1000 in dynamic_reads
        mock_logger.info.assert_called_once()
        assert "DYNAMIC-INDIVIDUAL" in str(mock_logger.info.call_args)

    def test_failure_threshold_reached(self):
        """Test that register is added when failure threshold is reached."""
        dynamic_reads = set()
        timeout_counters = {}
        failure_counters = {1000: 5}

        with patch('custom_components.lambda_heat_pumps.modbus_utils._LOGGER') as mock_logger:
            check_dynamic_individual_read(
                dynamic_reads, timeout_counters, failure_counters,
                1000, 0, "failure", 3, 5
            )

        assert 1000 in dynamic_reads
        mock_logger.info.assert_called_once()
        assert "DYNAMIC-INDIVIDUAL" in str(mock_logger.info.call_args)

    def test_no_action_when_threshold_not_reached(self):
        """Test that no action is taken when threshold is not reached."""
        dynamic_reads = set()
        timeout_counters = {1000: 2}
        failure_counters = {1000: 3}

        check_dynamic_individual_read(
            dynamic_reads, timeout_counters, failure_counters,
            1000, 0, "timeout", 3, 5
        )

        check_dynamic_individual_read(
            dynamic_reads, timeout_counters, failure_counters,
            1000, 0, "failure", 3, 5
        )

        assert len(dynamic_reads) == 0

    def test_custom_thresholds(self):
        """Test that custom thresholds work correctly."""
        dynamic_reads = set()
        timeout_counters = {1000: 2}
        failure_counters = {1000: 4}

        # Test with custom thresholds
        check_dynamic_individual_read(
            dynamic_reads, timeout_counters, failure_counters,
            1000, 0, "timeout", 2, 5
        )

        check_dynamic_individual_read(
            dynamic_reads, timeout_counters, failure_counters,
            1000, 0, "failure", 3, 4
        )

        assert 1000 in dynamic_reads

    def test_multiple_registers(self):
        """Test that multiple registers can be added independently."""
        dynamic_reads = set()
        timeout_counters = {1000: 3, 2000: 3}
        failure_counters = {}

        check_dynamic_individual_read(
            dynamic_reads, timeout_counters, failure_counters,
            1000, 0, "timeout", 3, 5
        )

        check_dynamic_individual_read(
            dynamic_reads, timeout_counters, failure_counters,
            2000, 0, "timeout", 3, 5
        )

        assert 1000 in dynamic_reads
        assert 2000 in dynamic_reads
        assert len(dynamic_reads) == 2


class TestIndividualReadsIntegration:
    """Test Individual-Reads integration with coordinators."""

    def test_static_individual_reads_initialization(self):
        """Test that static Individual-Reads are properly initialized."""
        from custom_components.lambda_heat_pumps.coordinator import LambdaDataUpdateCoordinator

        # Mock the coordinator initialization
        with patch('custom_components.lambda_heat_pumps.coordinator.SmartCircuitBreaker'):
            with patch('custom_components.lambda_heat_pumps.coordinator.HACompatibleOfflineManager'):
                coordinator = LambdaDataUpdateCoordinator(
                    Mock(), Mock(), modbus_timeout=3, max_retries=3,
                    circuit_breaker_enabled=True
                )

        # Check that static Individual-Reads are initialized
        assert hasattr(coordinator, '_dynamic_individual_reads')
        assert 0 in coordinator._dynamic_individual_reads
        assert hasattr(coordinator, '_register_timeout_counters')
        assert hasattr(coordinator, '_register_failure_counters')
        assert coordinator._dynamic_timeout_threshold == 3
        assert coordinator._dynamic_failure_threshold == 5

    def test_modular_coordinator_initialization(self):
        """Test that Modular Coordinator is properly initialized."""
        from custom_components.lambda_heat_pumps.modular_coordinator import LambdaModularCoordinator

        # Mock the coordinator initialization
        with patch('custom_components.lambda_heat_pumps.modular_coordinator.SmartCircuitBreaker'):
            with patch('custom_components.lambda_heat_pumps.modular_coordinator.HACompatibleOfflineManager'):
                coordinator = LambdaModularCoordinator(
                    Mock(), Mock(), modbus_timeout=3, max_retries=3,
                    circuit_breaker_enabled=True
                )

        # Check that static Individual-Reads are initialized
        assert hasattr(coordinator, '_dynamic_individual_reads')
        assert 0 in coordinator._dynamic_individual_reads
        assert hasattr(coordinator, '_register_timeout_counters')
        assert hasattr(coordinator, '_register_failure_counters')
        assert coordinator._dynamic_timeout_threshold == 3
        assert coordinator._dynamic_failure_threshold == 5