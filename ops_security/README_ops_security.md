# Operational Security (运维安全专项)

## 🇬🇧 English Summary
This folder contains documentation for the *Operational Security* tasks in Phase III.

**Contents:**
- threat_model.png – Tatou threat model diagram
- monitoring_diagram.png – Monitoring architecture (Prometheus + Grafana + Blackbox + Tatou)
- ops_log_examples.txt – Extracted logs from security.log
- README_ops_security.md – This overview file

**Summary:**
- Implemented Prometheus + Grafana + Blackbox monitoring for /api/health
- probe_success=1 confirms server uptime
- Logs include access, error, and monitoring events
- Meets operational security assessment requirements

---

## 🇨🇳 中文摘要
此文件夹包含 *运维安全专项任务* 的文档与证据。

**包含文件：**
- `threat_model.png`：威胁建模图  
- `monitoring_diagram.png`：Prometheus + Grafana + Blackbox + Tatou 架构图  
- `ops_log_examples.txt`：从 security.log 中提取的访问与错误日志  
- `README_ops_security.md`：本说明文件  

**完成摘要：**
- 成功部署 Prometheus + Grafana 监控 `/api/health` 接口  
- Blackbox Exporter 探测 HTTP 状态并上报 `probe_success`  
- Grafana 可视化监控可用性  
- 强化安全日志记录与异常检测机制  
