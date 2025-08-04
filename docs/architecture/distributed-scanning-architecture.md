# Distributed Scanning Architecture

## Overview

The Zeek-YARA Integration platform now supports enterprise-scale distributed scanning through a comprehensive architecture that enables horizontal scaling, fault tolerance, and high-throughput processing.

## Architecture Components

### 1. Core Components

#### Distributed Scanner (`PLATFORM/core/distributed.py`)
- **DistributedScanner**: Main orchestrator coordinating all distributed components
- **MessageQueueManager**: Abstract interface supporting multiple queue backends
- **WorkerNodeManager**: Manages worker registration, health monitoring, and lifecycle
- **LoadBalancer**: Distributes tasks using configurable algorithms
- **CentralizedConfigManager**: JSON-based configuration management

#### Monitoring System (`PLATFORM/core/monitoring.py`)
- **MetricsCollector**: Real-time metrics collection with time-series storage
- **AlertManager**: Configurable alerting with multiple severity levels
- **PerformanceTracker**: Trend analysis and baseline performance tracking
- **HealthChecker**: Comprehensive health checks across all components

#### Worker Node (`TOOLS/cli/distributed_worker.py`)
- **DistributedWorker**: Standalone worker implementation
- Automatic registration and heartbeat mechanism
- REST API for task reception and status reporting
- Graceful shutdown and error handling

### 2. Message Queue Backends

#### In-Memory Queue
- Development and testing environments
- Python Queue-based implementation
- Task prioritization support
- No external dependencies

#### RabbitMQ Integration
- Production-ready message queuing
- Durable queues and persistent messages
- Task prioritization and dead letter queues
- Automatic retry mechanisms

#### Apache Kafka Integration
- High-throughput enterprise scenarios
- Distributed commit log architecture
- Horizontal scaling capabilities
- Consumer group management

### 3. Load Balancing Algorithms

#### Load-Based Distribution
- Real-time worker capacity monitoring
- CPU, memory, and queue-based load factors
- Automatic load calculation and distribution

#### Round-Robin Distribution
- Even task distribution across workers
- Simple and predictable task allocation
- Suitable for homogeneous worker environments

#### Capability-Based Distribution
- Worker specialization support
- Task routing based on required capabilities
- Fallback to load-based when capabilities match

## API Endpoints

### Distributed Operations

#### System Management
- `POST /distributed/start` - Start distributed system
- `POST /distributed/stop` - Stop distributed system
- `GET /distributed/status` - Get comprehensive system status

#### Worker Management
- `POST /distributed/workers/register` - Register new worker node
- `DELETE /distributed/workers/{worker_id}` - Unregister worker
- `GET /distributed/workers` - List all registered workers
- `PUT /distributed/workers/{worker_id}/heartbeat` - Update worker heartbeat

#### Task Management
- `POST /distributed/scan` - Submit scan task to distributed system

### Monitoring Operations

#### Metrics and Performance
- `GET /monitoring/metrics` - Current system metrics
- `GET /monitoring/metrics/summary` - Time-windowed metric summaries
- `POST /monitoring/export` - Export metrics to file
- `GET /monitoring/dashboard` - Comprehensive monitoring dashboard

#### Alert Management
- `GET /monitoring/alerts` - Active alerts and history
- `POST /monitoring/alerts/{alert_id}/resolve` - Resolve specific alert

## Configuration

### Core Configuration (`config/default_config.json`)

```json
{
  "DISTRIBUTED_ENABLED": false,
  "MESSAGE_QUEUE_TYPE": "memory",
  "WORKER_HEARTBEAT_TIMEOUT": 60,
  "WORKER_HEALTH_CHECK_INTERVAL": 30,
  "LOAD_BALANCE_ALGORITHM": "load_based",
  
  "MONITORING_ENABLED": true,
  "METRICS_COLLECTION_INTERVAL": 30,
  "MONITORING_INTERVAL": 60,
  
  "ALERT_HIGH_ERROR_RATE": 0.1,
  "ALERT_HIGH_QUEUE_SIZE": 100,
  "ALERT_LOW_THROUGHPUT": 1.0
}
```

### Distributed Configuration (`config/distributed_config.json`)

```json
{
  "system_id": "zeek-yara-distributed",
  "deployment": {
    "environment": "development",
    "region": "local",
    "cluster_name": "default"
  },
  "worker_defaults": {
    "max_tasks": 5,
    "threads": 2,
    "capabilities": ["file_scan", "yara_analysis"]
  },
  "load_balancing": {
    "algorithm": "load_based"
  },
  "monitoring": {
    "enabled": true,
    "metrics_retention_hours": 24
  }
}
```

## Deployment Guide

### Master Node Setup

1. **Enable Distributed Mode**
   ```bash
   # Update configuration
   export DISTRIBUTED_ENABLED=true
   export MESSAGE_QUEUE_TYPE=rabbitmq  # or kafka
   export MONITORING_ENABLED=true
   ```

2. **Start Master Node**
   ```bash
   # Start API server with distributed support
   python -m PLATFORM.api.api_server
   ```

3. **Verify Master Status**
   ```bash
   curl -X GET "http://localhost:8000/distributed/status"
   ```

### Worker Node Deployment

1. **Start Individual Workers**
   ```bash
   python TOOLS/cli/distributed_worker.py \
     --worker-id worker-01 \
     --master-host localhost \
     --master-port 8000 \
     --worker-port 8001 \
     --max-tasks 5 \
     --threads 2
   ```

2. **Multiple Worker Deployment**
   ```bash
   # Start multiple workers on different ports
   for i in {1..5}; do
     python TOOLS/cli/distributed_worker.py \
       --worker-id worker-$(printf "%02d" $i) \
       --worker-port $((8000 + $i)) \
       --max-tasks 5 &
   done
   ```

3. **Verify Worker Registration**
   ```bash
   curl -X GET "http://localhost:8000/distributed/workers"
   ```

### Message Queue Setup

#### RabbitMQ Setup
```bash
# Install RabbitMQ
sudo apt-get install rabbitmq-server

# Start RabbitMQ service
sudo systemctl start rabbitmq-server

# Enable management plugin (optional)
sudo rabbitmq-plugins enable rabbitmq_management

# Configure Zeek-YARA
export MESSAGE_QUEUE_TYPE=rabbitmq
export RABBITMQ_HOST=localhost
export RABBITMQ_PORT=5672
```

#### Kafka Setup
```bash
# Download and start Kafka
wget https://downloads.apache.org/kafka/2.8.0/kafka_2.13-2.8.0.tgz
tar -xzf kafka_2.13-2.8.0.tgz
cd kafka_2.13-2.8.0

# Start Zookeeper
bin/zookeeper-server-start.sh config/zookeeper.properties &

# Start Kafka
bin/kafka-server-start.sh config/server.properties &

# Configure Zeek-YARA
export MESSAGE_QUEUE_TYPE=kafka
export KAFKA_BOOTSTRAP_SERVERS=localhost:9092
```

## Usage Examples

### Submit Scan Tasks

```bash
# Submit high-priority scan
curl -X POST "http://localhost:8000/distributed/scan" \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/path/to/suspicious/file.exe",
    "priority": 8,
    "metadata": {"source": "email_attachment"}
  }'
```

### Monitor System Performance

```bash
# Get current metrics
curl -X GET "http://localhost:8000/monitoring/metrics"

# Get monitoring dashboard
curl -X GET "http://localhost:8000/monitoring/dashboard"

# Export metrics
curl -X POST "http://localhost:8000/monitoring/export" \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/tmp/metrics_export.json",
    "format": "json"
  }'
```

### Worker Health Monitoring

```bash
# Check worker health
curl -X GET "http://localhost:8000/distributed/workers"

# Manual heartbeat (normally automatic)
curl -X PUT "http://localhost:8000/distributed/workers/worker-01/heartbeat" \
  -H "Content-Type: application/json" \
  -d '{
    "current_tasks": 2,
    "total_processed": 150,
    "error_count": 1,
    "average_processing_time": 2.5
  }'
```

## Monitoring and Alerting

### Key Metrics

#### System Metrics
- CPU usage percentage
- Memory utilization
- Disk space usage
- Network I/O statistics

#### Worker Metrics
- Active worker count
- Worker load distribution
- Task processing rates
- Error rates per worker

#### Queue Metrics
- Queue size and throughput
- Message processing latency
- Dead letter queue statistics

#### Performance Metrics
- Scan throughput (files/second)
- Average processing time
- 95th percentile response times
- System availability

### Alert Thresholds

#### Default Alert Rules
- High error rate: > 10%
- High queue size: > 100 tasks
- Low throughput: < 1 file/second
- Worker offline: Any worker unavailable
- High CPU usage: > 80%
- High memory usage: > 80%
- Low disk space: > 90% used

#### Custom Alert Configuration
```python
# Add custom alert rule via API
alert_manager.add_alert_rule("custom_threshold", {
    "metric": "scanner.custom_metric",
    "condition": ">",
    "threshold": 50,
    "level": AlertLevel.WARNING,
    "message": "Custom metric exceeded: {value}"
})
```

## Scaling Guidelines

### Horizontal Scaling

#### Worker Scaling
- Add workers dynamically during high load
- Remove workers during low usage periods
- Consider worker specialization for different file types

#### Queue Scaling
- RabbitMQ: Use clustering for high availability
- Kafka: Increase partition count for parallelism
- Monitor queue size and adjust worker count accordingly

### Vertical Scaling

#### Master Node Resources
- CPU: 4+ cores for API processing
- Memory: 8GB+ for metrics and state management
- Storage: SSD for fast database operations

#### Worker Node Resources
- CPU: 2+ cores per worker
- Memory: 4GB+ for YARA rule processing
- Storage: Local SSD for temporary file operations

### Performance Optimization

#### Queue Configuration
```json
{
  "MAX_QUEUE_SIZE": 1000,
  "QUEUE_TIMEOUT_NORMAL": 1.0,
  "QUEUE_TIMEOUT_PRIORITY": 0.1,
  "BATCH_SIZE": 10
}
```

#### Worker Tuning
```json
{
  "MAX_TASKS": 5,
  "THREADS": 2,
  "HEARTBEAT_INTERVAL": 30,
  "PROCESSING_TIMEOUT": 60
}
```

#### Load Balancer Optimization
```json
{
  "ALGORITHM": "load_based",
  "CPU_WEIGHT": 0.3,
  "MEMORY_WEIGHT": 0.3,
  "QUEUE_WEIGHT": 0.4
}
```

## Troubleshooting

### Common Issues

#### Worker Registration Failures
```bash
# Check master node connectivity
curl -X GET "http://master-host:8000/status"

# Verify worker configuration
python TOOLS/cli/distributed_worker.py --help

# Check network connectivity
telnet master-host 8000
```

#### High Queue Backlog
1. **Add More Workers**
   ```bash
   # Scale up worker count
   for i in {6..10}; do
     python TOOLS/cli/distributed_worker.py --worker-id worker-$i &
   done
   ```

2. **Optimize Worker Performance**
   ```bash
   # Increase worker capacity
   python TOOLS/cli/distributed_worker.py --max-tasks 10 --threads 4
   ```

3. **Check Resource Constraints**
   ```bash
   # Monitor system resources
   curl -X GET "http://localhost:8000/monitoring/metrics"
   ```

#### Message Queue Issues

##### RabbitMQ Problems
```bash
# Check RabbitMQ status
sudo systemctl status rabbitmq-server

# View queue statistics
sudo rabbitmqctl list_queues

# Purge problematic queue
sudo rabbitmqctl purge_queue zeek_yara_tasks
```

##### Kafka Problems
```bash
# Check Kafka topics
bin/kafka-topics.sh --list --bootstrap-server localhost:9092

# Check consumer group status
bin/kafka-consumer-groups.sh --bootstrap-server localhost:9092 --describe --group zeek-yara-workers

# Reset consumer group offset
bin/kafka-consumer-groups.sh --bootstrap-server localhost:9092 --group zeek-yara-workers --reset-offsets --to-earliest --topic zeek-yara-tasks --execute
```

### Performance Debugging

#### Slow Processing
1. **Identify Bottlenecks**
   ```bash
   # Get detailed performance metrics
   curl -X GET "http://localhost:8000/monitoring/metrics/summary?time_window=3600"
   ```

2. **Check Worker Distribution**
   ```bash
   # Analyze worker load
   curl -X GET "http://localhost:8000/distributed/workers" | jq '.workers[] | {id: .worker_id, load: .load_factor, tasks: .current_tasks}'
   ```

3. **Review System Resources**
   ```bash
   # Monitor system performance
   curl -X GET "http://localhost:8000/monitoring/dashboard"
   ```

#### Memory Issues
```bash
# Check worker memory usage
ps aux | grep distributed_worker

# Monitor memory trends
curl -X GET "http://localhost:8000/monitoring/metrics" | jq '.metrics.gauges.memory_percent'

# Restart workers if memory leaks detected
pkill -f distributed_worker
```

## Security Considerations

### Network Security
- Use TLS/SSL for all inter-node communication
- Implement network segmentation between master and workers
- Configure firewall rules to restrict access

### Authentication and Authorization
```json
{
  "security": {
    "require_worker_authentication": true,
    "api_key_required": true,
    "allowed_worker_ips": ["10.0.1.0/24"],
    "ssl_enabled": true
  }
}
```

### Data Protection
- Encrypt message queue communications
- Implement secure credential storage
- Regular security audits and updates

### Access Control
- Role-based access to API endpoints
- Worker-specific capability restrictions
- Audit logging for all operations

## Integration Examples

### Docker Deployment
```dockerfile
# Master node
FROM python:3.12
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
ENV DISTRIBUTED_ENABLED=true
CMD ["python", "-m", "PLATFORM.api.api_server"]
```

### Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: zeek-yara-master
spec:
  replicas: 1
  selector:
    matchLabels:
      app: zeek-yara-master
  template:
    metadata:
      labels:
        app: zeek-yara-master
    spec:
      containers:
      - name: master
        image: zeek-yara:latest
        env:
        - name: DISTRIBUTED_ENABLED
          value: "true"
        - name: MESSAGE_QUEUE_TYPE
          value: "kafka"
```

### Cloud Integration
- AWS: Use SQS for message queuing, ECS for worker deployment
- Azure: Use Service Bus for messaging, Container Instances for workers  
- GCP: Use Pub/Sub for messaging, Cloud Run for workers

## Future Enhancements

### Planned Features
- Auto-scaling based on queue metrics
- Advanced worker specialization
- Cross-region deployment support
- Machine learning-based load prediction
- Integration with container orchestration platforms

### Performance Improvements
- Connection pooling optimizations
- Batch processing capabilities
- Caching mechanisms
- Compression for message payloads

### Enterprise Features
- Role-based access control
- Advanced audit logging
- Multi-tenant support
- SLA monitoring and reporting

## Conclusion

The distributed scanning architecture transforms the Zeek-YARA integration from a single-node solution into an enterprise-scale security platform capable of handling massive traffic volumes while maintaining high availability, performance, and reliability.

The modular design allows for flexible deployment scenarios, from development environments using in-memory queues to production deployments with RabbitMQ or Kafka, multiple worker nodes, and comprehensive monitoring.

This architecture provides the foundation for scaling security operations to meet enterprise demands while maintaining the defensive security focus that makes this platform valuable for network monitoring and threat detection.