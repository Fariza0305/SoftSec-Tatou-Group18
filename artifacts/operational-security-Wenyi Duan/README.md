# Operational Security Artifacts - Wenyi Duan

## Specialization D: Operational Security (Threat Modeling, Logging & Monitoring)

This folder contains all operational security artifacts developed by Wenyi Duan, focusing on threat modeling, logging, and monitoring for the Tatou PDF Watermarking Platform.

## Contents

### Threat Modeling
- **threat_model.png** - Visual representation of the system threat model
  - Identifies threat actors and attack vectors
  - Maps trust boundaries and data flows
  - Highlights critical security controls

### Monitoring Infrastructure
Located in `monitoring/` directory:

#### Prometheus Configuration
- **prometheus.yml** - Prometheus monitoring configuration
  - Service health monitoring
  - Performance metrics collection
  - Alert rules configuration

#### Blackbox Exporter
- **blackbox.yml** - Blackbox exporter configuration for external monitoring
  - HTTP endpoint availability checks
  - Response time monitoring
  - SSL/TLS certificate validation

#### Monitoring Scripts
- **start_monitoring.sh** - Script to initialize monitoring stack
  - Starts Prometheus and exporters
  - Configures scraping intervals
  - Sets up alerting

### Logging
- **ops_log_examples.txt** - Sample operational logs demonstrating:
  - Security event logging
  - Access logs
  - Error and exception logging
  - Audit trail examples

### Documentation
- **README_ops_security.md** - Operational security overview and guidelines

## Key Components

### 1. Threat Model
The threat model identifies:
- **External Threats**: Unauthorized access, data exfiltration, API abuse
- **Internal Threats**: Privilege escalation, data tampering
- **Attack Vectors**: XSS, SQL injection, path traversal, XXE
- **Mitigations**: Input validation, authentication, rate limiting, encryption

### 2. Monitoring Strategy
Implemented comprehensive monitoring covering:
- **Availability**: Service uptime and health checks
- **Performance**: Response times, resource utilization
- **Security**: Failed login attempts, suspicious patterns
- **Compliance**: Audit logs for regulatory requirements

### 3. Logging Framework
Structured logging approach including:
- **Application Logs**: Debug, info, warning, error levels
- **Security Logs**: Authentication events, authorization failures
- **Audit Logs**: User actions, data modifications
- **Access Logs**: API endpoint access patterns

## Monitoring Architecture

```
┌─────────────────┐
│   Application   │──┐
└─────────────────┘  │
                     │ Metrics
┌─────────────────┐  │
│    Database     │──┤
└─────────────────┘  │
                     ▼
                ┌────────────┐      ┌──────────┐
                │ Prometheus │─────▶│ Alerting │
                └────────────┘      └──────────┘
                     ▲
                     │
                ┌────────────┐
                │  Blackbox  │
                │  Exporter  │
                └────────────┘
```

## Security Events Monitored

1. **Authentication Events**
   - Login attempts (successful/failed)
   - Session creation/termination
   - Password changes

2. **Authorization Events**
   - Access denied events
   - Privilege escalation attempts
   - Resource access patterns

3. **Security Violations**
   - Input validation failures
   - Rate limit exceeded
   - Suspicious payloads detected

4. **System Health**
   - Service availability
   - Database connectivity
   - Resource exhaustion

## Alert Configuration

Alerts are configured for:
- Service downtime > 1 minute
- Failed login attempts > 5 in 5 minutes
- High error rate > 10% of requests
- Database connection failures
- SSL certificate expiration < 30 days

## Usage

### Starting Monitoring
```bash
cd monitoring
./start_monitoring.sh
```

### Accessing Metrics
- Prometheus UI: http://localhost:9090
- Metrics endpoint: http://localhost:5000/metrics

### Viewing Logs
```bash
# View application logs
docker compose logs -f server

# View security logs
grep "SECURITY" logs/*.log

# View audit logs
grep "AUDIT" logs/*.log
```

## Key Achievements

1. **Comprehensive Threat Model**: Identified and documented all major threats
2. **Monitoring Infrastructure**: Deployed Prometheus-based monitoring stack
3. **Structured Logging**: Implemented consistent logging framework
4. **Alert System**: Configured actionable alerts for security events
5. **Documentation**: Created operational runbooks and procedures

## Best Practices Implemented

- Defense in depth through multiple security layers
- Continuous monitoring of security-critical events
- Centralized log aggregation
- Real-time alerting for anomalies
- Regular security metric reviews

## Contact
Wenyi Duan - Operational Security Specialization

