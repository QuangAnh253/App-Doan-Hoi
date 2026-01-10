# core/db_retry.py
import time
import functools
from typing import Callable, Any


def retry_db_operation(max_retries: int = 3, delay: float = 2.0, backoff: float = 1.5):
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_error = None
            current_delay = delay
            
            for attempt in range(max_retries):
                try:
                    result = func(*args, **kwargs)
                    return result
                    
                except Exception as e:
                    error_msg = str(e).lower()
                    
                    is_network_error = any(keyword in error_msg for keyword in [
                        'disconnect', 'disconnected', 'timeout', 'timed out',
                        'connection', 'network', 'unavailable', 'unreachable',
                        'refused', 'reset', 'broken pipe', 'aborted',
                        'temporary failure', 'service unavailable',
                        'gateway timeout', 'bad gateway'
                    ])
                    
                    last_error = e
                    
                    if attempt >= max_retries - 1 or not is_network_error:
                        raise
                    
                    time.sleep(current_delay)
                    current_delay *= backoff
            
            if last_error:
                raise last_error
            raise Exception(f"Max retries ({max_retries}) reached for {func.__name__}")
        
        return wrapper
    return decorator


def retry_quick(func: Callable) -> Callable:
    return retry_db_operation(max_retries=2, delay=1.0, backoff=1.5)(func)


def retry_standard(func: Callable) -> Callable:
    return retry_db_operation(max_retries=3, delay=2.0, backoff=1.5)(func)


def retry_patient(func: Callable) -> Callable:
    return retry_db_operation(max_retries=4, delay=3.0, backoff=2.0)(func)


def retry_critical(func: Callable) -> Callable:
    return retry_db_operation(max_retries=5, delay=5.0, backoff=2.0)(func)


class RetryContext:
    def __init__(self, max_retries: int = 3, delay: float = 2.0, backoff: float = 1.5):
        self.max_retries = max_retries
        self.delay = delay
        self.backoff = backoff
        self.attempt = 0
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            return False
        
        error_msg = str(exc_val).lower() if exc_val else ""
        is_network_error = any(keyword in error_msg for keyword in [
            'disconnect', 'disconnected', 'timeout', 'connection', 'network'
        ])
        
        if is_network_error and self.attempt < self.max_retries - 1:
            self.attempt += 1
            current_delay = self.delay * (self.backoff ** (self.attempt - 1))
            time.sleep(current_delay)
            return True
        
        return False


def retry_batch_operation(
    items: list,
    operation: Callable,
    batch_size: int = 50,
    max_retries: int = 3,
    delay: float = 2.0
):
    results = []
    
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        
        @retry_db_operation(max_retries=max_retries, delay=delay)
        def process_batch():
            return operation(batch)
        
        try:
            batch_result = process_batch()
            results.append(batch_result)
        except Exception as e:
            raise
    
    return results