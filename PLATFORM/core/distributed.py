#!/usr/bin/env python3
"""
Distributed Scanning Architecture for Zeek-YARA Integration
Created: August 2025
Author: Security Team

This module implements distributed scanning capabilities including:
- Message queue integration (RabbitMQ, Kafka, in-memory)
- Worker node management and health monitoring
- Load balancing across scanner workers
- Centralized configuration management
"""

import json
import logging
import threading
import time
import uuid
from abc import ABC, abstractmethod
from collections import deque
from enum import Enum
from typing import Any, Dict, List, Optional, Union

try:
    import pika

    RABBITMQ_AVAILABLE = True
except ImportError:
    RABBITMQ_AVAILABLE = False

try:
    from kafka import KafkaConsumer, KafkaProducer

    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False

from queue import Empty, Queue
from threading import Event, Lock


class MessageQueueType(Enum):
    """Message queue implementation types"""

    MEMORY = "memory"
    RABBITMQ = "rabbitmq"
    KAFKA = "kafka"


class WorkerStatus(Enum):
    """Worker node status"""

    IDLE = "idle"
    PROCESSING = "processing"
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    OFFLINE = "offline"


class TaskPriority(Enum):
    """Task priority levels"""

    LOW = 1
    NORMAL = 5
    HIGH = 8
    CRITICAL = 10


class MessageQueueManager(ABC):
    """Abstract base class for message queue implementations"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(
            f"zeek_yara.distributed.{self.__class__.__name__}"
        )

    @abstractmethod
    def connect(self) -> bool:
        """Connect to the message queue"""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from the message queue"""
        pass

    @abstractmethod
    def publish_task(
        self, task: Dict[str, Any], priority: int = TaskPriority.NORMAL.value
    ) -> bool:
        """Publish a task to the queue"""
        pass

    @abstractmethod
    def consume_tasks(self, callback, timeout: Optional[float] = None) -> bool:
        """Consume tasks from the queue"""
        pass

    @abstractmethod
    def get_queue_size(self) -> int:
        """Get current queue size"""
        pass


class InMemoryMessageQueue(MessageQueueManager):
    """In-memory message queue implementation for development/testing"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.task_queue = Queue(maxsize=config.get("MAX_QUEUE_SIZE", 1000))
        self.connected = False
        self.consumer_thread = None
        self.stop_event = Event()

    def connect(self) -> bool:
        """Connect to in-memory queue"""
        self.connected = True
        self.stop_event.clear()
        self.logger.info("Connected to in-memory message queue")
        return True

    def disconnect(self) -> None:
        """Disconnect from in-memory queue"""
        self.stop_event.set()
        if self.consumer_thread and self.consumer_thread.is_alive():
            self.consumer_thread.join(timeout=5.0)
        self.connected = False
        self.logger.info("Disconnected from in-memory message queue")

    def publish_task(
        self, task: Dict[str, Any], priority: int = TaskPriority.NORMAL.value
    ) -> bool:
        """Publish task to in-memory queue"""
        if not self.connected:
            return False

        try:
            task_with_priority = {
                "priority": priority,
                "timestamp": time.time(),
                "task": task,
            }
            self.task_queue.put(task_with_priority, timeout=1.0)
            self.logger.debug(f"Published task: {task.get('task_id', 'unknown')}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to publish task: {e}")
            return False

    def consume_tasks(self, callback, timeout: Optional[float] = None) -> bool:
        """Start consuming tasks from in-memory queue"""
        if not self.connected:
            return False

        def consumer_loop():
            while not self.stop_event.is_set():
                try:
                    task_data = self.task_queue.get(timeout=1.0)
                    task = task_data.get("task", {})
                    callback(task)
                    self.task_queue.task_done()
                except Empty:
                    continue
                except Exception as e:
                    self.logger.error(f"Error processing task: {e}")

        self.consumer_thread = threading.Thread(target=consumer_loop, daemon=True)
        self.consumer_thread.start()
        return True

    def get_queue_size(self) -> int:
        """Get current queue size"""
        return self.task_queue.qsize()


class RabbitMQMessageQueue(MessageQueueManager):
    """RabbitMQ message queue implementation"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        if not RABBITMQ_AVAILABLE:
            raise ImportError("RabbitMQ support requires 'pika' package")

        self.connection = None
        self.channel = None
        self.queue_name = config.get("RABBITMQ_QUEUE", "zeek_yara_tasks")
        self.host = config.get("RABBITMQ_HOST", "localhost")
        self.port = config.get("RABBITMQ_PORT", 5672)

        # Security: Require credentials from environment variables only
        import os

        self.username = os.environ.get("RABBITMQ_USERNAME")
        self.password = os.environ.get("RABBITMQ_PASSWORD")

        if not self.username or not self.password:
            raise ValueError(
                "RabbitMQ credentials must be provided via RABBITMQ_USERNAME and "
                "RABBITMQ_PASSWORD environment variables. Hard-coded credentials are "
                "not allowed for security reasons."
            )

    def connect(self) -> bool:
        """Connect to RabbitMQ"""
        try:
            credentials = pika.PlainCredentials(self.username, self.password)
            parameters = pika.ConnectionParameters(
                host=self.host, port=self.port, credentials=credentials
            )
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()

            # Declare queue with durability
            self.channel.queue_declare(queue=self.queue_name, durable=True)

            self.logger.info(f"Connected to RabbitMQ at {self.host}:{self.port}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to RabbitMQ: {e}")
            return False

    def disconnect(self) -> None:
        """Disconnect from RabbitMQ"""
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
            self.logger.info("Disconnected from RabbitMQ")
        except Exception as e:
            self.logger.error(f"Error disconnecting from RabbitMQ: {e}")

    def publish_task(
        self, task: Dict[str, Any], priority: int = TaskPriority.NORMAL.value
    ) -> bool:
        """Publish task to RabbitMQ"""
        if not self.channel:
            return False

        try:
            task_data = {"priority": priority, "timestamp": time.time(), "task": task}

            self.channel.basic_publish(
                exchange="",
                routing_key=self.queue_name,
                body=json.dumps(task_data),
                properties=pika.BasicProperties(
                    delivery_mode=2, priority=priority  # Make message persistent
                ),
            )
            self.logger.debug(
                f"Published task to RabbitMQ: {task.get('task_id', 'unknown')}"
            )
            return True
        except Exception as e:
            self.logger.error(f"Failed to publish task to RabbitMQ: {e}")
            return False

    def consume_tasks(self, callback, timeout: Optional[float] = None) -> bool:
        """Start consuming tasks from RabbitMQ"""
        if not self.channel:
            return False

        def process_message(ch, method, properties, body):
            try:
                task_data = json.loads(body)
                task = task_data.get("task", {})
                callback(task)
                ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                self.logger.error(f"Error processing RabbitMQ message: {e}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        try:
            self.channel.basic_consume(
                queue=self.queue_name, on_message_callback=process_message
            )
            self.channel.start_consuming()
            return True
        except Exception as e:
            self.logger.error(f"Error consuming from RabbitMQ: {e}")
            return False

    def get_queue_size(self) -> int:
        """Get current queue size from RabbitMQ"""
        if not self.channel:
            return 0

        try:
            method = self.channel.queue_declare(queue=self.queue_name, passive=True)
            return method.method.message_count
        except Exception as e:
            self.logger.error(f"Error getting RabbitMQ queue size: {e}")
            return 0


class KafkaMessageQueue(MessageQueueManager):
    """Apache Kafka message queue implementation"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        if not KAFKA_AVAILABLE:
            raise ImportError("Kafka support requires 'kafka-python' package")

        self.bootstrap_servers = config.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        self.topic = config.get("KAFKA_TOPIC", "zeek-yara-tasks")
        self.group_id = config.get("KAFKA_GROUP_ID", "zeek-yara-workers")
        self.producer = None
        self.consumer = None

    def connect(self) -> bool:
        """Connect to Kafka"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda x: json.dumps(x).encode("utf-8"),
            )
            self.logger.info(f"Connected to Kafka at {self.bootstrap_servers}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to Kafka: {e}")
            return False

    def disconnect(self) -> None:
        """Disconnect from Kafka"""
        try:
            if self.producer:
                self.producer.close()
            if self.consumer:
                self.consumer.close()
            self.logger.info("Disconnected from Kafka")
        except Exception as e:
            self.logger.error(f"Error disconnecting from Kafka: {e}")

    def publish_task(
        self, task: Dict[str, Any], priority: int = TaskPriority.NORMAL.value
    ) -> bool:
        """Publish task to Kafka"""
        if not self.producer:
            return False

        try:
            task_data = {"priority": priority, "timestamp": time.time(), "task": task}

            future = self.producer.send(self.topic, task_data)
            future.get(timeout=10)  # Block until sent
            self.logger.debug(
                f"Published task to Kafka: {task.get('task_id', 'unknown')}"
            )
            return True
        except Exception as e:
            self.logger.error(f"Failed to publish task to Kafka: {e}")
            return False

    def consume_tasks(self, callback, timeout: Optional[float] = None) -> bool:
        """Start consuming tasks from Kafka"""
        try:
            self.consumer = KafkaConsumer(
                self.topic,
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.group_id,
                value_deserializer=lambda x: json.loads(x.decode("utf-8")),
                auto_offset_reset="earliest",
            )

            for message in self.consumer:
                try:
                    task_data = message.value
                    task = task_data.get("task", {})
                    callback(task)
                except Exception as e:
                    self.logger.error(f"Error processing Kafka message: {e}")

            return True
        except Exception as e:
            self.logger.error(f"Error consuming from Kafka: {e}")
            return False

    def get_queue_size(self) -> int:
        """Get current queue size from Kafka (approximate)"""
        # Kafka doesn't provide exact queue size easily
        # This is a simplified implementation
        return 0


class WorkerNode:
    """Represents a worker node in the distributed system"""

    def __init__(
        self,
        worker_id: str,
        host: str,
        port: int,
        capabilities: Optional[List[str]] = None,
    ):
        self.worker_id = worker_id
        self.host = host
        self.port = port
        self.capabilities = capabilities or []
        self.status = WorkerStatus.OFFLINE
        self.last_heartbeat = 0
        self.current_tasks = 0
        self.max_tasks = 5
        self.total_processed = 0
        self.error_count = 0
        self.average_processing_time = 0.0
        self.created_at = time.time()
        self.metadata = {}

    def update_heartbeat(
        self, task_count: int = None, processing_time: float = None
    ) -> None:
        """Update worker heartbeat and status"""
        self.last_heartbeat = time.time()
        if task_count is not None:
            self.current_tasks = task_count
        if processing_time is not None:
            # Update average processing time using exponential moving average
            if self.average_processing_time == 0:
                self.average_processing_time = processing_time
            else:
                alpha = 0.1
                self.average_processing_time = (
                    alpha * processing_time + (1 - alpha) * self.average_processing_time
                )

    def get_load_factor(self) -> float:
        """Get worker load factor (0.0 = idle, 1.0 = fully loaded)"""
        if self.max_tasks <= 0:
            return 1.0
        return min(self.current_tasks / self.max_tasks, 1.0)

    def can_accept_task(self) -> bool:
        """Check if worker can accept new tasks"""
        return (
            self.status in [WorkerStatus.IDLE, WorkerStatus.HEALTHY]
            and self.current_tasks < self.max_tasks
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert worker to dictionary representation"""
        return {
            "worker_id": self.worker_id,
            "host": self.host,
            "port": self.port,
            "capabilities": self.capabilities,
            "status": self.status.value,
            "last_heartbeat": self.last_heartbeat,
            "current_tasks": self.current_tasks,
            "max_tasks": self.max_tasks,
            "total_processed": self.total_processed,
            "error_count": self.error_count,
            "average_processing_time": self.average_processing_time,
            "load_factor": self.get_load_factor(),
            "uptime": time.time() - self.created_at,
            "metadata": self.metadata,
        }


class LoadBalancer:
    """Load balancer for distributing tasks across worker nodes"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger("zeek_yara.distributed.LoadBalancer")
        self.algorithm = config.get("LOAD_BALANCE_ALGORITHM", "load_based")
        self.round_robin_index = 0
        self.lock = Lock()

    def select_worker(
        self, workers: List[WorkerNode], task: Optional[Dict[str, Any]] = None
    ) -> Optional[WorkerNode]:
        """Select best worker for task based on configured algorithm"""
        available_workers = [w for w in workers if w.can_accept_task()]

        if not available_workers:
            return None

        with self.lock:
            if self.algorithm == "load_based":
                return self._select_by_load(available_workers)
            elif self.algorithm == "round_robin":
                return self._select_round_robin(available_workers)
            elif self.algorithm == "capability_based":
                return self._select_by_capability(available_workers, task)
            else:
                self.logger.warning(
                    f"Unknown load balance algorithm: {self.algorithm}, using load_based"
                )
                return self._select_by_load(available_workers)

    def _select_by_load(self, workers: List[WorkerNode]) -> WorkerNode:
        """Select worker with lowest load factor"""
        return min(workers, key=lambda w: w.get_load_factor())

    def _select_round_robin(self, workers: List[WorkerNode]) -> WorkerNode:
        """Select worker using round-robin algorithm"""
        worker = workers[self.round_robin_index % len(workers)]
        self.round_robin_index += 1
        return worker

    def _select_by_capability(
        self, workers: List[WorkerNode], task: Optional[Dict[str, Any]]
    ) -> WorkerNode:
        """Select worker based on capabilities and task requirements"""
        if not task or "required_capabilities" not in task:
            # Fall back to load-based selection
            return self._select_by_load(workers)

        required_caps = set(task["required_capabilities"])
        capable_workers = [
            w for w in workers if required_caps.issubset(set(w.capabilities))
        ]

        if not capable_workers:
            # No workers with required capabilities, use any available
            return self._select_by_load(workers)

        return self._select_by_load(capable_workers)


class WorkerNodeManager:
    """Manager for worker nodes in the distributed system"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger("zeek_yara.distributed.WorkerManager")
        self.workers: Dict[str, WorkerNode] = {}
        self.heartbeat_timeout = config.get("WORKER_HEARTBEAT_TIMEOUT", 60)
        self.health_check_interval = config.get("WORKER_HEALTH_CHECK_INTERVAL", 30)
        self.lock = Lock()
        self.health_checker_thread = None
        self.stop_event = Event()

    def register_worker(self, worker_data: Dict[str, Any]) -> bool:
        """Register a new worker node"""
        try:
            worker_id = worker_data.get("worker_id")
            if not worker_id:
                self.logger.error("Worker registration missing worker_id")
                return False

            with self.lock:
                worker = WorkerNode(
                    worker_id=worker_id,
                    host=worker_data.get("host", "localhost"),
                    port=worker_data.get("port", 8001),
                    capabilities=worker_data.get("capabilities", []),
                )
                worker.max_tasks = worker_data.get("max_tasks", 5)
                worker.status = WorkerStatus.HEALTHY
                worker.update_heartbeat()
                worker.metadata = worker_data.get("metadata", {})

                self.workers[worker_id] = worker

            self.logger.info(
                f"Registered worker: {worker_id} at {worker.host}:{worker.port}"
            )
            return True
        except Exception as e:
            self.logger.error(f"Error registering worker: {e}")
            return False

    def unregister_worker(self, worker_id: str) -> bool:
        """Unregister a worker node"""
        try:
            with self.lock:
                if worker_id in self.workers:
                    del self.workers[worker_id]
                    self.logger.info(f"Unregistered worker: {worker_id}")
                    return True
                return False
        except Exception as e:
            self.logger.error(f"Error unregistering worker: {e}")
            return False

    def update_worker_heartbeat(
        self, worker_id: str, data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update worker heartbeat"""
        try:
            with self.lock:
                if worker_id not in self.workers:
                    self.logger.warning(f"Heartbeat from unknown worker: {worker_id}")
                    return False

                worker = self.workers[worker_id]
                task_count = data.get("current_tasks") if data else None
                processing_time = data.get("average_processing_time") if data else None

                worker.update_heartbeat(task_count, processing_time)
                worker.status = WorkerStatus.HEALTHY

                if data:
                    worker.total_processed = data.get(
                        "total_processed", worker.total_processed
                    )
                    worker.error_count = data.get("error_count", worker.error_count)

            return True
        except Exception as e:
            self.logger.error(f"Error updating worker heartbeat: {e}")
            return False

    def get_workers(self) -> List[WorkerNode]:
        """Get list of all workers"""
        with self.lock:
            return list(self.workers.values())

    def get_healthy_workers(self) -> List[WorkerNode]:
        """Get list of healthy workers"""
        return [w for w in self.get_workers() if w.status == WorkerStatus.HEALTHY]

    def start_health_monitoring(self) -> None:
        """Start health monitoring thread"""
        if self.health_checker_thread and self.health_checker_thread.is_alive():
            return

        self.stop_event.clear()
        self.health_checker_thread = threading.Thread(
            target=self._health_checker, daemon=True
        )
        self.health_checker_thread.start()
        self.logger.info("Started worker health monitoring")

    def stop_health_monitoring(self) -> None:
        """Stop health monitoring thread"""
        self.stop_event.set()
        if self.health_checker_thread and self.health_checker_thread.is_alive():
            self.health_checker_thread.join(timeout=5.0)
        self.logger.info("Stopped worker health monitoring")

    def _health_checker(self) -> None:
        """Health checker thread function"""
        while not self.stop_event.is_set():
            try:
                current_time = time.time()

                with self.lock:
                    for worker in self.workers.values():
                        time_since_heartbeat = current_time - worker.last_heartbeat

                        if time_since_heartbeat > self.heartbeat_timeout:
                            if worker.status != WorkerStatus.OFFLINE:
                                worker.status = WorkerStatus.OFFLINE
                                self.logger.warning(
                                    f"Worker {worker.worker_id} marked as offline (no heartbeat for {time_since_heartbeat:.1f}s)"
                                )
                        elif time_since_heartbeat > self.heartbeat_timeout * 0.8:
                            if worker.status == WorkerStatus.HEALTHY:
                                worker.status = WorkerStatus.UNHEALTHY
                                self.logger.warning(
                                    f"Worker {worker.worker_id} marked as unhealthy"
                                )

                # Sleep with responsive shutdown checking
                sleep_remaining = self.health_check_interval
                while sleep_remaining > 0 and not self.stop_event.is_set():
                    sleep_time = min(1.0, sleep_remaining)
                    time.sleep(sleep_time)
                    sleep_remaining -= sleep_time

            except Exception as e:
                self.logger.error(f"Error in health checker: {e}")
                time.sleep(5.0)


class CentralizedConfigManager:
    """Centralized configuration management for distributed system"""

    def __init__(self, config_file: str):
        self.config_file = config_file
        self.logger = logging.getLogger("zeek_yara.distributed.ConfigManager")
        self.config_data = {}
        self.lock = Lock()
        self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        try:
            with open(self.config_file, "r") as f:
                with self.lock:
                    self.config_data = json.load(f)
            self.logger.info(f"Loaded configuration from {self.config_file}")
            return self.config_data.copy()
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            return {}

    def save_config(self) -> bool:
        """Save configuration to file"""
        try:
            with self.lock:
                with open(self.config_file, "w") as f:
                    json.dump(self.config_data, f, indent=2)
            self.logger.info(f"Saved configuration to {self.config_file}")
            return True
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")
            return False

    def get_config(self, key: str = None) -> Any:
        """Get configuration value"""
        with self.lock:
            if key is None:
                return self.config_data.copy()
            return self.config_data.get(key)

    def set_config(self, key: str, value: Any) -> bool:
        """Set configuration value"""
        try:
            with self.lock:
                self.config_data[key] = value
            return True
        except Exception as e:
            self.logger.error(f"Error setting configuration {key}: {e}")
            return False

    def update_config(self, updates: Dict[str, Any]) -> bool:
        """Update multiple configuration values"""
        try:
            with self.lock:
                self.config_data.update(updates)
            return True
        except Exception as e:
            self.logger.error(f"Error updating configuration: {e}")
            return False


class DistributedScanner:
    """Main distributed scanner orchestrator"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger("zeek_yara.distributed.DistributedScanner")

        # Initialize components
        self.message_queue = self._create_message_queue()
        self.worker_manager = WorkerNodeManager(config)
        self.load_balancer = LoadBalancer(config)
        self.config_manager = CentralizedConfigManager(
            config.get("DISTRIBUTED_CONFIG_FILE", "config/distributed_config.json")
        )

        self.running = False
        self.task_consumer_thread = None
        self.stop_event = Event()

    def _create_message_queue(self) -> MessageQueueManager:
        """Create message queue based on configuration"""
        queue_type = self.config.get("MESSAGE_QUEUE_TYPE", "memory").lower()

        if queue_type == MessageQueueType.RABBITMQ.value:
            if not RABBITMQ_AVAILABLE:
                self.logger.warning(
                    "RabbitMQ requested but not available, falling back to in-memory"
                )
                return InMemoryMessageQueue(self.config)
            return RabbitMQMessageQueue(self.config)
        elif queue_type == MessageQueueType.KAFKA.value:
            if not KAFKA_AVAILABLE:
                self.logger.warning(
                    "Kafka requested but not available, falling back to in-memory"
                )
                return InMemoryMessageQueue(self.config)
            return KafkaMessageQueue(self.config)
        else:
            return InMemoryMessageQueue(self.config)

    def start(self) -> bool:
        """Start the distributed scanner system"""
        if self.running:
            self.logger.warning("Distributed scanner is already running")
            return False

        try:
            # Connect to message queue
            if not self.message_queue.connect():
                self.logger.error("Failed to connect to message queue")
                return False

            # Start worker health monitoring
            self.worker_manager.start_health_monitoring()

            # Start task consumer
            self.stop_event.clear()
            self.task_consumer_thread = threading.Thread(
                target=self._task_consumer, daemon=True
            )
            self.task_consumer_thread.start()

            self.running = True
            self.logger.info("Distributed scanner system started")
            return True

        except Exception as e:
            self.logger.error(f"Error starting distributed scanner: {e}")
            self.stop()
            return False

    def stop(self) -> None:
        """Stop the distributed scanner system"""
        if not self.running:
            return

        try:
            self.stop_event.set()

            # Stop worker health monitoring
            self.worker_manager.stop_health_monitoring()

            # Wait for task consumer to finish
            if self.task_consumer_thread and self.task_consumer_thread.is_alive():
                self.task_consumer_thread.join(timeout=5.0)

            # Disconnect from message queue
            self.message_queue.disconnect()

            self.running = False
            self.logger.info("Distributed scanner system stopped")

        except Exception as e:
            self.logger.error(f"Error stopping distributed scanner: {e}")

    def submit_scan_task(
        self,
        file_path: str,
        priority: int = TaskPriority.NORMAL.value,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Submit a file scan task to the distributed system"""
        task_id = str(uuid.uuid4())

        task = {
            "task_id": task_id,
            "type": "file_scan",
            "file_path": file_path,
            "priority": priority,
            "submitted_at": time.time(),
            "metadata": metadata or {},
        }

        if self.message_queue.publish_task(task, priority):
            self.logger.info(f"Submitted scan task {task_id} for file: {file_path}")
            return task_id
        else:
            self.logger.error(f"Failed to submit scan task for file: {file_path}")
            return None

    def _task_consumer(self) -> None:
        """Task consumer thread that distributes tasks to workers"""

        def task_handler(task: Dict[str, Any]) -> None:
            try:
                # Select worker for task
                workers = self.worker_manager.get_healthy_workers()
                worker = self.load_balancer.select_worker(workers, task)

                if not worker:
                    self.logger.warning(
                        f"No available workers for task {task.get('task_id', 'unknown')}"
                    )
                    # Could re-queue the task here or handle differently
                    return

                # Send task to worker (simplified - in real implementation would use HTTP/gRPC)
                self.logger.info(
                    f"Assigned task {task.get('task_id', 'unknown')} to worker {worker.worker_id}"
                )

                # Update worker task count
                worker.current_tasks += 1

            except Exception as e:
                self.logger.error(f"Error handling task: {e}")

        # Start consuming tasks
        self.message_queue.consume_tasks(task_handler)

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        workers = self.worker_manager.get_workers()
        healthy_workers = [w for w in workers if w.status == WorkerStatus.HEALTHY]

        return {
            "running": self.running,
            "message_queue": {
                "type": self.config.get("MESSAGE_QUEUE_TYPE", "memory"),
                "queue_size": self.message_queue.get_queue_size(),
            },
            "workers": {
                "total": len(workers),
                "healthy": len(healthy_workers),
                "workers": [w.to_dict() for w in workers],
            },
            "load_balancer": {"algorithm": self.load_balancer.algorithm},
            "config": self.config_manager.get_config(),
        }
