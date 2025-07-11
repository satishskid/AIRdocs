#!/usr/bin/env python3
"""
Circuit Breaker Implementation for AI Services
Provides automatic failover, service isolation, and recovery for reliable AI service orchestration
"""

import time
import asyncio
import logging
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass
from enum import Enum
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Service isolated due to failures
    HALF_OPEN = "half_open"  # Testing if service has recovered

@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5          # Number of failures before opening
    recovery_timeout: int = 60          # Seconds before trying half-open
    success_threshold: int = 3          # Successes needed to close from half-open
    timeout: int = 30                   # Request timeout in seconds
    monitor_window: int = 300           # Time window for failure tracking (5 minutes)

@dataclass
class ServiceMetrics:
    """Metrics for service health monitoring."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    last_failure_time: float = 0
    last_success_time: float = 0
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    average_response_time: float = 0
    failure_rate: float = 0

class CircuitBreaker:
    """
    Circuit breaker for individual AI service.
    Implements the circuit breaker pattern for fault tolerance.
    """
    
    def __init__(self, service_name: str, config: CircuitBreakerConfig = None):
        self.service_name = service_name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.metrics = ServiceMetrics()
        self.last_state_change = time.time()
        self.failure_times: List[float] = []
        self.response_times: List[float] = []
    
    async def call(self, func: Callable, *args, **kwargs) -> Dict[str, Any]:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Async function to execute
            *args, **kwargs: Arguments for the function
            
        Returns:
            Dict containing result and circuit breaker metadata
        """
        
        # Check circuit state
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._transition_to_half_open()
            else:
                return self._create_circuit_open_response()
        
        # Execute the function
        start_time = time.time()
        try:
            # Set timeout for the request
            result = await asyncio.wait_for(
                func(*args, **kwargs),
                timeout=self.config.timeout
            )
            
            # Record success
            response_time = time.time() - start_time
            self._record_success(response_time)
            
            # Add circuit breaker metadata
            if isinstance(result, dict):
                result["circuit_breaker"] = {
                    "service": self.service_name,
                    "state": self.state.value,
                    "response_time": response_time,
                    "attempt_number": 1
                }
            
            return result
        
        except asyncio.TimeoutError:
            response_time = time.time() - start_time
            self._record_failure("timeout")
            
            return {
                "success": False,
                "error": "timeout",
                "service": self.service_name,
                "circuit_breaker": {
                    "service": self.service_name,
                    "state": self.state.value,
                    "response_time": response_time,
                    "failure_reason": "timeout"
                }
            }
        
        except Exception as e:
            response_time = time.time() - start_time
            self._record_failure(str(e))
            
            return {
                "success": False,
                "error": str(e),
                "service": self.service_name,
                "circuit_breaker": {
                    "service": self.service_name,
                    "state": self.state.value,
                    "response_time": response_time,
                    "failure_reason": str(e)
                }
            }
    
    def _record_success(self, response_time: float):
        """Record successful request."""
        
        current_time = time.time()
        
        # Update metrics
        self.metrics.total_requests += 1
        self.metrics.successful_requests += 1
        self.metrics.last_success_time = current_time
        self.metrics.consecutive_successes += 1
        self.metrics.consecutive_failures = 0
        
        # Update response times
        self.response_times.append(response_time)
        if len(self.response_times) > 100:  # Keep last 100 response times
            self.response_times.pop(0)
        
        self.metrics.average_response_time = sum(self.response_times) / len(self.response_times)
        
        # Update failure rate
        self._update_failure_rate()
        
        # Handle state transitions
        if self.state == CircuitState.HALF_OPEN:
            if self.metrics.consecutive_successes >= self.config.success_threshold:
                self._transition_to_closed()
        
        logger.debug(f"✅ {self.service_name} success recorded (consecutive: {self.metrics.consecutive_successes})")
    
    def _record_failure(self, error: str):
        """Record failed request."""
        
        current_time = time.time()
        
        # Update metrics
        self.metrics.total_requests += 1
        self.metrics.failed_requests += 1
        self.metrics.last_failure_time = current_time
        self.metrics.consecutive_failures += 1
        self.metrics.consecutive_successes = 0
        
        # Track failure times
        self.failure_times.append(current_time)
        # Keep only failures within the monitor window
        cutoff_time = current_time - self.config.monitor_window
        self.failure_times = [t for t in self.failure_times if t > cutoff_time]
        
        # Update failure rate
        self._update_failure_rate()
        
        # Handle state transitions
        if self.state == CircuitState.CLOSED:
            if self.metrics.consecutive_failures >= self.config.failure_threshold:
                self._transition_to_open()
        elif self.state == CircuitState.HALF_OPEN:
            self._transition_to_open()
        
        logger.warning(f"❌ {self.service_name} failure recorded: {error} (consecutive: {self.metrics.consecutive_failures})")
    
    def _update_failure_rate(self):
        """Update failure rate based on recent requests."""
        
        if self.metrics.total_requests > 0:
            self.metrics.failure_rate = self.metrics.failed_requests / self.metrics.total_requests
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit should attempt to reset from open to half-open."""
        
        return (time.time() - self.last_state_change) >= self.config.recovery_timeout
    
    def _transition_to_open(self):
        """Transition circuit to open state."""
        
        self.state = CircuitState.OPEN
        self.last_state_change = time.time()
        
        logger.error(f"🔴 Circuit breaker OPEN for {self.service_name} (failures: {self.metrics.consecutive_failures})")
    
    def _transition_to_half_open(self):
        """Transition circuit to half-open state."""
        
        self.state = CircuitState.HALF_OPEN
        self.last_state_change = time.time()
        self.metrics.consecutive_successes = 0
        
        logger.info(f"🟡 Circuit breaker HALF-OPEN for {self.service_name} (testing recovery)")
    
    def _transition_to_closed(self):
        """Transition circuit to closed state."""
        
        self.state = CircuitState.CLOSED
        self.last_state_change = time.time()
        self.metrics.consecutive_failures = 0
        
        logger.info(f"🟢 Circuit breaker CLOSED for {self.service_name} (service recovered)")
    
    def _create_circuit_open_response(self) -> Dict[str, Any]:
        """Create response when circuit is open."""
        
        return {
            "success": False,
            "error": "circuit_breaker_open",
            "service": self.service_name,
            "message": f"Service {self.service_name} is currently unavailable",
            "circuit_breaker": {
                "service": self.service_name,
                "state": self.state.value,
                "consecutive_failures": self.metrics.consecutive_failures,
                "last_failure_time": self.metrics.last_failure_time,
                "recovery_time": self.last_state_change + self.config.recovery_timeout
            }
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status and metrics."""
        
        current_time = time.time()
        
        return {
            "service": self.service_name,
            "state": self.state.value,
            "healthy": self.state != CircuitState.OPEN,
            "metrics": {
                "total_requests": self.metrics.total_requests,
                "successful_requests": self.metrics.successful_requests,
                "failed_requests": self.metrics.failed_requests,
                "failure_rate": self.metrics.failure_rate,
                "consecutive_failures": self.metrics.consecutive_failures,
                "consecutive_successes": self.metrics.consecutive_successes,
                "average_response_time": self.metrics.average_response_time,
                "last_success_time": self.metrics.last_success_time,
                "last_failure_time": self.metrics.last_failure_time
            },
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "recovery_timeout": self.config.recovery_timeout,
                "success_threshold": self.config.success_threshold,
                "timeout": self.config.timeout
            },
            "state_info": {
                "last_state_change": self.last_state_change,
                "time_in_current_state": current_time - self.last_state_change,
                "next_retry_time": self.last_state_change + self.config.recovery_timeout if self.state == CircuitState.OPEN else None
            }
        }
    
    def reset(self):
        """Manually reset circuit breaker to closed state."""
        
        self.state = CircuitState.CLOSED
        self.last_state_change = time.time()
        self.metrics.consecutive_failures = 0
        self.metrics.consecutive_successes = 0
        self.failure_times.clear()
        
        logger.info(f"🔄 Circuit breaker manually reset for {self.service_name}")

class CircuitBreakerManager:
    """
    Manages circuit breakers for all AI services.
    Provides centralized monitoring and control.
    """
    
    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.default_config = CircuitBreakerConfig()
    
    def get_circuit_breaker(self, service_name: str, config: CircuitBreakerConfig = None) -> CircuitBreaker:
        """Get or create circuit breaker for service."""
        
        if service_name not in self.circuit_breakers:
            self.circuit_breakers[service_name] = CircuitBreaker(
                service_name, 
                config or self.default_config
            )
            logger.info(f"🔧 Created circuit breaker for {service_name}")
        
        return self.circuit_breakers[service_name]
    
    async def call_with_circuit_breaker(self, service_name: str, func: Callable, *args, **kwargs) -> Dict[str, Any]:
        """Execute function with circuit breaker protection."""
        
        circuit_breaker = self.get_circuit_breaker(service_name)
        return await circuit_breaker.call(func, *args, **kwargs)
    
    def get_all_health_status(self) -> Dict[str, Dict[str, Any]]:
        """Get health status for all circuit breakers."""
        
        return {
            service_name: breaker.get_health_status()
            for service_name, breaker in self.circuit_breakers.items()
        }
    
    def get_system_health_summary(self) -> Dict[str, Any]:
        """Get overall system health summary."""
        
        total_services = len(self.circuit_breakers)
        healthy_services = sum(
            1 for breaker in self.circuit_breakers.values()
            if breaker.state != CircuitState.OPEN
        )
        
        open_circuits = [
            name for name, breaker in self.circuit_breakers.items()
            if breaker.state == CircuitState.OPEN
        ]
        
        half_open_circuits = [
            name for name, breaker in self.circuit_breakers.items()
            if breaker.state == CircuitState.HALF_OPEN
        ]
        
        return {
            "total_services": total_services,
            "healthy_services": healthy_services,
            "unhealthy_services": total_services - healthy_services,
            "health_percentage": (healthy_services / max(total_services, 1)) * 100,
            "open_circuits": open_circuits,
            "half_open_circuits": half_open_circuits,
            "system_status": "healthy" if healthy_services == total_services else "degraded" if healthy_services > 0 else "critical"
        }
    
    def reset_all_circuit_breakers(self):
        """Reset all circuit breakers to closed state."""
        
        for breaker in self.circuit_breakers.values():
            breaker.reset()
        
        logger.info(f"🔄 Reset all {len(self.circuit_breakers)} circuit breakers")
    
    def reset_circuit_breaker(self, service_name: str) -> bool:
        """Reset specific circuit breaker."""
        
        if service_name in self.circuit_breakers:
            self.circuit_breakers[service_name].reset()
            return True
        
        return False

# Global circuit breaker manager
circuit_breaker_manager = CircuitBreakerManager()

# Convenience functions
async def call_with_circuit_breaker(service_name: str, func: Callable, *args, **kwargs) -> Dict[str, Any]:
    """Execute function with circuit breaker protection."""
    return await circuit_breaker_manager.call_with_circuit_breaker(service_name, func, *args, **kwargs)

def get_service_health(service_name: str) -> Optional[Dict[str, Any]]:
    """Get health status for specific service."""
    if service_name in circuit_breaker_manager.circuit_breakers:
        return circuit_breaker_manager.circuit_breakers[service_name].get_health_status()
    return None

def get_all_service_health() -> Dict[str, Dict[str, Any]]:
    """Get health status for all services."""
    return circuit_breaker_manager.get_all_health_status()

def get_system_health() -> Dict[str, Any]:
    """Get overall system health summary."""
    return circuit_breaker_manager.get_system_health_summary()
