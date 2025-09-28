# 🤖 03_FUTURES_AUTOMATION_SETUP.md

**Binance USDT Perpetual Futures 전용 Freqtrade AI 시스템의 완전 자동화 설정 전문가급 가이드**

<div align="center">

[![Automation](https://img.shields.io/badge/Automation-100%25-green?style=for-the-badge&logo=docker)](https://docs.freqtrade.io/)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-Ready-blue?style=for-the-badge&logo=kubernetes)](https://kubernetes.io/)
[![CI/CD](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-orange?style=for-the-badge&logo=githubactions)](https://github.com/features/actions)
[![Monitoring](https://img.shields.io/badge/Monitoring-24%2F7-red?style=for-the-badge&logo=grafana)](https://grafana.com/)

**🎯 목표: 24시간 무중단 무인 운영 가능한 엔터프라이즈급 완전 자동화 시스템 구축**

</div>

---

## 📋 **목차**

1. [🏗️ 완전 자동화 아키텍처](#️-완전-자동화-아키텍처) (40분 읽기)
2. [🐳 Docker 컨테이너 오케스트레이션](#-docker-컨테이너-오케스트레이션) (45분)
3. [🔄 CI/CD 파이프라인 구축](#-cicd-파이프라인-구축) (50분)
4. [🎯 멀티 전략 관리 시스템](#-멀티-전략-관리-시스템) (55분)
5. [📊 실시간 데이터 파이프라인](#-실시간-데이터-파이프라인) (60분)
6. [📢 통합 알림 시스템](#-통합-알림-시스템) (65분)
7. [🔄 자동 장애 복구 시스템](#-자동-장애-복구-시스템) (70분)
8. [⚡ 성과 최적화 자동화](#-성과-최적화-자동화) (75분)
9. [🔐 보안 및 컴플라이언스](#-보안-및-컴플라이언스) (80분)
10. [🚀 운영 및 유지보수 자동화](#-운영-및-유지보수-자동화) (85분)

---

## 🏗️ **완전 자동화 아키텍처**

### 📐 **마이크로서비스 기반 설계**

```mermaid
graph TB
    subgraph "Load Balancer Layer"
        LB[HAProxy/Nginx]
    end
    
    subgraph "API Gateway"
        AG[Kong/Ambassador]
    end
    
    subgraph "Core Services"
        FT1[Freqtrade Instance 1]
        FT2[Freqtrade Instance 2]
        FT3[Freqtrade Instance N]
    end
    
    subgraph "Data Layer"
        TS[TimescaleDB]
        RD[Redis Cluster]
        ES[Elasticsearch]
    end
    
    subgraph "Message Queue"
        RMQ[RabbitMQ Cluster]
        KF[Apache Kafka]
    end
    
    subgraph "Monitoring Stack"
        PR[Prometheus]
        GF[Grafana]
        JG[Jaeger]
        ELK[ELK Stack]
    end
    
    subgraph "External APIs"
        BA[Binance API]
        TG[Telegram API]
        SL[Slack API]
    end
    
    LB --> AG
    AG --> FT1
    AG --> FT2
    AG --> FT3
    
    FT1 --> TS
    FT2 --> TS
    FT3 --> TS
    
    FT1 --> RD
    FT2 --> RD
    FT3 --> RD
    
    FT1 --> RMQ
    FT2 --> RMQ
    FT3 --> RMQ
    
    RMQ --> KF
    
    FT1 --> BA
    FT2 --> BA
    FT3 --> BA
    
    style FT1 fill:#27ae60
    style FT2 fill:#27ae60
    style FT3 fill:#27ae60
    style TS fill:#3498db
    style RD fill:#e74c3c
    style BA fill:#f9d71c
```

### 🎯 **이벤트 드리븐 아키텍처**

```python
# automation/event_driven_core.py
import asyncio
import json
from typing import Dict, List, Callable, Any
from dataclasses import dataclass, asdict
from enum import Enum
import aioredis
import aiokafka

class EventType(Enum):
    """이벤트 타입 정의"""
    TRADE_SIGNAL = "trade_signal"
    POSITION_UPDATE = "position_update"
    RISK_ALERT = "risk_alert"
    SYSTEM_STATUS = "system_status"
    MARKET_DATA_UPDATE = "market_data_update"
    STRATEGY_PERFORMANCE = "strategy_performance"
    FUNDING_RATE_UPDATE = "funding_rate_update"
    LIQUIDATION_WARNING = "liquidation_warning"

@dataclass
class Event:
    """이벤트 데이터 클래스"""
    event_id: str
    event_type: EventType
    source: str
    timestamp: float
    data: Dict[str, Any]
    metadata: Dict[str, Any] = None

class EventBus:
    """중앙 이벤트 버스"""
    
    def __init__(self, redis_url: str, kafka_bootstrap_servers: str):
        self.redis_url = redis_url
        self.kafka_servers = kafka_bootstrap_servers
        self.subscribers: Dict[EventType, List[Callable]] = {}
        self.redis_pool = None
        self.kafka_producer = None
        self.kafka_consumer = None
        
    async def initialize(self):
        """이벤트 버스 초기화"""
        # Redis 연결
        self.redis_pool = aioredis.ConnectionPool.from_url(self.redis_url)
        
        # Kafka Producer 초기화
        self.kafka_producer = aiokafka.AIOKafkaProducer(
            bootstrap_servers=self.kafka_servers,
            value_serializer=lambda x: json.dumps(asdict(x) if isinstance(x, Event) else x).encode()
        )
        await self.kafka_producer.start()
        
        # Kafka Consumer 초기화
        self.kafka_consumer = aiokafka.AIOKafkaConsumer(
            'freqtrade-events',
            bootstrap_servers=self.kafka_servers,
            value_deserializer=lambda m: json.loads(m.decode())
        )
        await self.kafka_consumer.start()
    
    async def publish(self, event: Event):
        """이벤트 발행"""
        # Kafka로 이벤트 전송
        await self.kafka_producer.send('freqtrade-events', event)
        
        # Redis로 실시간 이벤트 전송 (즉시 처리용)
        redis = aioredis.Redis(connection_pool=self.redis_pool)
        await redis.publish('realtime-events', json.dumps(asdict(event)))
    
    def subscribe(self, event_type: EventType, handler: Callable):
        """이벤트 구독"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(handler)
    
    async def process_events(self):
        """이벤트 처리 루프"""
        async for msg in self.kafka_consumer:
            event_data = msg.value
            event = Event(**event_data)
            
            # 해당 이벤트 타입 구독자들에게 전달
            if event.event_type in self.subscribers:
                for handler in self.subscribers[event.event_type]:
                    try:
                    # 로컬 이미지 정보
                    local_result = subprocess.run(
                        ['docker', 'image', 'inspect', image],
                        capture_output=True, text=True
                    )
                    
                    if local_result.returncode == 0:
                        local_info = json.loads(local_result.stdout)[0]
                        local_digest = local_info.get('RepoDigests', [''])[0]
                        
                        # 원격 이미지 정보
                        remote_result = subprocess.run(
                            ['docker', 'manifest', 'inspect', image],
                            capture_output=True, text=True
                        )
                        
                        if remote_result.returncode == 0:
                            remote_info = json.loads(remote_result.stdout)
                            remote_digest = remote_info.get('config', {}).get('digest', '')
                            
                            # 다이제스트 비교
                            if local_digest != remote_digest:
                                update = UpdatePackage(
                                    name=image,
                                    current_version=local_digest[:12] if local_digest else "unknown",
                                    new_version=remote_digest[:12] if remote_digest else "latest",
                                    update_type=UpdateType.DOCKER,
                                    auto_install=True,
                                    requires_restart=True
                                )
                                updates.append(update)
                                
                except Exception as e:
                    self.logger.warning(f"Failed to check updates for image {image}: {e}")
                    continue
            
            return updates
            
        except Exception as e:
            self.logger.error(f"Docker update check failed: {e}")
            return []
    
    async def _check_freqtrade_updates(self) -> List[UpdatePackage]:
        """Freqtrade 업데이트 확인"""
        try:
            # GitHub API를 통한 최신 릴리즈 확인
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                async with session.get('https://api.github.com/repos/freqtrade/freqtrade/releases/latest') as resp:
                    if resp.status == 200:
                        release_info = await resp.json()
                        latest_version = release_info['tag_name']
                        
                        # 현재 버전 확인
                        result = subprocess.run(
                            ['freqtrade', '--version'],
                            capture_output=True, text=True
                        )
                        
                        if result.returncode == 0:
                            current_version = result.stdout.strip().split()[-1]
                            
                            if current_version != latest_version:
                                update = UpdatePackage(
                                    name="freqtrade",
                                    current_version=current_version,
                                    new_version=latest_version,
                                    update_type=UpdateType.APPLICATION,
                                    auto_install=False,  # 수동 승인 필요
                                    requires_restart=True
                                )
                                return [update]
            
            return []
            
        except Exception as e:
            self.logger.error(f"Freqtrade update check failed: {e}")
            return []
    
    async def _check_strategy_updates(self) -> List[UpdatePackage]:
        """전략 업데이트 확인"""
        # Git 저장소에서 전략 업데이트 확인
        # 실제 구현에서는 전략 저장소의 변경사항 확인
        return []
    
    def _is_critical_package(self, package_name: str) -> bool:
        """중요 패키지 여부 확인"""
        critical_packages = [
            'linux-image', 'kernel', 'systemd', 'openssh-server',
            'docker', 'postgresql', 'nginx'
        ]
        
        return any(critical in package_name for critical in critical_packages)
    
    async def schedule_maintenance_window(self, start_time: datetime, duration_hours: int, 
                                        update_types: List[UpdateType]):
        """유지보수 윈도우 스케줄링"""
        
        window = {
            'start_time': start_time,
            'end_time': start_time + timedelta(hours=duration_hours),
            'update_types': update_types,
            'status': 'scheduled'
        }
        
        self.maintenance_windows.append(window)
        
        # 스케줄된 업데이트 태스크 생성
        delay = (start_time - datetime.now()).total_seconds()
        if delay > 0:
            asyncio.create_task(self._scheduled_maintenance(window, delay))
        
        self.logger.info(f"Maintenance window scheduled: {start_time} - {window['end_time']}")
    
    async def _scheduled_maintenance(self, window: Dict, delay: float):
        """스케줄된 유지보수 실행"""
        await asyncio.sleep(delay)
        
        try:
            window['status'] = 'in_progress'
            
            # 유지보수 시작 알림
            await self._send_maintenance_notification("started", window)
            
            # 사용 가능한 업데이트 확인
            available_updates = await self.check_available_updates()
            
            # 유지보수 윈도우에 포함된 업데이트 타입만 처리
            updates_to_install = []
            for update_type in window['update_types']:
                updates_to_install.extend(available_updates.get(update_type, []))
            
            # 백업 생성
            backup_success = await self.backup_manager.execute_backup("pre_update_backup")
            if not backup_success:
                self.logger.error("Pre-update backup failed")
                window['status'] = 'failed'
                return
            
            # 업데이트 설치
            success_count = 0
            total_count = len(updates_to_install)
            
            for update in updates_to_install:
                success = await self._install_update(update)
                if success:
                    success_count += 1
            
            # 결과 처리
            if success_count == total_count:
                window['status'] = 'completed'
                await self._send_maintenance_notification("completed", window, {
                    'updates_installed': success_count,
                    'total_updates': total_count
                })
            else:
                window['status'] = 'partial'
                await self._send_maintenance_notification("partial", window, {
                    'updates_installed': success_count,
                    'total_updates': total_count
                })
            
        except Exception as e:
            window['status'] = 'failed'
            self.logger.error(f"Scheduled maintenance failed: {e}")
            await self._send_maintenance_notification("failed", window, {'error': str(e)})
    
    async def _install_update(self, update: UpdatePackage) -> bool:
        """업데이트 설치"""
        
        try:
            self.logger.info(f"Installing update: {update.name} {update.current_version} -> {update.new_version}")
            
            if update.update_type == UpdateType.SYSTEM:
                return await self._install_system_update(update)
            elif update.update_type == UpdateType.DOCKER:
                return await self._install_docker_update(update)
            elif update.update_type == UpdateType.APPLICATION:
                return await self._install_application_update(update)
            elif update.update_type == UpdateType.SECURITY:
                return await self._install_security_update(update)
            
            return False
            
        except Exception as e:
            self.logger.error(f"Update installation failed for {update.name}: {e}")
            return False
    
    async def _install_system_update(self, update: UpdatePackage) -> bool:
        """시스템 업데이트 설치"""
        try:
            cmd = ['apt', 'install', '-y', f"{update.name}={update.new_version}"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            return result.returncode == 0
            
        except Exception as e:
            self.logger.error(f"System update failed: {e}")
            return False
    
    async def _install_docker_update(self, update: UpdatePackage) -> bool:
        """Docker 이미지 업데이트"""
        try:
            # 새 이미지 풀
            pull_result = subprocess.run(
                ['docker', 'pull', update.name],
                capture_output=True, text=True
            )
            
            if pull_result.returncode != 0:
                return False
            
            # 컨테이너 재시작 (Docker Compose 사용)
            restart_result = subprocess.run(
                ['docker', 'compose', 'up', '-d', '--force-recreate'],
                cwd='/opt/freqtrade-futures',
                capture_output=True, text=True
            )
            
            return restart_result.returncode == 0
            
        except Exception as e:
            self.logger.error(f"Docker update failed: {e}")
            return False
    
    async def _install_application_update(self, update: UpdatePackage) -> bool:
        """애플리케이션 업데이트"""
        if update.name == "freqtrade":
            try:
                # Docker 이미지 업데이트로 처리
                docker_update = UpdatePackage(
                    name="freqtradeorg/freqtrade:stable",
                    current_version=update.current_version,
                    new_version=update.new_version,
                    update_type=UpdateType.DOCKER,
                    requires_restart=True
                )
                
                return await self._install_docker_update(docker_update)
                
            except Exception as e:
                self.logger.error(f"Freqtrade update failed: {e}")
                return False
        
        return False
    
    async def _install_security_update(self, update: UpdatePackage) -> bool:
        """보안 업데이트 설치"""
        try:
            # unattended-upgrades 사용
            result = subprocess.run(
                ['unattended-upgrade'],
                capture_output=True, text=True
            )
            
            return result.returncode == 0
            
        except Exception as e:
            self.logger.error(f"Security update failed: {e}")
            return False
    
    async def _send_maintenance_notification(self, status: str, window: Dict, details: Dict = None):
        """유지보수 알림 전송"""
        
        if status == "started":
            title = "🔧 유지보수 시작"
            message = f"시작 시간: {window['start_time'].strftime('%Y-%m-%d %H:%M:%S')}\n"
            message += f"예상 종료: {window['end_time'].strftime('%Y-%m-%d %H:%M:%S')}\n"
            message += f"업데이트 타입: {', '.join([t.value for t in window['update_types']])}"
            priority = NotificationPriority.MEDIUM
            
        elif status == "completed":
            title = "✅ 유지보수 완료"
            message = f"종료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            if details:
                message += f"설치된 업데이트: {details['updates_installed']}/{details['total_updates']}"
            priority = NotificationPriority.LOW
            
        elif status == "partial":
            title = "⚠️ 유지보수 부분 완료"
            message = f"종료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            if details:
                message += f"설치된 업데이트: {details['updates_installed']}/{details['total_updates']}\n"
                message += "일부 업데이트가 실패했습니다."
            priority = NotificationPriority.MEDIUM
            
        elif status == "failed":
            title = "❌ 유지보수 실패"
            message = f"실패 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            if details and 'error' in details:
                message += f"오류: {details['error']}"
            priority = NotificationPriority.HIGH
        
        notification = Notification(
            title=title,
            message=message,
            priority=priority,
            tags=['maintenance', status]
        )
        
        await self.notification_system.route_notification(notification)

### 📊 **용량 계획 및 스케일링**

```python
# automation/capacity_planning.py
import asyncio
import psutil
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from enum import Enum
import json

class ResourceType(Enum):
    """리소스 타입"""
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    DATABASE_CONNECTIONS = "db_connections"

class ScalingDirection(Enum):
    """스케일링 방향"""
    UP = "up"
    DOWN = "down"
    MAINTAIN = "maintain"

@dataclass
class ResourceMetric:
    """리소스 메트릭"""
    timestamp: datetime
    resource_type: ResourceType
    value: float
    unit: str
    threshold_warning: float = 80.0
    threshold_critical: float = 90.0

@dataclass
class ScalingRecommendation:
    """스케일링 권장사항"""
    resource_type: ResourceType
    direction: ScalingDirection
    current_value: float
    recommended_value: float
    confidence: float
    reasoning: str
    estimated_cost_impact: float

class CapacityPlanningManager:
    """용량 계획 관리자"""
    
    def __init__(self, notification_system):
        self.notification_system = notification_system
        self.metrics_history: Dict[ResourceType, List[ResourceMetric]] = {
            resource_type: [] for resource_type in ResourceType
        }
        self.scaling_policies = {}
        self.prediction_models = {}
        
        # 메트릭 보존 기간 (일)
        self.retention_days = 90
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # 백그라운드 태스크 시작
        asyncio.create_task(self._monitoring_loop())
    
    async def _monitoring_loop(self):
        """모니터링 루프"""
        while True:
            try:
                # 리소스 메트릭 수집
                await self._collect_metrics()
                
                # 용량 분석
                await self._analyze_capacity()
                
                # 예측 모델 업데이트
                await self._update_prediction_models()
                
                # 스케일링 권장사항 생성
                recommendations = await self._generate_scaling_recommendations()
                
                if recommendations:
                    await self._send_capacity_alerts(recommendations)
                
                # 5분마다 실행
                await asyncio.sleep(300)
                
            except Exception as e:
                self.logger.error(f"Capacity monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def _collect_metrics(self):
        """메트릭 수집"""
        timestamp = datetime.now()
        
        # CPU 사용률
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_metric = ResourceMetric(
            timestamp=timestamp,
            resource_type=ResourceType.CPU,
            value=cpu_percent,
            unit="percent"
        )
        self.metrics_history[ResourceType.CPU].append(cpu_metric)
        
        # 메모리 사용률
        memory = psutil.virtual_memory()
        memory_metric = ResourceMetric(
            timestamp=timestamp,
            resource_type=ResourceType.MEMORY,
            value=memory.percent,
            unit="percent"
        )
        self.metrics_history[ResourceType.MEMORY].append(memory_metric)
        
        # 디스크 사용률
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        disk_metric = ResourceMetric(
            timestamp=timestamp,
            resource_type=ResourceType.DISK,
            value=disk_percent,
            unit="percent"
        )
        self.metrics_history[ResourceType.DISK].append(disk_metric)
        
        # 네트워크 I/O
        network = psutil.net_io_counters()
        network_mbps = (network.bytes_sent + network.bytes_recv) / (1024 * 1024)  # MB/s
        network_metric = ResourceMetric(
            timestamp=timestamp,
            resource_type=ResourceType.NETWORK,
            value=network_mbps,
            unit="mbps"
        )
        self.metrics_history[ResourceType.NETWORK].append(network_metric)
        
        # 데이터베이스 연결 수 (PostgreSQL)
        try:
            db_connections = await self._get_database_connections()
            db_metric = ResourceMetric(
                timestamp=timestamp,
                resource_type=ResourceType.DATABASE_CONNECTIONS,
                value=db_connections,
                unit="connections"
            )
            self.metrics_history[ResourceType.DATABASE_CONNECTIONS].append(db_metric)
        except Exception as e:
            self.logger.warning(f"Failed to collect DB metrics: {e}")
        
        # 오래된 메트릭 정리
        await self._cleanup_old_metrics()
    
    async def _get_database_connections(self) -> float:
        """데이터베이스 연결 수 조회"""
        try:
            import asyncpg
            
            conn = await asyncpg.connect(
                host='localhost',
                port=5432,
                user='freqtrade',
                password=os.getenv('DB_PASSWORD'),
                database='freqtrade'
            )
            
            result = await conn.fetchval(
                "SELECT count(*) FROM pg_stat_activity WHERE state = 'active'"
            )
            
            await conn.close()
            return float(result)
            
        except Exception as e:
            self.logger.error(f"Database connection check failed: {e}")
            return 0.0
    
    async def _cleanup_old_metrics(self):
        """오래된 메트릭 정리"""
        cutoff_time = datetime.now() - timedelta(days=self.retention_days)
        
        for resource_type in ResourceType:
            metrics = self.metrics_history[resource_type]
            self.metrics_history[resource_type] = [
                m for m in metrics if m.timestamp > cutoff_time
            ]
    
    async def _analyze_capacity(self):
        """용량 분석"""
        for resource_type in ResourceType:
            metrics = self.metrics_history[resource_type]
            
            if len(metrics) < 10:  # 최소 데이터 포인트 필요
                continue
            
            # 최근 1시간 평균
            recent_metrics = [m for m in metrics 
                            if m.timestamp > datetime.now() - timedelta(hours=1)]
            
            if recent_metrics:
                avg_usage = np.mean([m.value for m in recent_metrics])
                max_usage = np.max([m.value for m in recent_metrics])
                
                # 임계값 확인
                if max_usage > recent_metrics[0].threshold_critical:
                    await self._send_critical_alert(resource_type, max_usage)
                elif avg_usage > recent_metrics[0].threshold_warning:
                    await self._send_warning_alert(resource_type, avg_usage)
    
    async def _update_prediction_models(self):
        """예측 모델 업데이트"""
        for resource_type in ResourceType:
            metrics = self.metrics_history[resource_type]
            
            if len(metrics) < 100:  # 최소 데이터 포인트 필요
                continue
            
            try:
                # 시계열 데이터 준비
                timestamps = np.array([m.timestamp.timestamp() for m in metrics])
                values = np.array([m.value for m in metrics])
                
                # 선형 회귀를 통한 트렌드 분석
                coefficients = np.polyfit(timestamps, values, 1)
                
                # 24시간 후 예측값
                future_timestamp = datetime.now().timestamp() + (24 * 3600)
                predicted_value = np.polyval(coefficients, future_timestamp)
                
                self.prediction_models[resource_type] = {
                    'coefficients': coefficients.tolist(),
                    'predicted_24h': predicted_value,
                    'trend': 'increasing' if coefficients[0] > 0 else 'decreasing',
                    'updated_at': datetime.now()
                }
                
            except Exception as e:
                self.logger.error(f"Prediction model update failed for {resource_type.value}: {e}")
    
    async def _generate_scaling_recommendations(self) -> List[ScalingRecommendation]:
        """스케일링 권장사항 생성"""
        recommendations = []
        
        for resource_type, model in self.prediction_models.items():
            try:
                predicted_value = model['predicted_24h']
                trend = model['trend']
                
                # 현재 값
                recent_metrics = self.metrics_history[resource_type][-10:]
                if not recent_metrics:
                    continue
                
                current_avg = np.mean([m.value for m in recent_metrics])
                
                # 스케일링 결정 로직
                recommendation = await self._determine_scaling_action(
                    resource_type, current_avg, predicted_value, trend
                )
                
                if recommendation:
                    recommendations.append(recommendation)
                    
            except Exception as e:
                self.logger.error(f"Scaling recommendation generation failed for {resource_type.value}: {e}")
        
        return recommendations
    
    async def _determine_scaling_action(self, resource_type: ResourceType, 
                                      current_value: float, predicted_value: float, 
                                      trend: str) -> Optional[ScalingRecommendation]:
        """스케일링 액션 결정"""
        
        # 리소스별 임계값
        thresholds = {
            ResourceType.CPU: {'warning': 70, 'critical': 85},
            ResourceType.MEMORY: {'warning': 75, 'critical': 90},
            ResourceType.DISK: {'warning': 80, 'critical': 95},
            ResourceType.NETWORK: {'warning': 100, 'critical': 500},  # Mbps
            ResourceType.DATABASE_CONNECTIONS: {'warning': 80, 'critical': 95}
        }
        
        threshold = thresholds.get(resource_type, {'warning': 80, 'critical': 90})
        
        # 스케일 업 권장
        if predicted_value > threshold['critical'] or current_value > threshold['warning']:
            if resource_type in [ResourceType.CPU, ResourceType.MEMORY]:
                return ScalingRecommendation(
                    resource_type=resource_type,
                    direction=ScalingDirection.UP,
                    current_value=current_value,
                    recommended_value=current_value * 1.5,  # 50% 증가
                    confidence=0.8,
                    reasoning=f"Current: {current_value:.1f}%, Predicted 24h: {predicted_value:.1f}%",
                    estimated_cost_impact=50.0  # USD
                )
            elif resource_type == ResourceType.DISK:
                return ScalingRecommendation(
                    resource_type=resource_type,
                    direction=ScalingDirection.UP,
                    current_value=current_value,
                    recommended_value=100.0,  # 추가 스토리지
                    confidence=0.9,
                    reasoning=f"Disk usage critical: {current_value:.1f}%",
                    estimated_cost_impact=20.0  # USD
                )
        
        # 스케일 다운 권장 (리소스 절약)
        elif current_value < 30 and predicted_value < 40 and trend == 'decreasing':
            if resource_type in [ResourceType.CPU, ResourceType.MEMORY]:
                return ScalingRecommendation(
                    resource_type=resource_type,
                    direction=ScalingDirection.DOWN,
                    current_value=current_value,
                    recommended_value=current_value * 0.8,  # 20% 감소
                    confidence=0.6,
                    reasoning=f"Low usage: {current_value:.1f}%, trend: {trend}",
                    estimated_cost_impact=-25.0  # 비용 절약
                )
        
        return None
    
    async def _send_capacity_alerts(self, recommendations: List[ScalingRecommendation]):
        """용량 알림 전송"""
        
        if not recommendations:
            return
        
        title = "📊 용량 계획 권장사항"
        message = "다음 리소스에 대한 스케일링을 검토해주세요:\n\n"
        
        for rec in recommendations:
            direction_emoji = "⬆️" if rec.direction == ScalingDirection.UP else "⬇️"
            cost_text = f"+${rec.estimated_cost_impact:.0f}" if rec.estimated_cost_impact > 0 else f"${rec.estimated_cost_impact:.0f}"
            
            message += f"{direction_emoji} {rec.resource_type.value.upper()}\n"
            message += f"   현재: {rec.current_value:.1f}\n"
            message += f"   권장: {rec.recommended_value:.1f}\n"
            message += f"   이유: {rec.reasoning}\n"
            message += f"   비용 영향: {cost_text}/월\n"
            message += f"   신뢰도: {rec.confidence*100:.0f}%\n\n"
        
        notification = Notification(
            title=title,
            message=message,
            priority=NotificationPriority.MEDIUM,
            tags=['capacity', 'scaling']
        )
        
        await self.notification_system.route_notification(notification)
    
    async def _send_critical_alert(self, resource_type: ResourceType, value: float):
        """임계 알림 전송"""
        title = f"🚨 리소스 임계 상태: {resource_type.value.upper()}"
        message = f"현재 사용률: {value:.1f}%\n즉시 조치가 필요합니다."
        
        notification = Notification(
            title=title,
            message=message,
            priority=NotificationPriority.CRITICAL,
            tags=['resource', 'critical', resource_type.value]
        )
        
        await self.notification_system.route_notification(notification)
    
    async def _send_warning_alert(self, resource_type: ResourceType, value: float):
        """경고 알림 전송"""
        title = f"⚠️ 리소스 경고: {resource_type.value.upper()}"
        message = f"평균 사용률: {value:.1f}%\n모니터링을 강화해주세요."
        
        notification = Notification(
            title=title,
            message=message,
            priority=NotificationPriority.MEDIUM,
            tags=['resource', 'warning', resource_type.value]
        )
        
        await self.notification_system.route_notification(notification)
    
    async def get_capacity_report(self, days: int = 7) -> Dict[str, Any]:
        """용량 보고서 생성"""
        
        start_time = datetime.now() - timedelta(days=days)
        report = {
            'period': f'Last {days} days',
            'start_time': start_time.isoformat(),
            'end_time': datetime.now().isoformat(),
            'resources': {},
            'predictions': {},
            'recommendations': []
        }
        
        for resource_type in ResourceType:
            metrics = [m for m in self.metrics_history[resource_type] 
                      if m.timestamp > start_time]
            
            if metrics:
                values = [m.value for m in metrics]
                report['resources'][resource_type.value] = {
                    'average': np.mean(values),
                    'maximum': np.max(values),
                    'minimum': np.min(values),
                    'current': values[-1] if values else 0,
                    'data_points': len(values)
                }
            
            # 예측 정보 추가
            if resource_type in self.prediction_models:
                model = self.prediction_models[resource_type]
                report['predictions'][resource_type.value] = {
                    'predicted_24h': model['predicted_24h'],
                    'trend': model['trend'],
                    'updated_at': model['updated_at'].isoformat()
                }
        
        # 권장사항 추가
        recommendations = await self._generate_scaling_recommendations()
        report['recommendations'] = [
            {
                'resource': rec.resource_type.value,
                'direction': rec.direction.value,
                'current': rec.current_value,
                'recommended': rec.recommended_value,
                'confidence': rec.confidence,
                'reasoning': rec.reasoning,
                'cost_impact': rec.estimated_cost_impact
            }
            for rec in recommendations
        ]
        
        return report

### 🎯 **성능 튜닝 자동화**

```python
# automation/performance_tuning.py
import asyncio
import psutil
import time
import subprocess
import os
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from enum import Enum
import json

class TuningCategory(Enum):
    """튜닝 카테고리"""
    SYSTEM = "system"
    DATABASE = "database"
    APPLICATION = "application"
    NETWORK = "network"
    STORAGE = "storage"

class TuningAction(Enum):
    """튜닝 액션"""
    PARAMETER_CHANGE = "parameter_change"
    CONFIGURATION_UPDATE = "configuration_update"
    RESOURCE_REALLOCATION = "resource_reallocation"
    CACHING_OPTIMIZATION = "caching_optimization"

@dataclass
class PerformanceMetric:
    """성능 메트릭"""
    name: str
    value: float
    unit: str
    target_value: Optional[float] = None
    improvement_potential: float = 0.0

@dataclass
class TuningRecommendation:
    """튜닝 권장사항"""
    category: TuningCategory
    action: TuningAction
    description: str
    current_config: Dict[str, Any]
    recommended_config: Dict[str, Any]
    expected_improvement: float
    risk_level: str  # low, medium, high
    implementation_effort: str  # low, medium, high

class PerformanceTuningManager:
    """성능 튜닝 관리자"""
    
    def __init__(self, notification_system):
        self.notification_system = notification_system
        self.performance_baselines = {}
        self.tuning_history = []
        self.active_experiments = {}
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    async def analyze_performance(self) -> Dict[str, List[PerformanceMetric]]:
        """성능 분석"""
        
        analysis_results = {
            'system': await self._analyze_system_performance(),
            'database': await self._analyze_database_performance(),
            'application': await self._analyze_application_performance(),
            'network': await self._analyze_network_performance(),
            'storage': await self._analyze_storage_performance()
        }
        
        return analysis_results
    
    async def _analyze_system_performance(self) -> List[PerformanceMetric]:
        """시스템 성능 분석"""
        metrics = []
        
        # CPU 성능
        cpu_freq = psutil.cpu_freq()
        if cpu_freq:
            cpu_metric = PerformanceMetric(
                name="cpu_frequency",
                value=cpu_freq.current,
                unit="MHz",
                target_value=cpu_freq.max * 0.8,
                improvement_potential=max(0, (cpu_freq.max * 0.8 - cpu_freq.current) / cpu_freq.max)
            )
            metrics.append(cpu_metric)
        
        # 메모리 성능
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        memory_efficiency = (memory.available / memory.total) * 100
        metrics.append(PerformanceMetric(
            name="memory_efficiency",
            value=memory_efficiency,
            unit="percent",
            target_value=70.0,
            improvement_potential=max(0, (70.0 - memory_efficiency) / 70.0)
        ))
        
        # 스왑 사용률
        swap_usage = swap.percent
        metrics.append(PerformanceMetric(
            name="swap_usage",
            value=swap_usage,
            unit="percent",
            target_value=5.0,
            improvement_potential=max(0, (swap_usage - 5.0) / 95.0)
        ))
        
        return metrics
    
    async def _analyze_database_performance(self) -> List[PerformanceMetric]:
        """데이터베이스 성능 분석"""
        metrics = []
        
        try:
            import asyncpg
            
            conn = await asyncpg.connect(
                host='localhost',
                port=5432,
                user='freqtrade',
                password=os.getenv('DB_PASSWORD'),
                database='freqtrade'
            )
            
            # 활성 연결 수
            active_connections = await conn.fetchval(
                "SELECT count(*) FROM pg_stat_activity WHERE state = 'active'"
            )
            
            metrics.append(PerformanceMetric(
                name="active_connections",
                value=float(active_connections),
                unit="connections",
                target_value=50.0
            ))
            
            # 데이터베이스 크기
            db_size = await conn.fetchval(
                "SELECT pg_database_size('freqtrade')"
            )
            
            metrics.append(PerformanceMetric(
                name="database_size",
                value=float(db_size) / (1024 * 1024),  # MB
                unit="MB"
            ))
            
            # 캐시 히트 비율
            cache_hit_ratio = await conn.fetchval("""
                SELECT round(
                    sum(blks_hit) * 100.0 / (sum(blks_hit) + sum(blks_read)), 2
                ) FROM pg_stat_database WHERE datname = 'freqtrade'
            """)
            
            if cache_hit_ratio:
                metrics.append(PerformanceMetric(
                    name="cache_hit_ratio",
                    value=float(cache_hit_ratio),
                    unit="percent",
                    target_value=95.0,
                    improvement_potential=max(0, (95.0 - float(cache_hit_ratio)) / 95.0)
                ))
            
            await conn.close()
            
        except Exception as e:
            self.logger.error(f"Database performance analysis failed: {e}")
        
        return metrics
    
    async def _analyze_application_performance(self) -> List[PerformanceMetric]:
        """애플리케이션 성능 분석"""
        metrics = []
        
        try:
            # Freqtrade API 응답 시간 측정
            import aiohttp
            
            start_time = time.time()
            async with aiohttp.ClientSession() as session:
                async with session.get('http://localhost:8080/api/v1/ping') as resp:
                    if resp.status == 200:
                        response_time = (time.time() - start_time) * 1000  # ms
                        
                        metrics.append(PerformanceMetric(
                            name="api_response_time",
                            value=response_time,
                            unit="ms",
                            target_value=100.0,
                            improvement_potential=max(0, (response_time - 100.0) / 1000.0)
                        ))
            
            # Docker 컨테이너 리소스 사용량
            docker_stats = await self._get_docker_stats()
            for container_name, stats in docker_stats.items():
                metrics.append(PerformanceMetric(
                    name=f"{container_name}_cpu_usage",
                    value=stats.get('cpu_percent', 0),
                    unit="percent"
                ))
                
                metrics.append(PerformanceMetric(
                    name=f"{container_name}_memory_usage",
                    value=stats.get('memory_percent', 0),
                    unit="percent"
                ))
            
        except Exception as e:
            self.logger.error(f"Application performance analysis failed: {e}")
        
        return metrics
    
    async def _get_docker_stats(self) -> Dict[str, Dict]:
        """Docker 컨테이너 통계 조회"""
        try:
            result = subprocess.run(
                ['docker', 'stats', '--no-stream', '--format', 'json'],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                stats = {}
                for line in result.stdout.strip().split('\n'):
                    if line:
                        data = json.loads(line)
                        stats[data['Name']] = {
                            'cpu_percent': float(data['CPUPerc'].rstrip('%')),
                            'memory_percent': float(data['MemPerc'].rstrip('%'))
                        }
                return stats
            
        except Exception as e:
            self.logger.error(f"Docker stats collection failed: {e}")
        
        return {}
    
    async def _analyze_network_performance(self) -> List[PerformanceMetric]:
        """네트워크 성능 분석"""
        metrics = []
        
        try:
            # 네트워크 통계
            net_io = psutil.net_io_counters()
            
            # 처리량 (바이트/초)
            if hasattr(self, '_last_net_io') and hasattr(self, '_last_net_time'):
                time_delta = time.time() - self._last_net_time
                bytes_sent_per_sec = (net_io.bytes_sent - self._last_net_io.bytes_sent) / time_delta
                bytes_recv_per_sec = (net_io.bytes_recv - self._last_net_io.bytes_recv) / time_delta
                
                metrics.append(PerformanceMetric(
                    name="network_throughput_sent",
                    value=bytes_sent_per_sec / (1024 * 1024),  # MB/s
                    unit="MB/s"
                ))
                
                metrics.append(PerformanceMetric(
                    name="network_throughput_recv",
                    value=bytes_recv_per_sec / (1024 * 1024),  # MB/s
                    unit="MB/s"
                ))
            
            self._last_net_io = net_io
            self._last_net_time = time.time()
            
            # 네트워크 지연시간 (ping)
            ping_result = subprocess.run(
                ['ping', '-c', '3', '8.8.8.8'],
                capture_output=True, text=True
            )
            
            if ping_result.returncode == 0:
                # ping 결과에서 평균 지연시간 추출
                lines = ping_result.stdout.split('\n')
                for line in lines:
                    if 'avg' in line:
                        avg_latency = float(line.split('/')[-3])
                        metrics.append(PerformanceMetric(
                            name="network_latency",
                            value=avg_latency,
                            unit="ms",
                            target_value=50.0,
                            improvement_potential=max(0, (avg_latency - 50.0) / 200.0)
                        ))
                        break
            
        except Exception as e:
            self.logger.error(f"Network performance analysis failed: {e}")
        
        return metrics
    
    async def _analyze_storage_performance(self) -> List[PerformanceMetric]:
        """스토리지 성능 분석"""
        metrics = []
        
        try:
            # 디스크 I/O
            disk_io = psutil.disk_io_counters()
            
            if hasattr(self, '_last_disk_io') and hasattr(self, '_last_disk_time'):
                time_delta = time.time() - self._last_disk_time
                
                read_speed = (disk_io.read_bytes - self._last_disk_io.read_bytes) / time_delta
                write_speed = (disk_io.write_bytes - self._last_disk_io.write_bytes) / time_delta
                
                metrics.append(PerformanceMetric(
                    name="disk_read_speed",
                    value=read_speed / (1024 * 1024),  # MB/s
                    unit="MB/s"
                ))
                
                metrics.append(PerformanceMetric(
                    name="disk_write_speed",
                    value=write_speed / (1024 * 1024),  # MB/s
                    unit="MB/s"
                ))
            
            self._last_disk_io = disk_io
            self._last_disk_time = time.time()
            
            # 디스크 사용률
            disk_usage = psutil.disk_usage('/')
            usage_percent = (disk_usage.used / disk_usage.total) * 100
            
            metrics.append(PerformanceMetric(
                name="disk_usage",
                value=usage_percent,
                unit="percent",
                target_value=80.0,
                improvement_potential=max(0, (usage_percent - 80.0) / 20.0)
            ))
            
        except Exception as e:
            self.logger.error(f"Storage performance analysis failed: {e}")
        
        return metrics
    
    async def generate_tuning_recommendations(self) -> List[TuningRecommendation]:
        """튜닝 권장사항 생성"""
        
        # 성능 분석 실행
        performance_data = await self.analyze_performance()
        
        recommendations = []
        
        # 시스템 튜닝 권장사항
        system_recommendations = await self._generate_system_tuning(performance_data['system'])
        recommendations.extend(system_recommendations)
        
        # 데이터베이스 튜닝 권장사항
        db_recommendations = await self._generate_database_tuning(performance_data['database'])
        recommendations.extend(db_recommendations)
        
        # 애플리케이션 튜닝 권장사항
        app_recommendations = await self._generate_application_tuning(performance_data['application'])
        recommendations.extend(app_recommendations)
        
        return recommendations
    
    async def _generate_system_tuning(self, metrics: List[PerformanceMetric]) -> List[TuningRecommendation]:
        """시스템 튜닝 권장사항"""
        recommendations = []
        
        # 스왑 사용률이 높은 경우
        swap_metric = next((m for m in metrics if m.name == "swap_usage"), None)
        if swap_metric and swap_metric.value > 10:
            recommendations.append(TuningRecommendation(
                category=TuningCategory.SYSTEM,
                action=TuningAction.PARAMETER_CHANGE,
                description="스왑 사용률이 높습니다. 스왑 스왑피니스를 조정하세요.",
                current_config={"vm.swappiness": "60"},
                recommended_config={"vm.swappiness": "10"},
                expected_improvement=15.0,
                risk_level="low",
                implementation_effort="low"
            ))
        
        # 메모리 효율성이 낮은 경우
        memory_metric = next((m for m in metrics if m.name == "memory_efficiency"), None)
        if memory_metric and memory_metric.value < 50:
            recommendations.append(TuningRecommendation(
                category=TuningCategory.SYSTEM,
                action=TuningAction.RESOURCE_REALLOCATION,
                description="메모리 효율성이 낮습니다. 메모리 증설을 고려하세요.",
                current_config={"memory": "current"},
                recommended_config={"memory": "upgrade"},
                expected_improvement=25.0,
                risk_level="low",
                implementation_effort="medium"
            ))
        
        return recommendations
    
    async def _generate_database_tuning(self, metrics: List[PerformanceMetric]) -> List[TuningRecommendation]:
        """데이터베이스 튜닝 권장사항"""
        recommendations = []
        
        # 캐시 히트 비율이 낮은 경우
        cache_metric = next((m for m in metrics if m.name == "cache_hit_ratio"), None)
        if cache_metric and cache_metric.value < 90:
            recommendations.append(TuningRecommendation(
                category=TuningCategory.DATABASE,
                action=TuningAction.CONFIGURATION_UPDATE,
                description="데이터베이스 캐시 히트 비율이 낮습니다. shared_buffers를 증가시키세요.",
                current_config={"shared_buffers": "128MB"},
                recommended_config={"shared_buffers": "256MB"},
                expected_improvement=20.0,
                risk_level="low",
                implementation_effort="low"
            ))
        
        return recommendations
    
    async def _generate_application_tuning(self, metrics: List[PerformanceMetric]) -> List[TuningRecommendation]:
        """애플리케이션 튜닝 권장사항"""
        recommendations = []
        
        # API 응답 시간이 느린 경우
        api_metric = next((m for m in metrics if m.name == "api_response_time"), None)
        if api_metric and api_metric.value > 200:
            recommendations.append(TuningRecommendation(
                category=TuningCategory.APPLICATION,
                action=TuningAction.CACHING_OPTIMIZATION,
                description="API 응답 시간이 느립니다. Redis 캐싱을 활성화하세요.",
                current_config={"caching": "disabled"},
                recommended_config={"caching": "redis"},
                expected_improvement=30.0,
                risk_level="low",
                implementation_effort="medium"
            ))
        
        return recommendations
    
    async def apply_tuning_recommendation(self, recommendation: TuningRecommendation) -> bool:
        """튜닝 권장사항 적용"""
        
        try:
            self.logger.info(f"Applying tuning recommendation: {recommendation.description}")
            
            if recommendation.category == TuningCategory.SYSTEM:
                return await self._apply_system_tuning(recommendation)
            elif recommendation.category == TuningCategory.DATABASE:
                return await self._apply_database_tuning(recommendation)
            elif recommendation.category == TuningCategory.APPLICATION:
                return await self._apply_application_tuning(recommendation)
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to apply tuning recommendation: {e}")
            return False
    
    async def _apply_system_tuning(self, recommendation: TuningRecommendation) -> bool:
        """시스템 튜닝 적용"""
        
        if recommendation.action == TuningAction.PARAMETER_CHANGE:
            for param, value in recommendation.recommended_config.items():
                if param == "vm.swappiness":
                    cmd = ['sysctl', '-w', f'{param}={value}']
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        # 영구 설정
                        with open('/etc/sysctl.conf', 'a') as f:
                            f.write(f'\n{param}={value}\n')
                        return True
        
        return False
    
    async def _apply_database_tuning(self, recommendation: TuningRecommendation) -> bool:
        """데이터베이스 튜닝 적용"""
        
        # PostgreSQL 설정 파일 수정
        # 실제 구현에서는 postgresql.conf 파일을 수정하고 재시작
        self.logger.info("Database tuning would require manual configuration")
        return True
    
    async def _apply_application_tuning(self, recommendation: TuningRecommendation) -> bool:
        """애플리케이션 튜닝 적용"""
        
        # Docker Compose 설정 수정 또는 환경 변수 업데이트
        # 실제 구현에서는 애플리케이션별 설정 적용
        self.logger.info("Application tuning would require configuration update")
        return True

---

## 🎉 **결론 및 다음 단계**

이 **03_FUTURES_AUTOMATION_SETUP.md** 가이드를 통해 엔터프라이즈급 완전 자동화 시스템을 구축할 수 있습니다:

### ✅ **달성된 자동화 수준**

1. **🏗️ 마이크로서비스 아키텍처**: 확장 가능하고 유연한 시스템 설계
2. **🐳 컨테이너 오케스트레이션**: Docker와 Kubernetes를 통한 완전 자동화 배포
3. **🔄 CI/CD 파이프라인**: GitHub Actions 기반 자동 테스트 및 배포
4. **🎯 멀티 전략 관리**: 동적 로딩과 성과 기반 자동 스케일링
5. **📊 실시간 데이터 파이프라인**: 고성능 데이터 처리 및 분석
6. **📢 통합 알림 시스템**: 지능적 라우팅과 에스컬레이션
7. **🔄 자동 장애 복구**: 서킷 브레이커와 자동 페일오버
8. **⚡ 성과 최적화**: ML 기반 하이퍼파라미터 튜닝과 A/B 테스트
9. **🔐 보안 및 컴플라이언스**: 완전 자동화된 보안 관리
10. **🚀 운영 자동화**: 백업, 업데이트, 성능 튜닝까지 모든 것 자동화

### 🚀 **다음 단계 권장사항**

1. **단계별 구현**: 기본 Docker 설정부터 시작하여 점진적으로 확장
2. **모니터링 우선**: Prometheus + Grafana 대시보드를 먼저 구축
3. **보안 강화**: HashiCorp Vault와 네트워크 보안을 조기에 설정
4. **성능 최적화**: 기본 시스템이 안정화된 후 ML 기반 최적화 도입
5. **팀 교육**: 운영팀의 자동화 시스템 이해도 향상

### 💡 **핵심 성공 요소**

- **점진적 구현**: 한 번에 모든 것을 구현하지 말고 단계별로 접근
- **충분한 테스트**: 각 자동화 단계마다 철저한 테스트 수행
- **모니터링 중심**: 모든 자동화에 대한 관찰성 확보
- **문서화**: 자동화된 프로세스의 명확한 문서화
- **팀 협업**: DevOps, 개발, 운영팀 간의 긴밀한 협력

이제 **24시간 무중단 무인 운영**이 가능한 엔터프라이즈급 자동화 시스템을 구축할 준비가 완료되었습니다! 🎯

---

<div align="center">

**🤖 완전 자동화된 Futures 트레이딩 시스템으로 새로운 차원의 효율성을 경험하세요! 🚀**

[![시작하기](https://img.shields.io/badge/시작하기-🚀%20Get%20Started-success?style=for-the-badge)](README_FUTURES.md)
[![문의하기](https://img.shields.io/badge/문의하기-💬%20Contact-blue?style=for-the-badge)](mailto:support@freqtrade.com)

</div>
                        await handler(event)
                    except Exception as e:
                        print(f"이벤트 처리 오류: {e}")

class AutomationOrchestrator:
    """자동화 오케스트레이터"""
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.strategies = {}
        self.risk_manager = None
        self.position_manager = None
        
    async def handle_trade_signal(self, event: Event):
        """거래 신호 처리"""
        signal_data = event.data
        
        # 리스크 검증
        if await self.risk_manager.validate_signal(signal_data):
            # 포지션 관리자에게 전달
            await self.position_manager.execute_signal(signal_data)
            
            # 실행 결과 이벤트 발행
            result_event = Event(
                event_id=f"execution_{event.event_id}",
                event_type=EventType.POSITION_UPDATE,
                source="automation_orchestrator",
                timestamp=time.time(),
                data={"status": "executed", "original_signal": signal_data}
            )
            await self.event_bus.publish(result_event)
    
    async def start(self):
        """자동화 시스템 시작"""
        # 이벤트 핸들러 등록
        self.event_bus.subscribe(EventType.TRADE_SIGNAL, self.handle_trade_signal)
        self.event_bus.subscribe(EventType.RISK_ALERT, self.handle_risk_alert)
        
        # 이벤트 처리 시작
        await self.event_bus.process_events()
```

### 🔧 **서비스 메시 구성**

```yaml
# infrastructure/service-mesh/istio-config.yaml
apiVersion: install.istio.io/v1alpha1
kind: IstioOperator
metadata:
  name: freqtrade-control-plane
spec:
  values:
    global:
      meshID: freqtrade-mesh
      network: freqtrade-network
  components:
    pilot:
      k8s:
        resources:
          requests:
            cpu: 500m
            memory: 512Mi
    ingressGateways:
    - name: freqtrade-gateway
      enabled: true
      k8s:
        service:
          type: LoadBalancer
        resources:
          requests:
            cpu: 200m
            memory: 256Mi
---
apiVersion: networking.istio.io/v1alpha3
kind: Gateway
metadata:
  name: freqtrade-gateway
spec:
  selector:
    istio: ingressgateway
  servers:
  - port:
      number: 80
      name: http
      protocol: HTTP
    hosts:
    - "freqtrade-api.local"
  - port:
      number: 443
      name: https
      protocol: HTTPS
    tls:
      mode: SIMPLE
      credentialName: freqtrade-tls
    hosts:
    - "freqtrade-api.local"
```

---

## 🐳 **Docker 컨테이너 오케스트레이션**

### 📦 **Multi-container Freqtrade 설정**

```yaml
# docker-compose.automation.yml
version: '3.8'

services:
  # 메인 트레이딩 엔진들
  freqtrade-strategy-1:
    build:
      context: .
      dockerfile: docker/Dockerfile.freqtrade
      args:
        STRATEGY_NAME: FuturesAIRiskStrategy
    environment:
      - FREQTRADE_INSTANCE_ID=strategy-1
      - REDIS_URL=redis://redis-cluster:6379
      - POSTGRES_URL=postgresql://user:pass@timescaledb:5432/freqtrade
      - KAFKA_BOOTSTRAP_SERVERS=kafka:9092
    volumes:
      - ./user_data:/freqtrade/user_data
      - ./strategies:/freqtrade/user_data/strategies
    networks:
      - freqtrade-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:8080/api/v1/ping || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3
    
  freqtrade-strategy-2:
    build:
      context: .
      dockerfile: docker/Dockerfile.freqtrade
      args:
        STRATEGY_NAME: RossCameronFuturesStrategy
    environment:
      - FREQTRADE_INSTANCE_ID=strategy-2
      - REDIS_URL=redis://redis-cluster:6379
      - POSTGRES_URL=postgresql://user:pass@timescaledb:5432/freqtrade
      - KAFKA_BOOTSTRAP_SERVERS=kafka:9092
    volumes:
      - ./user_data:/freqtrade/user_data
      - ./strategies:/freqtrade/user_data/strategies
    networks:
      - freqtrade-network
    restart: unless-stopped

  # 리스크 관리 서비스
  risk-manager:
    build:
      context: .
      dockerfile: docker/Dockerfile.risk-manager
    environment:
      - REDIS_URL=redis://redis-cluster:6379
      - POSTGRES_URL=postgresql://user:pass@timescaledb:5432/freqtrade
      - MAX_PORTFOLIO_RISK=0.02  # 2% VaR
      - MAX_POSITION_SIZE=0.1    # 10% per position
    volumes:
      - ./risk_management:/app/risk_management
    networks:
      - freqtrade-network
    restart: unless-stopped

  # 포지션 관리 서비스
  position-manager:
    build:
      context: .
      dockerfile: docker/Dockerfile.position-manager
    environment:
      - REDIS_URL=redis://redis-cluster:6379
      - POSTGRES_URL=postgresql://user:pass@timescaledb:5432/freqtrade
      - BINANCE_API_KEY=${BINANCE_API_KEY}
      - BINANCE_API_SECRET=${BINANCE_API_SECRET}
    networks:
      - freqtrade-network
    restart: unless-stopped

  # 데이터베이스 - TimescaleDB (시계열 데이터 최적화)
  timescaledb:
    image: timescale/timescaledb:latest-pg14
    environment:
      - POSTGRES_DB=freqtrade
      - POSTGRES_USER=freqtrade
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - timescaledb_data:/var/lib/postgresql/data
      - ./sql/init_timescaledb.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    networks:
      - freqtrade-network
    restart: unless-stopped

  # Redis 클러스터 (캐싱 및 세션 관리)
  redis-cluster:
    image: redis/redis-stack-server:latest
    command: redis-server --appendonly yes --cluster-enabled yes --cluster-config-file nodes.conf --cluster-node-timeout 5000 --port 6379
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    networks:
      - freqtrade-network
    restart: unless-stopped

  # Message Queue - RabbitMQ
  rabbitmq:
    image: rabbitmq:3-management-alpine
    environment:
      - RABBITMQ_DEFAULT_USER=freqtrade
      - RABBITMQ_DEFAULT_PASS=${RABBITMQ_PASSWORD}
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq
      - ./rabbitmq/rabbitmq.conf:/etc/rabbitmq/rabbitmq.conf
    ports:
      - "5672:5672"
      - "15672:15672"
    networks:
      - freqtrade-network
    restart: unless-stopped

  # Apache Kafka
  zookeeper:
    image: confluentinc/cp-zookeeper:latest
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000
    networks:
      - freqtrade-network

  kafka:
    image: confluentinc/cp-kafka:latest
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
    networks:
      - freqtrade-network

  # 모니터링 - Prometheus
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"
    networks:
      - freqtrade-network
    restart: unless-stopped

  # 대시보드 - Grafana
  grafana:
    image: grafana/grafana:latest
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning
    ports:
      - "3000:3000"
    networks:
      - freqtrade-network
    restart: unless-stopped

  # 로그 수집 - Elasticsearch
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    ports:
      - "9200:9200"
    networks:
      - freqtrade-network

  # 로그 처리 - Logstash
  logstash:
    image: docker.elastic.co/logstash/logstash:8.11.0
    volumes:
      - ./monitoring/logstash/pipeline:/usr/share/logstash/pipeline
    depends_on:
      - elasticsearch
    networks:
      - freqtrade-network

  # 로그 시각화 - Kibana
  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch
    networks:
      - freqtrade-network

  # 분산 추적 - Jaeger
  jaeger:
    image: jaegertracing/all-in-one:latest
    environment:
      - COLLECTOR_OTLP_ENABLED=true
    ports:
      - "16686:16686"
      - "14250:14250"
    networks:
      - freqtrade-network

  # API Gateway - Kong
  kong:
    image: kong/kong-gateway:latest
    environment:
      - KONG_DATABASE=off
      - KONG_DECLARATIVE_CONFIG=/kong/declarative/kong.yml
      - KONG_PROXY_ACCESS_LOG=/dev/stdout
      - KONG_ADMIN_ACCESS_LOG=/dev/stdout
      - KONG_PROXY_ERROR_LOG=/dev/stderr
      - KONG_ADMIN_ERROR_LOG=/dev/stderr
      - KONG_ADMIN_LISTEN=0.0.0.0:8001
    volumes:
      - ./api-gateway/kong.yml:/kong/declarative/kong.yml
    ports:
      - "8000:8000"
      - "8001:8001"
      - "8443:8443"
      - "8444:8444"
    networks:
      - freqtrade-network

networks:
  freqtrade-network:
    driver: bridge

volumes:
  timescaledb_data:
  redis_data:
  rabbitmq_data:
  prometheus_data:
  grafana_data:
  elasticsearch_data:
```

### 🔧 **볼륨 관리 및 데이터 영속성**

```bash
# scripts/volume_management.sh
#!/bin/bash
# 볼륨 관리 자동화 스크립트

set -e

BACKUP_DIR="/backup/freqtrade"
DATE=$(date +%Y%m%d_%H%M%S)

create_volumes() {
    echo "📦 Docker 볼륨 생성 중..."
    
    # 데이터 볼륨들
    docker volume create freqtrade_timescaledb_data
    docker volume create freqtrade_redis_data
    docker volume create freqtrade_prometheus_data
    docker volume create freqtrade_grafana_data
    docker volume create freqtrade_elasticsearch_data
    
    echo "✅ 볼륨 생성 완료"
}

backup_volumes() {
    echo "💾 볼륨 백업 시작..."
    
    mkdir -p ${BACKUP_DIR}/${DATE}
    
    # TimescaleDB 백업
    docker run --rm \
        -v freqtrade_timescaledb_data:/var/lib/postgresql/data:ro \
        -v ${BACKUP_DIR}/${DATE}:/backup \
        postgres:14 \
        pg_dumpall -h localhost -U freqtrade -f /backup/timescaledb_backup.sql
    
    # Redis 백업
    docker run --rm \
        -v freqtrade_redis_data:/data:ro \
        -v ${BACKUP_DIR}/${DATE}:/backup \
        redis:alpine \
        cp /data/dump.rdb /backup/redis_backup.rdb
    
    # Grafana 백업
    docker run --rm \
        -v freqtrade_grafana_data:/var/lib/grafana:ro \
        -v ${BACKUP_DIR}/${DATE}:/backup \
        alpine:latest \
        tar -czf /backup/grafana_backup.tar.gz -C /var/lib/grafana .
    
    echo "✅ 볼륨 백업 완료: ${BACKUP_DIR}/${DATE}"
}

restore_volumes() {
    local RESTORE_DATE=$1
    
    if [ -z "$RESTORE_DATE" ]; then
        echo "❌ 복원 날짜를 지정해주세요. 예: 20241201_143000"
        exit 1
    fi
    
    if [ ! -d "${BACKUP_DIR}/${RESTORE_DATE}" ]; then
        echo "❌ 백업 디렉토리가 존재하지 않습니다: ${BACKUP_DIR}/${RESTORE_DATE}"
        exit 1
    fi
    
    echo "🔄 볼륨 복원 시작: ${RESTORE_DATE}"
    
    # 서비스 중지
    docker-compose -f docker-compose.automation.yml down
    
    # TimescaleDB 복원
    docker run --rm \
        -v freqtrade_timescaledb_data:/var/lib/postgresql/data \
        -v ${BACKUP_DIR}/${RESTORE_DATE}:/backup:ro \
        postgres:14 \
        psql -h localhost -U freqtrade -f /backup/timescaledb_backup.sql
    
    # Redis 복원
    docker run --rm \
        -v freqtrade_redis_data:/data \
        -v ${BACKUP_DIR}/${RESTORE_DATE}:/backup:ro \
        redis:alpine \
        cp /backup/redis_backup.rdb /data/dump.rdb
    
    # Grafana 복원
    docker run --rm \
        -v freqtrade_grafana_data:/var/lib/grafana \
        -v ${BACKUP_DIR}/${RESTORE_DATE}:/backup:ro \
        alpine:latest \
        tar -xzf /backup/grafana_backup.tar.gz -C /var/lib/grafana
    
    echo "✅ 볼륨 복원 완료"
}

# 스크립트 실행
case "$1" in
    "create")
        create_volumes
        ;;
    "backup")
        backup_volumes
        ;;
    "restore")
        restore_volumes $2
        ;;
    *)
        echo "사용법: $0 {create|backup|restore <date>}"
        exit 1
        ;;
esac
```

### 🌐 **네트워크 구성 및 보안**

```yaml
# docker/networks/secure-network.yml
version: '3.8'

networks:
  # 프론트엔드 네트워크 (외부 접근)
  frontend:
    driver: bridge
    driver_opts:
      com.docker.network.bridge.name: ft-frontend
    ipam:
      config:
        - subnet: 172.20.1.0/24

  # 백엔드 네트워크 (내부 통신)
  backend:
    driver: bridge
    driver_opts:
      com.docker.network.bridge.name: ft-backend
    internal: true
    ipam:
      config:
        - subnet: 172.20.2.0/24

  # 데이터베이스 네트워크 (고도로 격리)
  database:
    driver: bridge
    driver_opts:
      com.docker.network.bridge.name: ft-database
    internal: true
    ipam:
      config:
        - subnet: 172.20.3.0/24

  # 모니터링 네트워크
  monitoring:
    driver: bridge
    driver_opts:
      com.docker.network.bridge.name: ft-monitoring
    ipam:
      config:
        - subnet: 172.20.4.0/24
```

---

## 🔄 **CI/CD 파이프라인 구축**

### 🚀 **GitHub Actions 워크플로우**

```yaml
# .github/workflows/freqtrade-cicd.yml
name: Freqtrade Futures Automation CI/CD

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: freqtrade-futures-automation

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      redis:
        image: redis:alpine
        ports:
          - 6379:6379
      postgres:
        image: timescale/timescaledb:latest-pg14
        env:
          POSTGRES_PASSWORD: testpassword
          POSTGRES_DB: freqtrade_test
        ports:
          - 5432:5432
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python 3.11
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
        cache: 'pip'
    
    - name: Install dependencies
      run: |
        pip install -r requirements-test.txt
        pip install -e .
    
    - name: Run linting
      run: |
        flake8 user_data/strategies/
        black --check user_data/strategies/
        isort --check-only user_data/strategies/
    
    - name: Run type checking
      run: |
        mypy user_data/strategies/
    
    - name: Run unit tests
      run: |
        pytest tests/unit/ -v --cov=user_data/strategies --cov-report=xml
    
    - name: Run integration tests
      run: |
        pytest tests/integration/ -v
      env:
        REDIS_URL: redis://localhost:6379
        POSTGRES_URL: postgresql://postgres:testpassword@localhost:5432/freqtrade_test
    
    - name: Run strategy backtests
      run: |
        freqtrade backtesting \
          --config tests/configs/test_config_futures.json \
          --strategy FuturesAIRiskStrategy \
          --timerange 20241101-20241130 \
          --breakdown day
    
    - name: Upload coverage reports
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml

  security-scan:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Run security scan
      uses: github/super-linter/slim@v4
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        VALIDATE_PYTHON_BLACK: true
        VALIDATE_PYTHON_FLAKE8: true
        VALIDATE_YAML: true
        VALIDATE_DOCKERFILE: true
    
    - name: Run dependency vulnerability scan
      run: |
        pip install safety
        safety check
    
    - name: Scan Docker image for vulnerabilities
      uses: aquasecurity/trivy-action@master
      with:
        image-ref: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest
        format: 'sarif'
        output: 'trivy-results.sarif'
    
    - name: Upload Trivy scan results
      uses: github/codeql-action/upload-sarif@v2
      with:
        sarif_file: 'trivy-results.sarif'

  build-and-push:
    needs: [test, security-scan]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    outputs:
      image-digest: ${{ steps.build.outputs.digest }}
    
    steps:
    - name: Checkout
      uses: actions/checkout@v4
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3
    
    - name: Log in to Container Registry
      uses: docker/login-action@v3
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
    
    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v5
      with:
        images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
        tags: |
          type=ref,event=branch
          type=ref,event=pr
          type=sha,prefix={{branch}}-
          type=raw,value=latest,enable={{is_default_branch}}
    
    - name: Build and push
      id: build
      uses: docker/build-push-action@v5
      with:
        context: .
        platforms: linux/amd64,linux/arm64
        push: true
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
        cache-from: type=gha
        cache-to: type=gha,mode=max

  deploy-staging:
    needs: build-and-push
    runs-on: ubuntu-latest
    environment: staging
    
    steps:
    - name: Deploy to staging
      run: |
        echo "Deploying to staging environment..."
        # Kubernetes 배포 로직
        kubectl set image deployment/freqtrade-app \
          freqtrade=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}@${{ needs.build-and-push.outputs.image-digest }} \
          --namespace=staging
        
        kubectl rollout status deployment/freqtrade-app --namespace=staging

  integration-tests:
    needs: deploy-staging
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Run integration tests against staging
      run: |
        pytest tests/integration/ -v --staging
      env:
        STAGING_API_URL: https://staging-api.freqtrade.local
        API_KEY: ${{ secrets.STAGING_API_KEY }}

  deploy-production:
    needs: integration-tests
    runs-on: ubuntu-latest
    environment: production
    if: github.ref == 'refs/heads/main'
    
    steps:
    - name: Deploy to production
      run: |
        echo "Deploying to production environment..."
        
        # 블루-그린 배포
        kubectl patch deployment freqtrade-app \
          -p '{"spec":{"template":{"spec":{"containers":[{"name":"freqtrade","image":"${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}@${{ needs.build-and-push.outputs.image-digest }}"}]}}}}' \
          --namespace=production
        
        kubectl rollout status deployment/freqtrade-app --namespace=production
        
        # 헬스체크
        kubectl wait --for=condition=ready pod -l app=freqtrade-app --namespace=production --timeout=300s
    
    - name: Run smoke tests
      run: |
        curl -f https://api.freqtrade.local/health || exit 1
        
    - name: Notify deployment success
      uses: 8398a7/action-slack@v3
      with:
        status: success
        text: "🚀 프로덕션 배포 성공! 버전: ${{ github.sha }}"
      env:
        SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}
```

### 🔧 **자동 테스트 및 검증**

```python
# tests/integration/test_automation_pipeline.py
import pytest
import asyncio
import aiohttp
import websockets
from datetime import datetime, timedelta

class TestAutomationPipeline:
    """자동화 파이프라인 통합 테스트"""
    
    @pytest.fixture
    async def api_client(self):
        """API 클라이언트 픽스처"""
        async with aiohttp.ClientSession() as session:
            yield session
    
    @pytest.mark.asyncio
    async def test_end_to_end_trading_flow(self, api_client):
        """종단간 거래 플로우 테스트"""
        
        # 1. 시스템 헬스체크
        async with api_client.get("https://api.freqtrade.local/api/v1/ping") as resp:
            assert resp.status == 200
        
        # 2. 전략 로드 확인
        async with api_client.get("https://api.freqtrade.local/api/v1/strategies") as resp:
            strategies = await resp.json()
            assert "FuturesAIRiskStrategy" in [s["strategy_name"] for s in strategies]
        
        # 3. 실시간 데이터 수신 테스트
        uri = "wss://api.freqtrade.local/api/v1/ws"
        async with websockets.connect(uri) as websocket:
            await websocket.send(json.dumps({"type": "subscribe", "data": "ticker"}))
            
            message = await asyncio.wait_for(websocket.recv(), timeout=30.0)
            data = json.loads(message)
            assert data["type"] == "ticker_update"
            assert "BTCUSDT" in data["data"]
    
    @pytest.mark.asyncio
    async def test_risk_management_triggers(self, api_client):
        """리스크 관리 트리거 테스트"""
        
        # 위험한 신호 전송
        dangerous_signal = {
            "symbol": "BTCUSDT",
            "side": "long",
            "leverage": 50,  # 과도한 레버리지
            "size_percent": 0.8  # 과도한 포지션 크기
        }
        
        async with api_client.post(
            "https://api.freqtrade.local/api/v1/signals",
            json=dangerous_signal
        ) as resp:
            assert resp.status == 400  # 리스크 관리자가 거부해야 함
            response = await resp.json()
            assert "risk_limit_exceeded" in response["error"]
    
    @pytest.mark.asyncio
    async def test_automated_scaling(self, api_client):
        """자동 스케일링 테스트"""
        
        # 시스템 로드 증가 시뮬레이션
        tasks = []
        for i in range(100):
            task = asyncio.create_task(
                api_client.get("https://api.freqtrade.local/api/v1/status")
            )
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 모든 요청이 성공적으로 처리되어야 함 (오토 스케일링으로)
        success_count = sum(1 for r in responses if not isinstance(r, Exception))
        assert success_count >= 95  # 95% 이상 성공률

class TestDisasterRecovery:
    """재해 복구 테스트"""
    
    @pytest.mark.asyncio
    async def test_database_failover(self):
        """데이터베이스 장애 복구 테스트"""
        
        # 메인 DB 중단 시뮬레이션
        subprocess.run(["docker", "stop", "timescaledb-primary"], check=True)
        
        # 복제 DB로 자동 전환 확인
        await asyncio.sleep(30)  # 장애 감지 및 전환 대기
        
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.freqtrade.local/api/v1/trades") as resp:
                assert resp.status == 200  # 여전히 작동해야 함
        
        # 메인 DB 복구
        subprocess.run(["docker", "start", "timescaledb-primary"], check=True)
    
    @pytest.mark.asyncio
    async def test_service_auto_recovery(self):
        """서비스 자동 복구 테스트"""
        
        # Freqtrade 서비스 강제 종료
        subprocess.run(["docker", "kill", "--signal=KILL", "freqtrade-strategy-1"])
        
        # 자동 재시작 확인 (최대 60초 대기)
        for _ in range(12):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get("https://api.freqtrade.local/api/v1/ping") as resp:
                        if resp.status == 200:
                            break
            except:
                pass
            await asyncio.sleep(5)
        else:
            pytest.fail("서비스가 60초 내에 복구되지 않음")
```

### 📋 **스테이징/프로덕션 배포**

```bash
# scripts/deploy.sh
#!/bin/bash
# 배포 자동화 스크립트

set -e

ENVIRONMENT=${1:-staging}
IMAGE_TAG=${2:-latest}
NAMESPACE="freqtrade-${ENVIRONMENT}"

echo "🚀 ${ENVIRONMENT} 환경으로 배포 시작..."

# 환경별 설정 검증
validate_environment() {
    case $ENVIRONMENT in
        "staging")
            REPLICAS=2
            RESOURCES_LIMIT_CPU="1000m"
            RESOURCES_LIMIT_MEMORY="2Gi"
            ;;
        "production")
            REPLICAS=5
            RESOURCES_LIMIT_CPU="2000m"
            RESOURCES_LIMIT_MEMORY="4Gi"
            ;;
        *)
            echo "❌ 지원되지 않는 환경: $ENVIRONMENT"
            exit 1
            ;;
    esac
}

# Kubernetes 매니페스트 적용
deploy_to_kubernetes() {
    echo "📦 Kubernetes 배포 중..."
    
    # 네임스페이스 생성/업데이트
    kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -
    
    # ConfigMap 및 Secret 적용
    envsubst < k8s/configmap.yaml | kubectl apply -f -
    envsubst < k8s/secrets.yaml | kubectl apply -f -
    
    # 서비스 배포
    envsubst < k8s/deployment.yaml | kubectl apply -f -
    envsubst < k8s/service.yaml | kubectl apply -f -
    envsubst < k8s/ingress.yaml | kubectl apply -f -
    
    # 배포 상태 확인
    kubectl rollout status deployment/freqtrade-app -n $NAMESPACE --timeout=300s
}

# 헬스체크
health_check() {
    echo "🏥 헬스체크 수행 중..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if kubectl get pods -n $NAMESPACE -l app=freqtrade-app | grep -q "Running"; then
            echo "✅ 헬스체크 통과"
            return 0
        fi
        
        echo "대기 중... ($attempt/$max_attempts)"
        sleep 10
        ((attempt++))
    done
    
    echo "❌ 헬스체크 실패"
    exit 1
}

# 스모크 테스트
smoke_test() {
    echo "💨 스모크 테스트 수행 중..."
    
    local api_url
    if [ "$ENVIRONMENT" = "staging" ]; then
        api_url="https://staging-api.freqtrade.local"
    else
        api_url="https://api.freqtrade.local"
    fi
    
    # API 핑 테스트
    if curl -f "$api_url/api/v1/ping" > /dev/null 2>&1; then
        echo "✅ API 핑 테스트 통과"
    else
        echo "❌ API 핑 테스트 실패"
        exit 1
    fi
    
    # 전략 로드 테스트
    if curl -f "$api_url/api/v1/strategies" > /dev/null 2>&1; then
        echo "✅ 전략 로드 테스트 통과"
    else
        echo "❌ 전략 로드 테스트 실패"
        exit 1
    fi
}

# 롤백 함수
rollback() {
    echo "🔄 이전 버전으로 롤백 중..."
    kubectl rollout undo deployment/freqtrade-app -n $NAMESPACE
    kubectl rollout status deployment/freqtrade-app -n $NAMESPACE --timeout=300s
    echo "✅ 롤백 완료"
}

# 메인 배포 로직
main() {
    validate_environment
    
    export ENVIRONMENT
    export IMAGE_TAG
    export NAMESPACE
    export REPLICAS
    export RESOURCES_LIMIT_CPU
    export RESOURCES_LIMIT_MEMORY
    
    deploy_to_kubernetes
    health_check
    smoke_test
    
    echo "🎉 ${ENVIRONMENT} 환경 배포 성공!"
}

# 트랩 설정 (실패시 롤백)
trap 'echo "❌ 배포 실패! 롤백 수행..."; rollback; exit 1' ERR

# 메인 함수 실행
main "$@"
```

---

## 🎯 **멀티 전략 관리 시스템**

### 🔄 **전략 라이프사이클 관리**

```python
# automation/strategy_lifecycle_manager.py
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass, asdict
import asyncio
import json
import importlib
import sys
from pathlib import Path

class StrategyStatus(Enum):
    """전략 상태"""
    INACTIVE = "inactive"
    LOADING = "loading"
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"
    UNLOADING = "unloading"

class PerformanceMetric(Enum):
    """성과 지표"""
    TOTAL_RETURN = "total_return"
    SHARPE_RATIO = "sharpe_ratio" 
    MAX_DRAWDOWN = "max_drawdown"
    WIN_RATE = "win_rate"
    PROFIT_FACTOR = "profit_factor"
    CALMAR_RATIO = "calmar_ratio"

@dataclass
class StrategyConfig:
    """전략 설정"""
    name: str
    class_name: str
    module_path: str
    config: Dict[str, Any]
    resource_limits: Dict[str, Any]
    performance_targets: Dict[PerformanceMetric, float]
    auto_scaling: bool = True
    auto_pause_on_drawdown: float = 0.15  # 15% 드로다운시 자동 일시정지

@dataclass
class StrategyInstance:
    """전략 인스턴스"""
    id: str
    config: StrategyConfig
    status: StrategyStatus
    instance: Optional[Any] = None
    performance: Dict[str, float] = None
    error_count: int = 0
    last_error: Optional[str] = None
    created_at: float = 0
    updated_at: float = 0

class StrategyLifecycleManager:
    """전략 라이프사이클 관리자"""
    
    def __init__(self, event_bus, resource_monitor, performance_analyzer):
        self.event_bus = event_bus
        self.resource_monitor = resource_monitor
        self.performance_analyzer = performance_analyzer
        self.strategies: Dict[str, StrategyInstance] = {}
        self.strategy_configs: Dict[str, StrategyConfig] = {}
        self.is_running = False
        
    async def initialize(self):
        """매니저 초기화"""
        # 설정 파일에서 전략 로드
        await self._load_strategy_configs()
        
        # 이벤트 구독
        self.event_bus.subscribe("strategy_performance_update", self._handle_performance_update)
        self.event_bus.subscribe("resource_usage_update", self._handle_resource_update)
        
        self.is_running = True
        
        # 백그라운드 태스크 시작
        asyncio.create_task(self._lifecycle_monitor())
    
    async def _load_strategy_configs(self):
        """전략 설정 로드"""
        config_path = Path("strategies/configs")
        
        for config_file in config_path.glob("*.json"):
            with open(config_file, 'r') as f:
                config_data = json.load(f)
                
            strategy_config = StrategyConfig(**config_data)
            self.strategy_configs[strategy_config.name] = strategy_config
    
    async def load_strategy(self, strategy_name: str) -> bool:
        """전략 로드"""
        if strategy_name not in self.strategy_configs:
            raise ValueError(f"Unknown strategy: {strategy_name}")
        
        config = self.strategy_configs[strategy_name]
        strategy_id = f"{strategy_name}_{int(time.time())}"
        
        # 전략 인스턴스 생성
        instance = StrategyInstance(
            id=strategy_id,
            config=config,
            status=StrategyStatus.LOADING,
            created_at=time.time(),
            updated_at=time.time()
        )
        
        self.strategies[strategy_id] = instance
        
        try:
            # 전략 모듈 동적 로드
            module = importlib.import_module(config.module_path)
            strategy_class = getattr(module, config.class_name)
            
            # 전략 인스턴스 생성
            strategy_instance = strategy_class(config.config)
            
            instance.instance = strategy_instance
            instance.status = StrategyStatus.ACTIVE
            instance.updated_at = time.time()
            
            # 이벤트 발행
            await self.event_bus.publish({
                "type": "strategy_loaded",
                "strategy_id": strategy_id,
                "strategy_name": strategy_name
            })
            
            return True
            
        except Exception as e:
            instance.status = StrategyStatus.ERROR
            instance.error_count += 1
            instance.last_error = str(e)
            
            await self.event_bus.publish({
                "type": "strategy_load_failed",
                "strategy_id": strategy_id,
                "error": str(e)
            })
            
            return False
    
    async def unload_strategy(self, strategy_id: str) -> bool:
        """전략 언로드"""
        if strategy_id not in self.strategies:
            return False
        
        instance = self.strategies[strategy_id]
        instance.status = StrategyStatus.UNLOADING
        
        try:
            # 진행 중인 거래 완료 대기
            if hasattr(instance.instance, 'close_all_positions'):
                await instance.instance.close_all_positions()
            
            # 리소스 정리
            if hasattr(instance.instance, 'cleanup'):
                await instance.instance.cleanup()
            
            # 인스턴스 제거
            del self.strategies[strategy_id]
            
            await self.event_bus.publish({
                "type": "strategy_unloaded",
                "strategy_id": strategy_id
            })
            
            return True
            
        except Exception as e:
            instance.status = StrategyStatus.ERROR
            instance.last_error = str(e)
            
            return False
    
    async def _handle_performance_update(self, event):
        """성과 업데이트 처리"""
        strategy_id = event.get("strategy_id")
        performance_data = event.get("performance_data")
        
        if strategy_id in self.strategies:
            instance = self.strategies[strategy_id]
            instance.performance = performance_data
            instance.updated_at = time.time()
            
            # 성과 기반 자동 액션
            await self._evaluate_performance_actions(instance)
    
    async def _evaluate_performance_actions(self, instance: StrategyInstance):
        """성과 기반 자동 액션 평가"""
        if not instance.performance:
            return
        
        config = instance.config
        performance = instance.performance
        
        # 드로다운 체크
        current_drawdown = performance.get("max_drawdown", 0)
        if current_drawdown > config.auto_pause_on_drawdown:
            await self._pause_strategy(instance.id)
            
            await self.event_bus.publish({
                "type": "strategy_auto_paused",
                "strategy_id": instance.id,
                "reason": f"Drawdown exceeded {config.auto_pause_on_drawdown*100}%"
            })
        
        # 성과 목표 달성 체크
        for metric, target in config.performance_targets.items():
            current_value = performance.get(metric.value, 0)
            
            if current_value < target:
                # 성과 미달시 리소스 조정
                await self._adjust_strategy_resources(instance.id, reduce=True)
    
    async def _pause_strategy(self, strategy_id: str):
        """전략 일시정지"""
        if strategy_id in self.strategies:
            instance = self.strategies[strategy_id]
            instance.status = StrategyStatus.PAUSED
            
            if hasattr(instance.instance, 'pause'):
                await instance.instance.pause()
    
    async def _adjust_strategy_resources(self, strategy_id: str, reduce: bool = False):
        """전략 리소스 조정"""
        # 리소스 모니터와 연동하여 CPU/메모리 할당 조정
        pass
    
    async def _lifecycle_monitor(self):
        """전략 라이프사이클 모니터링 루프"""
        while self.is_running:
            try:
                # 전략 상태 확인
                for strategy_id, instance in self.strategies.items():
                    
                    # 오류 상태 전략 재시작 시도
                    if instance.status == StrategyStatus.ERROR and instance.error_count < 3:
                        await self._attempt_strategy_recovery(strategy_id)
                    
                    # 장시간 비활성 전략 정리
                    if (time.time() - instance.updated_at) > 3600:  # 1시간
                        await self._cleanup_inactive_strategy(strategy_id)
                
                await asyncio.sleep(30)  # 30초마다 체크
                
            except Exception as e:
                print(f"Lifecycle monitor error: {e}")
                await asyncio.sleep(60)
    
    async def _attempt_strategy_recovery(self, strategy_id: str):
        """전략 복구 시도"""
        instance = self.strategies[strategy_id]
        
        try:
            # 전략 인스턴스 재생성
            config = instance.config
            module = importlib.import_module(config.module_path)
            strategy_class = getattr(module, config.class_name)
            
            new_instance = strategy_class(config.config)
            
            instance.instance = new_instance
            instance.status = StrategyStatus.ACTIVE
            instance.updated_at = time.time()
            
            await self.event_bus.publish({
                "type": "strategy_recovered",
                "strategy_id": strategy_id
            })
            
        except Exception as e:
            instance.error_count += 1
            instance.last_error = str(e)

class DynamicStrategyLoader:
    """동적 전략 로더"""
    
    def __init__(self, strategies_path: Path):
        self.strategies_path = strategies_path
        self.loaded_modules = {}
        
        # 파일 시스템 워처 설정
        self.watcher = None
        
    async def hot_reload_strategy(self, strategy_name: str):
        """전략 핫 리로드"""
        module_name = f"user_data.strategies.{strategy_name}"
        
        if module_name in sys.modules:
            # 모듈 리로드
            importlib.reload(sys.modules[module_name])
        else:
            # 새 모듈 로드
            importlib.import_module(module_name)
        
        # 로드된 모듈 추적
        self.loaded_modules[strategy_name] = sys.modules[module_name]
        
        return True
    
    async def start_file_watcher(self):
        """파일 변경 감지 시작"""
        # watchdog 라이브러리를 사용한 파일 변경 감지
        # 실제 구현에서는 파일 변경시 자동 리로드
        pass
```

### 🔧 **동적 전략 로딩/언로딩**

```python
# automation/dynamic_loading.py
import os
import sys
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import importlib.util

class StrategyFileHandler(FileSystemEventHandler):
    """전략 파일 변경 핸들러"""
    
    def __init__(self, strategy_manager):
        self.strategy_manager = strategy_manager
        self.file_hashes = {}
    
    def on_modified(self, event):
        """파일 수정 시 호출"""
        if not event.is_directory and event.src_path.endswith('.py'):
            self._handle_strategy_change(event.src_path)
    
    def _handle_strategy_change(self, file_path: str):
        """전략 파일 변경 처리"""
        # 파일 해시 확인 (중복 이벤트 방지)
        with open(file_path, 'rb') as f:
            file_hash = hashlib.md5(f.read()).hexdigest()
        
        if file_path in self.file_hashes and self.file_hashes[file_path] == file_hash:
            return
        
        self.file_hashes[file_path] = file_hash
        
        # 전략 이름 추출
        strategy_name = Path(file_path).stem
        
        # 전략 리로드
        asyncio.create_task(self.strategy_manager.reload_strategy(strategy_name))

class DynamicConfigManager:
    """동적 설정 관리자"""
    
    def __init__(self):
        self.config_cache = {}
        self.config_watchers = {}
    
    async def load_config(self, config_path: str) -> Dict[str, Any]:
        """설정 파일 로드"""
        if config_path in self.config_cache:
            return self.config_cache[config_path]
        
        with open(config_path, 'r') as f:
            if config_path.endswith('.json'):
                config = json.load(f)
            elif config_path.endswith('.yaml') or config_path.endswith('.yml'):
                config = yaml.safe_load(f)
            else:
                raise ValueError(f"Unsupported config format: {config_path}")
        
        self.config_cache[config_path] = config
        return config
    
    async def watch_config_changes(self, config_path: str, callback):
        """설정 파일 변경 감지"""
        observer = Observer()
        handler = ConfigChangeHandler(config_path, callback)
        
        observer.schedule(handler, Path(config_path).parent, recursive=False)
        observer.start()
        
        self.config_watchers[config_path] = observer

class ResourceIsolationManager:
    """리소스 격리 관리자"""
    
    def __init__(self):
        self.strategy_resources = {}
        self.resource_limits = {
            'cpu_percent': 80,
            'memory_mb': 1024,
            'max_threads': 4
        }
    
    async def allocate_resources(self, strategy_id: str, requirements: Dict[str, Any]):
        """전략별 리소스 할당"""
        
        # CPU 제한 설정
        if 'cpu_limit' in requirements:
            await self._set_cpu_limit(strategy_id, requirements['cpu_limit'])
        
        # 메모리 제한 설정
        if 'memory_limit' in requirements:
            await self._set_memory_limit(strategy_id, requirements['memory_limit'])
        
        # 스레드 풀 제한
        if 'thread_limit' in requirements:
            await self._set_thread_limit(strategy_id, requirements['thread_limit'])
        
        self.strategy_resources[strategy_id] = requirements
    
    async def _set_cpu_limit(self, strategy_id: str, cpu_limit: float):
        """CPU 사용률 제한"""
        # cgroups 또는 Docker 제한 사용
        pass
    
    async def _set_memory_limit(self, strategy_id: str, memory_limit: int):
        """메모리 사용량 제한"""
        # cgroups 또는 Docker 제한 사용
        pass
    
    async def monitor_resource_usage(self, strategy_id: str) -> Dict[str, float]:
        """전략별 리소스 사용량 모니터링"""
        # psutil 등을 사용한 실제 사용량 측정
        return {
            'cpu_percent': 0.0,
            'memory_mb': 0.0,
            'thread_count': 0
        }
```

---

## 📊 **실시간 데이터 파이프라인**

### 🌊 **WebSocket 데이터 스트리밍**

```python
# automation/data_pipeline.py
import asyncio
import websockets
import json
import aioredis
import aiokafka
from typing import Dict, List, Callable, Optional, Any
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from dataclasses import dataclass
import logging
from collections import deque
import time

@dataclass
class MarketData:
    """시장 데이터 구조"""
    symbol: str
    timestamp: float
    price: float
    volume: float
    bid_price: float
    ask_price: float
    funding_rate: Optional[float] = None
    open_interest: Optional[float] = None

class WebSocketDataStreamer:
    """WebSocket 데이터 스트리머"""
    
    def __init__(self, exchange_urls: Dict[str, str], redis_client, kafka_producer):
        self.exchange_urls = exchange_urls
        self.redis_client = redis_client
        self.kafka_producer = kafka_producer
        self.connections = {}
        self.subscribed_symbols = set()
        self.data_handlers = []
        self.is_running = False
        
        # 데이터 품질 모니터링
        self.data_quality_metrics = {
            'messages_received': 0,
            'messages_processed': 0,
            'errors': 0,
            'latency_ms': deque(maxlen=1000)
        }
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    async def start_streaming(self, symbols: List[str]):
        """스트리밍 시작"""
        self.subscribed_symbols.update(symbols)
        self.is_running = True
        
        # 각 거래소별 연결
        tasks = []
        for exchange, url in self.exchange_urls.items():
            task = asyncio.create_task(self._connect_to_exchange(exchange, url, symbols))
            tasks.append(task)
        
        # 데이터 품질 모니터링 태스크
        tasks.append(asyncio.create_task(self._monitor_data_quality()))
        
        await asyncio.gather(*tasks)
    
    async def _connect_to_exchange(self, exchange: str, url: str, symbols: List[str]):
        """거래소 연결"""
        retry_count = 0
        max_retries = 5
        
        while self.is_running and retry_count < max_retries:
            try:
                async with websockets.connect(
                    url,
                    ping_interval=20,
                    ping_timeout=10,
                    close_timeout=10
                ) as websocket:
                    
                    self.connections[exchange] = websocket
                    self.logger.info(f"Connected to {exchange}")
                    
                    # 구독 메시지 전송
                    await self._subscribe_to_symbols(websocket, exchange, symbols)
                    
                    # 메시지 수신 루프
                    async for message in websocket:
                        await self._process_message(exchange, message)
                        
            except Exception as e:
                retry_count += 1
                self.logger.error(f"Connection error for {exchange}: {e}")
                await asyncio.sleep(min(retry_count * 2, 30))  # 지수 백오프
        
        self.logger.error(f"Max retries exceeded for {exchange}")
    
    async def _subscribe_to_symbols(self, websocket, exchange: str, symbols: List[str]):
        """심볼 구독"""
        if exchange == "binance":
            # Binance 구독 형식
            streams = []
            for symbol in symbols:
                streams.extend([
                    f"{symbol.lower()}@ticker",
                    f"{symbol.lower()}@bookTicker",
                    f"{symbol.lower()}@kline_1m"
                ])
            
            subscribe_msg = {
                "method": "SUBSCRIBE",
                "params": streams,
                "id": 1
            }
            
            await websocket.send(json.dumps(subscribe_msg))
    
    async def _process_message(self, exchange: str, message: str):
        """메시지 처리"""
        start_time = time.time()
        
        try:
            data = json.loads(message)
            self.data_quality_metrics['messages_received'] += 1
            
            # 데이터 파싱 및 정규화
            market_data = await self._parse_market_data(exchange, data)
            
            if market_data:
                # Redis에 실시간 데이터 저장
                await self._store_realtime_data(market_data)
                
                # Kafka로 데이터 스트리밍
                await self._stream_to_kafka(market_data)
                
                # 등록된 핸들러들에게 데이터 전달
                for handler in self.data_handlers:
                    asyncio.create_task(handler(market_data))
                
                self.data_quality_metrics['messages_processed'] += 1
            
            # 레이턴시 측정
            latency = (time.time() - start_time) * 1000
            self.data_quality_metrics['latency_ms'].append(latency)
            
        except Exception as e:
            self.data_quality_metrics['errors'] += 1
            self.logger.error(f"Message processing error: {e}")
    
    async def _parse_market_data(self, exchange: str, data: Dict) -> Optional[MarketData]:
        """시장 데이터 파싱"""
        try:
            if exchange == "binance":
                if 'stream' in data and data['stream'].endswith('@ticker'):
                    ticker_data = data['data']
                    return MarketData(
                        symbol=ticker_data['s'],
                        timestamp=float(ticker_data['E']) / 1000,
                        price=float(ticker_data['c']),
                        volume=float(ticker_data['v']),
                        bid_price=float(ticker_data['b']),
                        ask_price=float(ticker_data['a'])
                    )
            
            return None
            
        except KeyError as e:
            self.logger.warning(f"Missing field in market data: {e}")
            return None
    
    async def _store_realtime_data(self, market_data: MarketData):
        """실시간 데이터 저장"""
        key = f"realtime:{market_data.symbol}"
        
        data_dict = {
            'price': market_data.price,
            'volume': market_data.volume,
            'bid': market_data.bid_price,
            'ask': market_data.ask_price,
            'timestamp': market_data.timestamp
        }
        
        # Redis에 최신 데이터 저장 (TTL 1시간)
        await self.redis_client.setex(key, 3600, json.dumps(data_dict))
        
        # 시계열 데이터로도 저장 (최근 1000개 틱)
        list_key = f"ticks:{market_data.symbol}"
        await self.redis_client.lpush(list_key, json.dumps(data_dict))
        await self.redis_client.ltrim(list_key, 0, 999)
    
    async def _stream_to_kafka(self, market_data: MarketData):
        """Kafka로 데이터 스트리밍"""
        topic = f"market-data-{market_data.symbol.lower()}"
        
        message = {
            'symbol': market_data.symbol,
            'timestamp': market_data.timestamp,
            'price': market_data.price,
            'volume': market_data.volume,
            'bid_price': market_data.bid_price,
            'ask_price': market_data.ask_price
        }
        
        await self.kafka_producer.send(topic, json.dumps(message).encode())
    
    async def _monitor_data_quality(self):
        """데이터 품질 모니터링"""
        while self.is_running:
            await asyncio.sleep(60)  # 1분마다 체크
            
            metrics = self.data_quality_metrics
            
            # 처리율 계산
            processing_rate = metrics['messages_processed'] / max(metrics['messages_received'], 1)
            
            # 평균 레이턴시 계산
            avg_latency = np.mean(metrics['latency_ms']) if metrics['latency_ms'] else 0
            
            # 품질 지표 로깅
            self.logger.info(f"Data Quality - Processing Rate: {processing_rate:.2%}, "
                           f"Avg Latency: {avg_latency:.2f}ms, "
                           f"Errors: {metrics['errors']}")
            
            # 품질 이슈 감지
            if processing_rate < 0.95:  # 95% 미만
                self.logger.warning("Low processing rate detected!")
            
            if avg_latency > 100:  # 100ms 초과
                self.logger.warning("High latency detected!")
    
    def add_data_handler(self, handler: Callable):
        """데이터 핸들러 추가"""
        self.data_handlers.append(handler)

class RealTimeDataProcessor:
    """실시간 데이터 처리기"""
    
    def __init__(self, redis_client):
        self.redis_client = redis_client
        self.technical_indicators = {}
        self.data_windows = {}  # 윈도우 데이터 저장
        
    async def process_tick_data(self, market_data: MarketData):
        """틱 데이터 처리"""
        symbol = market_data.symbol
        
        # 기술적 지표 계산
        await self._update_technical_indicators(market_data)
        
        # 윈도우 데이터 업데이트
        await self._update_data_windows(market_data)
        
        # 신호 생성 (필요시)
        signals = await self._generate_signals(market_data)
        
        if signals:
            await self._publish_signals(signals)
    
    async def _update_technical_indicators(self, market_data: MarketData):
        """기술적 지표 업데이트"""
        symbol = market_data.symbol
        
        if symbol not in self.technical_indicators:
            self.technical_indicators[symbol] = {
                'prices': deque(maxlen=200),
                'volumes': deque(maxlen=200),
                'ema_12': None,
                'ema_26': None,
                'rsi': None,
                'macd': None
            }
        
        indicators = self.technical_indicators[symbol]
        indicators['prices'].append(market_data.price)
        indicators['volumes'].append(market_data.volume)
        
        # 충분한 데이터가 있을 때만 지표 계산
        if len(indicators['prices']) >= 26:
            prices = np.array(indicators['prices'])
            
            # EMA 계산
            indicators['ema_12'] = self._calculate_ema(prices, 12)
            indicators['ema_26'] = self._calculate_ema(prices, 26)
            
            # RSI 계산
            if len(indicators['prices']) >= 14:
                indicators['rsi'] = self._calculate_rsi(prices, 14)
            
            # MACD 계산
            if indicators['ema_12'] is not None and indicators['ema_26'] is not None:
                indicators['macd'] = indicators['ema_12'] - indicators['ema_26']
        
        # Redis에 지표 저장
        await self._store_indicators(symbol, indicators)
    
    def _calculate_ema(self, prices: np.ndarray, period: int) -> float:
        """EMA 계산"""
        alpha = 2 / (period + 1)
        ema = prices[0]
        
        for price in prices[1:]:
            ema = alpha * price + (1 - alpha) * ema
        
        return ema
    
    def _calculate_rsi(self, prices: np.ndarray, period: int) -> float:
        """RSI 계산"""
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    async def _store_indicators(self, symbol: str, indicators: Dict):
        """지표를 Redis에 저장"""
        key = f"indicators:{symbol}"
        
        data = {
            'ema_12': indicators.get('ema_12'),
            'ema_26': indicators.get('ema_26'),
            'rsi': indicators.get('rsi'),
            'macd': indicators.get('macd'),
            'timestamp': time.time()
        }
        
        # None 값 제거
        data = {k: v for k, v in data.items() if v is not None}
        
        await self.redis_client.setex(key, 300, json.dumps(data))  # 5분 TTL

class DistributedCacheManager:
    """분산 캐시 관리자"""
    
    def __init__(self, redis_cluster_nodes: List[str]):
        self.redis_cluster_nodes = redis_cluster_nodes
        self.redis_cluster = None
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'errors': 0
        }
    
    async def initialize(self):
        """캐시 클러스터 초기화"""
        self.redis_cluster = aioredis.RedisCluster(
            startup_nodes=[{"host": node.split(':')[0], "port": int(node.split(':')[1])} 
                          for node in self.redis_cluster_nodes],
            decode_responses=True,
            skip_full_coverage_check=True
        )
    
    async def get_market_data(self, symbol: str, timeframe: str = "1m") -> Optional[Dict]:
        """시장 데이터 조회"""
        try:
            key = f"market:{symbol}:{timeframe}"
            data = await self.redis_cluster.get(key)
            
            if data:
                self.cache_stats['hits'] += 1
                return json.loads(data)
            else:
                self.cache_stats['misses'] += 1
                return None
                
        except Exception as e:
            self.cache_stats['errors'] += 1
            logging.error(f"Cache get error: {e}")
            return None
    
    async def set_market_data(self, symbol: str, timeframe: str, data: Dict, ttl: int = 300):
        """시장 데이터 저장"""
        try:
            key = f"market:{symbol}:{timeframe}"
            await self.redis_cluster.setex(key, ttl, json.dumps(data))
            
        except Exception as e:
            self.cache_stats['errors'] += 1
            logging.error(f"Cache set error: {e}")
    
    async def invalidate_cache(self, pattern: str):
        """캐시 무효화"""
        try:
            keys = await self.redis_cluster.keys(pattern)
            if keys:
                await self.redis_cluster.delete(*keys)
                
        except Exception as e:
            logging.error(f"Cache invalidation error: {e}")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """캐시 통계 조회"""
        total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
        hit_rate = self.cache_stats['hits'] / max(total_requests, 1)
        
        return {
            **self.cache_stats,
            'hit_rate': hit_rate,
            'total_requests': total_requests
        }

class DataQualityMonitor:
    """데이터 품질 모니터"""
    
    def __init__(self, alert_manager):
        self.alert_manager = alert_manager
        self.quality_metrics = {}
        self.thresholds = {
            'latency_ms': 100,
            'error_rate': 0.01,  # 1%
            'data_freshness_seconds': 60,
            'missing_data_rate': 0.05  # 5%
        }
    
    async def monitor_data_stream(self, symbol: str, data_source: str):
        """데이터 스트림 모니터링"""
        while True:
            try:
                # 데이터 신선도 체크
                await self._check_data_freshness(symbol, data_source)
                
                # 누락 데이터 체크
                await self._check_missing_data(symbol, data_source)
                
                # 이상치 검출
                await self._detect_anomalies(symbol, data_source)
                
                await asyncio.sleep(30)  # 30초마다 체크
                
            except Exception as e:
                logging.error(f"Data quality monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def _check_data_freshness(self, symbol: str, data_source: str):
        """데이터 신선도 체크"""
        # 마지막 데이터 타임스탬프 확인
        # 임계값을 초과하면 알림
        pass
    
    async def _check_missing_data(self, symbol: str, data_source: str):
        """누락 데이터 체크"""
        # 예상 데이터 포인트 대비 실제 수신 데이터 비교
        pass
    
    async def _detect_anomalies(self, symbol: str, data_source: str):
        """이상치 검출"""
        # 통계적 방법으로 이상치 검출
        # 가격 급등락, 비정상적 거래량 등
        pass

---

## 📢 **통합 알림 시스템**

### 📱 **멀티채널 알림 (텔레그램/슬랙/이메일/SMS)**

```python
# automation/notification_system.py
import asyncio
import aiohttp
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass
import json
import logging
from datetime import datetime, timedelta

class NotificationChannel(Enum):
    """알림 채널 타입"""
    TELEGRAM = "telegram"
    SLACK = "slack"
    EMAIL = "email"
    SMS = "sms"
    WEBHOOK = "webhook"
    DISCORD = "discord"

class NotificationPriority(Enum):
    """알림 우선순위"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
    EMERGENCY = 5

@dataclass
class NotificationConfig:
    """알림 설정"""
    channel: NotificationChannel
    enabled: bool
    config: Dict[str, Any]
    priority_threshold: NotificationPriority = NotificationPriority.LOW
    rate_limit: Optional[int] = None  # 분당 최대 알림 수
    quiet_hours: Optional[List[int]] = None  # 알림 제한 시간대

@dataclass
class Notification:
    """알림 메시지"""
    title: str
    message: str
    priority: NotificationPriority
    tags: List[str] = None
    metadata: Dict[str, Any] = None
    channel_override: Optional[NotificationChannel] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class NotificationTemplate:
    """알림 템플릿"""
    
    def __init__(self):
        self.templates = {
            'trade_entry': {
                'title': '🔵 포지션 진입',
                'message': '{side} {symbol} | 가격: ${price} | 레버리지: {leverage}x | 크기: ${position_size}'
            },
            'trade_exit': {
                'title': '🔴 포지션 청산',
                'message': '{side} {symbol} 청산 | 가격: ${price} | P&L: ${pnl} ({pnl_percent}%)'
            },
            'risk_alert': {
                'title': '⚠️ 리스크 경고',
                'message': '{alert_type}: {symbol} | 현재값: {current_value} | 임계값: {threshold}'
            },
            'system_error': {
                'title': '🚨 시스템 오류',
                'message': '오류 발생: {error_type} | 상세: {error_details} | 시간: {timestamp}'
            },
            'funding_rate': {
                'title': '💰 자금 조달료',
                'message': '{symbol} 자금 조달료: {rate}% | 다음 정산: {next_funding}'
            },
            'liquidation_warning': {
                'title': '🚨 청산 위험',
                'message': '{symbol} 청산 위험! | 현재가: ${current_price} | 청산가: ${liquidation_price} | 거리: {distance}%'
            }
        }
    
    def format_notification(self, template_name: str, **kwargs) -> Notification:
        """템플릿을 사용한 알림 생성"""
        template = self.templates.get(template_name)
        if not template:
            raise ValueError(f"Template not found: {template_name}")
        
        title = template['title'].format(**kwargs)
        message = template['message'].format(**kwargs)
        
        # 우선순위 자동 결정
        priority = self._determine_priority(template_name, kwargs)
        
        return Notification(
            title=title,
            message=message,
            priority=priority,
            tags=[template_name],
            metadata=kwargs
        )
    
    def _determine_priority(self, template_name: str, kwargs: Dict) -> NotificationPriority:
        """템플릿과 데이터를 기반으로 우선순위 결정"""
        if template_name == 'liquidation_warning':
            return NotificationPriority.EMERGENCY
        elif template_name == 'system_error':
            return NotificationPriority.CRITICAL
        elif template_name == 'risk_alert':
            return NotificationPriority.HIGH
        elif template_name in ['trade_entry', 'trade_exit']:
            # 손실 크기에 따라 우선순위 결정
            pnl_percent = kwargs.get('pnl_percent', 0)
            if pnl_percent < -10:
                return NotificationPriority.HIGH
            elif abs(pnl_percent) > 5:
                return NotificationPriority.MEDIUM
            else:
                return NotificationPriority.LOW
        else:
            return NotificationPriority.LOW

class TelegramNotifier:
    """텔레그램 알림"""
    
    def __init__(self, bot_token: str, chat_ids: List[str]):
        self.bot_token = bot_token
        self.chat_ids = chat_ids
        self.api_url = f"https://api.telegram.org/bot{bot_token}"
        
    async def send_notification(self, notification: Notification) -> bool:
        """텔레그램 알림 전송"""
        try:
            # 우선순위에 따른 이모지 추가
            priority_emojis = {
                NotificationPriority.LOW: "ℹ️",
                NotificationPriority.MEDIUM: "⚠️",
                NotificationPriority.HIGH: "🔥",
                NotificationPriority.CRITICAL: "🚨",
                NotificationPriority.EMERGENCY: "🆘"
            }
            
            emoji = priority_emojis.get(notification.priority, "📢")
            message = f"{emoji} {notification.title}\n\n{notification.message}"
            
            # 마크다운 포맷팅
            if notification.priority >= NotificationPriority.HIGH:
                message = f"*{message}*"
            
            async with aiohttp.ClientSession() as session:
                success_count = 0
                
                for chat_id in self.chat_ids:
                    payload = {
                        'chat_id': chat_id,
                        'text': message,
                        'parse_mode': 'Markdown'
                    }
                    
                    async with session.post(f"{self.api_url}/sendMessage", json=payload) as resp:
                        if resp.status == 200:
                            success_count += 1
                        else:
                            logging.error(f"Telegram send failed: {await resp.text()}")
                
                return success_count > 0
                
        except Exception as e:
            logging.error(f"Telegram notification error: {e}")
            return False

class SlackNotifier:
    """슬랙 알림"""
    
    def __init__(self, webhook_url: str, channels: List[str]):
        self.webhook_url = webhook_url
        self.channels = channels
        
    async def send_notification(self, notification: Notification) -> bool:
        """슬랙 알림 전송"""
        try:
            # 우선순위에 따른 색상 설정
            colors = {
                NotificationPriority.LOW: "#36a64f",      # 녹색
                NotificationPriority.MEDIUM: "#ff9800",   # 주황색
                NotificationPriority.HIGH: "#f44336",     # 빨간색
                NotificationPriority.CRITICAL: "#9c27b0", # 보라색
                NotificationPriority.EMERGENCY: "#000000" # 검은색
            }
            
            color = colors.get(notification.priority, "#36a64f")
            
            payload = {
                "attachments": [
                    {
                        "color": color,
                        "title": notification.title,
                        "text": notification.message,
                        "footer": "Freqtrade Automation",
                        "ts": int(notification.timestamp.timestamp())
                    }
                ]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=payload) as resp:
                    return resp.status == 200
                    
        except Exception as e:
            logging.error(f"Slack notification error: {e}")
            return False

class EmailNotifier:
    """이메일 알림"""
    
    def __init__(self, smtp_config: Dict[str, Any], recipients: List[str]):
        self.smtp_config = smtp_config
        self.recipients = recipients
        
    async def send_notification(self, notification: Notification) -> bool:
        """이메일 알림 전송"""
        try:
            # HTML 템플릿 생성
            html_content = self._create_html_template(notification)
            
            msg = MimeMultipart('alternative')
            msg['Subject'] = notification.title
            msg['From'] = self.smtp_config['username']
            msg['To'] = ', '.join(self.recipients)
            
            # HTML 파트 추가
            html_part = MimeText(html_content, 'html')
            msg.attach(html_part)
            
            # SMTP 서버 연결 및 전송
            with smtplib.SMTP(self.smtp_config['host'], self.smtp_config['port']) as server:
                server.starttls()
                server.login(self.smtp_config['username'], self.smtp_config['password'])
                server.send_message(msg)
                
            return True
            
        except Exception as e:
            logging.error(f"Email notification error: {e}")
            return False
    
    def _create_html_template(self, notification: Notification) -> str:
        """HTML 이메일 템플릿 생성"""
        priority_colors = {
            NotificationPriority.LOW: "#4CAF50",
            NotificationPriority.MEDIUM: "#FF9800",
            NotificationPriority.HIGH: "#F44336",
            NotificationPriority.CRITICAL: "#9C27B0",
            NotificationPriority.EMERGENCY: "#000000"
        }
        
        color = priority_colors.get(notification.priority, "#4CAF50")
        
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto;">
                <div style="background-color: {color}; color: white; padding: 20px; border-radius: 5px 5px 0 0;">
                    <h2 style="margin: 0;">{notification.title}</h2>
                </div>
                <div style="background-color: #f5f5f5; padding: 20px; border-radius: 0 0 5px 5px;">
                    <p style="font-size: 16px; line-height: 1.6;">{notification.message}</p>
                    <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                    <p style="font-size: 12px; color: #666;">
                        시간: {notification.timestamp.strftime('%Y-%m-%d %H:%M:%S')}<br>
                        우선순위: {notification.priority.name}
                    </p>
                </div>
            </div>
        </body>
        </html>
        """

class NotificationRouter:
    """알림 라우팅 및 필터링"""
    
    def __init__(self):
        self.channels = {}
        self.routing_rules = []
        self.rate_limiters = {}
        
    def add_channel(self, name: str, notifier, config: NotificationConfig):
        """알림 채널 추가"""
        self.channels[name] = {
            'notifier': notifier,
            'config': config
        }
        
        # 레이트 리미터 초기화
        if config.rate_limit:
            self.rate_limiters[name] = {
                'count': 0,
                'reset_time': datetime.now() + timedelta(minutes=1)
            }
    
    def add_routing_rule(self, condition: Callable, channels: List[str]):
        """라우팅 규칙 추가"""
        self.routing_rules.append({
            'condition': condition,
            'channels': channels
        })
    
    async def route_notification(self, notification: Notification) -> Dict[str, bool]:
        """알림 라우팅"""
        results = {}
        
        # 적용할 채널 결정
        target_channels = self._determine_channels(notification)
        
        # 각 채널로 알림 전송
        for channel_name in target_channels:
            if channel_name not in self.channels:
                continue
                
            channel_info = self.channels[channel_name]
            config = channel_info['config']
            
            # 채널 활성화 체크
            if not config.enabled:
                continue
            
            # 우선순위 체크
            if notification.priority.value < config.priority_threshold.value:
                continue
            
            # 조용한 시간 체크
            if self._is_quiet_hours(config):
                continue
            
            # 레이트 리미트 체크
            if not self._check_rate_limit(channel_name, config):
                continue
            
            # 알림 전송
            try:
                success = await channel_info['notifier'].send_notification(notification)
                results[channel_name] = success
                
                if success and config.rate_limit:
                    self._update_rate_limit(channel_name)
                    
            except Exception as e:
                logging.error(f"Notification routing error for {channel_name}: {e}")
                results[channel_name] = False
        
        return results
    
    def _determine_channels(self, notification: Notification) -> List[str]:
        """알림에 적용할 채널 결정"""
        if notification.channel_override:
            return [ch for ch, info in self.channels.items() 
                   if info['config'].channel == notification.channel_override]
        
        # 라우팅 규칙 적용
        for rule in self.routing_rules:
            if rule['condition'](notification):
                return rule['channels']
        
        # 기본: 모든 채널
        return list(self.channels.keys())
    
    def _is_quiet_hours(self, config: NotificationConfig) -> bool:
        """조용한 시간 체크"""
        if not config.quiet_hours:
            return False
        
        current_hour = datetime.now().hour
        return current_hour in config.quiet_hours
    
    def _check_rate_limit(self, channel_name: str, config: NotificationConfig) -> bool:
        """레이트 리미트 체크"""
        if not config.rate_limit or channel_name not in self.rate_limiters:
            return True
        
        limiter = self.rate_limiters[channel_name]
        
        # 리셋 시간 체크
        if datetime.now() > limiter['reset_time']:
            limiter['count'] = 0
            limiter['reset_time'] = datetime.now() + timedelta(minutes=1)
        
        return limiter['count'] < config.rate_limit
    
    def _update_rate_limit(self, channel_name: str):
        """레이트 리미트 업데이트"""
        if channel_name in self.rate_limiters:
            self.rate_limiters[channel_name]['count'] += 1

class EscalationManager:
    """에스컬레이션 정책 관리"""
    
    def __init__(self, notification_router: NotificationRouter):
        self.notification_router = notification_router
        self.escalation_policies = {}
        self.pending_escalations = {}
        
    def add_escalation_policy(self, name: str, policy: Dict[str, Any]):
        """에스컬레이션 정책 추가"""
        self.escalation_policies[name] = policy
    
    async def handle_notification(self, notification: Notification, policy_name: str):
        """에스컬레이션 정책에 따른 알림 처리"""
        if policy_name not in self.escalation_policies:
            # 기본 라우팅
            return await self.notification_router.route_notification(notification)
        
        policy = self.escalation_policies[policy_name]
        
        # 1차 알림 전송
        primary_result = await self._send_primary_notification(notification, policy)
        
        # 에스컬레이션 필요 여부 확인
        if self._should_escalate(notification, primary_result, policy):
            await self._schedule_escalation(notification, policy)
        
        return primary_result
    
    async def _send_primary_notification(self, notification: Notification, policy: Dict) -> Dict[str, bool]:
        """1차 알림 전송"""
        # 우선순위에 따른 채널 선택
        primary_channels = policy.get('primary_channels', {})
        channels = primary_channels.get(notification.priority.name.lower(), [])
        
        if channels:
            # 특정 채널로만 전송
            original_override = notification.channel_override
            results = {}
            
            for channel in channels:
                notification.channel_override = NotificationChannel(channel)
                result = await self.notification_router.route_notification(notification)
                results.update(result)
            
            notification.channel_override = original_override
            return results
        else:
            # 기본 라우팅
            return await self.notification_router.route_notification(notification)
    
    def _should_escalate(self, notification: Notification, result: Dict[str, bool], policy: Dict) -> bool:
        """에스컬레이션 필요 여부 판단"""
        # 긴급 상황은 항상 에스컬레이션
        if notification.priority == NotificationPriority.EMERGENCY:
            return True
        
        # 1차 알림 실패시 에스컬레이션
        if not any(result.values()):
            return True
        
        # 정책별 에스컬레이션 조건 체크
        escalation_conditions = policy.get('escalation_conditions', {})
        
        return any(condition(notification, result) for condition in escalation_conditions)
    
    async def _schedule_escalation(self, notification: Notification, policy: Dict):
        """에스컬레이션 스케줄링"""
        escalation_delay = policy.get('escalation_delay_minutes', 5)
        
        # 에스컬레이션 대기 목록에 추가
        escalation_id = f"{notification.timestamp.isoformat()}_{hash(notification.message)}"
        self.pending_escalations[escalation_id] = {
            'notification': notification,
            'policy': policy,
            'escalation_time': datetime.now() + timedelta(minutes=escalation_delay)
        }
        
        # 지연 후 에스컬레이션 실행
        await asyncio.sleep(escalation_delay * 60)
        await self._execute_escalation(escalation_id)
    
    async def _execute_escalation(self, escalation_id: str):
        """에스컬레이션 실행"""
        if escalation_id not in self.pending_escalations:
            return
        
        escalation_info = self.pending_escalations[escalation_id]
        notification = escalation_info['notification']
        policy = escalation_info['policy']
        
        # 에스컬레이션 알림 생성
        escalated_notification = Notification(
            title=f"🚨 ESCALATED: {notification.title}",
            message=f"원본 알림이 처리되지 않았습니다.\n\n{notification.message}",
            priority=NotificationPriority.CRITICAL,
            tags=['escalated'] + (notification.tags or [])
        )
        
        # 에스컬레이션 채널로 전송
        escalation_channels = policy.get('escalation_channels', [])
        for channel in escalation_channels:
            escalated_notification.channel_override = NotificationChannel(channel)
            await self.notification_router.route_notification(escalated_notification)
        
        # 에스컬레이션 완료 후 제거
        del self.pending_escalations[escalation_id]

# 사용 예시
async def setup_notification_system():
    """알림 시스템 설정 예시"""
    
    # 알림 라우터 생성
    router = NotificationRouter()
    
    # 텔레그램 채널 설정
    telegram_notifier = TelegramNotifier(
        bot_token="YOUR_BOT_TOKEN",
        chat_ids=["CHAT_ID_1", "CHAT_ID_2"]
    )
    
    telegram_config = NotificationConfig(
        channel=NotificationChannel.TELEGRAM,
        enabled=True,
        config={},
        priority_threshold=NotificationPriority.LOW,
        rate_limit=10  # 분당 10개
    )
    
    router.add_channel("telegram_main", telegram_notifier, telegram_config)
    
    # 슬랙 채널 설정
    slack_notifier = SlackNotifier(
        webhook_url="SLACK_WEBHOOK_URL",
        channels=["#trading-alerts"]
    )
    
    slack_config = NotificationConfig(
        channel=NotificationChannel.SLACK,
        enabled=True,
        config={},
        priority_threshold=NotificationPriority.MEDIUM,
        quiet_hours=[0, 1, 2, 3, 4, 5, 6]  # 새벽 시간 제한
    )
    
    router.add_channel("slack_main", slack_notifier, slack_config)
    
    # 라우팅 규칙 설정
    router.add_routing_rule(
        condition=lambda n: n.priority >= NotificationPriority.CRITICAL,
        channels=["telegram_main", "slack_main"]  # 중요 알림은 모든 채널
    )
    
    router.add_routing_rule(
        condition=lambda n: 'trade' in (n.tags or []),
        channels=["telegram_main"]  # 거래 알림은 텔레그램만
    )
    
    # 에스컬레이션 매니저 설정
    escalation_manager = EscalationManager(router)
    
    escalation_policy = {
        'primary_channels': {
            'emergency': ['telegram'],
            'critical': ['telegram', 'slack'],
            'high': ['telegram']
        },
        'escalation_delay_minutes': 5,
        'escalation_channels': ['email', 'sms'],
        'escalation_conditions': [
            lambda n, r: not any(r.values()),  # 모든 알림 실패
            lambda n, r: n.priority == NotificationPriority.EMERGENCY  # 긴급 상황
        ]
    }
    
    escalation_manager.add_escalation_policy("default", escalation_policy)
    
    return router, escalation_manager

---

## 🔄 **자동 장애 복구 시스템**

### 🏥 **헬스체크 및 자동 재시작**

```python
# automation/health_monitoring.py
import asyncio
import aiohttp
import psutil
import docker
from typing import Dict, List, Optional, Callable, Any
from enum import Enum
from dataclasses import dataclass
import logging
import time
from datetime import datetime, timedelta

class HealthStatus(Enum):
    """헬스 상태"""
    HEALTHY = "healthy"
    WARNING = "warning"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

class ServiceType(Enum):
    """서비스 타입"""
    FREQTRADE = "freqtrade"
    DATABASE = "database"
    REDIS = "redis"
    MESSAGE_QUEUE = "message_queue"
    API_GATEWAY = "api_gateway"
    MONITORING = "monitoring"

@dataclass
class HealthCheck:
    """헬스체크 설정"""
    name: str
    service_type: ServiceType
    check_function: Callable
    check_interval: int = 30  # 초
    timeout: int = 10
    failure_threshold: int = 3
    success_threshold: int = 2
    recovery_action: Optional[Callable] = None

@dataclass
class HealthResult:
    """헬스체크 결과"""
    name: str
    status: HealthStatus
    message: str
    response_time: float
    timestamp: datetime
    metadata: Dict[str, Any] = None

class HealthMonitor:
    """헬스 모니터링 시스템"""
    
    def __init__(self, notification_system, recovery_manager):
        self.notification_system = notification_system
        self.recovery_manager = recovery_manager
        self.health_checks: Dict[str, HealthCheck] = {}
        self.health_states: Dict[str, Dict] = {}
        self.is_running = False
        
        # Docker 클라이언트
        self.docker_client = docker.from_env()
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def register_health_check(self, health_check: HealthCheck):
        """헬스체크 등록"""
        self.health_checks[health_check.name] = health_check
        self.health_states[health_check.name] = {
            'current_status': HealthStatus.UNKNOWN,
            'consecutive_failures': 0,
            'consecutive_successes': 0,
            'last_check': None,
            'last_recovery_attempt': None
        }
    
    async def start_monitoring(self):
        """모니터링 시작"""
        self.is_running = True
        
        # 각 헬스체크에 대한 태스크 생성
        tasks = []
        for name, health_check in self.health_checks.items():
            task = asyncio.create_task(self._monitor_service(name, health_check))
            tasks.append(task)
        
        await asyncio.gather(*tasks)
    
    async def _monitor_service(self, name: str, health_check: HealthCheck):
        """서비스 모니터링 루프"""
        while self.is_running:
            try:
                # 헬스체크 실행
                result = await self._execute_health_check(health_check)
                
                # 상태 업데이트
                await self._update_health_state(name, result, health_check)
                
                # 지정된 간격 대기
                await asyncio.sleep(health_check.check_interval)
                
            except Exception as e:
                self.logger.error(f"Health check error for {name}: {e}")
                await asyncio.sleep(health_check.check_interval)
    
    async def _execute_health_check(self, health_check: HealthCheck) -> HealthResult:
        """헬스체크 실행"""
        start_time = time.time()
        
        try:
            # 타임아웃과 함께 헬스체크 함수 실행
            result = await asyncio.wait_for(
                health_check.check_function(),
                timeout=health_check.timeout
            )
            
            response_time = (time.time() - start_time) * 1000  # ms
            
            return HealthResult(
                name=health_check.name,
                status=result.get('status', HealthStatus.HEALTHY),
                message=result.get('message', 'OK'),
                response_time=response_time,
                timestamp=datetime.now(),
                metadata=result.get('metadata', {})
            )
            
        except asyncio.TimeoutError:
            return HealthResult(
                name=health_check.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check timeout ({health_check.timeout}s)",
                response_time=(time.time() - start_time) * 1000,
                timestamp=datetime.now()
            )
        except Exception as e:
            return HealthResult(
                name=health_check.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check failed: {str(e)}",
                response_time=(time.time() - start_time) * 1000,
                timestamp=datetime.now()
            )
    
    async def _update_health_state(self, name: str, result: HealthResult, health_check: HealthCheck):
        """헬스 상태 업데이트"""
        state = self.health_states[name]
        previous_status = state['current_status']
        
        # 연속 실패/성공 카운터 업데이트
        if result.status in [HealthStatus.HEALTHY, HealthStatus.WARNING]:
            state['consecutive_failures'] = 0
            state['consecutive_successes'] += 1
        else:
            state['consecutive_successes'] = 0
            state['consecutive_failures'] += 1
        
        state['last_check'] = result.timestamp
        
        # 상태 변경 감지 및 처리
        new_status = self._determine_service_status(state, health_check, result.status)
        
        if new_status != previous_status:
            state['current_status'] = new_status
            await self._handle_status_change(name, previous_status, new_status, result, health_check)
    
    def _determine_service_status(self, state: Dict, health_check: HealthCheck, check_status: HealthStatus) -> HealthStatus:
        """서비스 상태 결정"""
        # 연속 실패가 임계값을 초과하면 UNHEALTHY
        if state['consecutive_failures'] >= health_check.failure_threshold:
            return HealthStatus.UNHEALTHY
        
        # 연속 성공이 임계값을 초과하면 HEALTHY
        if state['consecutive_successes'] >= health_check.success_threshold:
            return HealthStatus.HEALTHY
        
        # 현재 체크 결과 반환
        return check_status
    
    async def _handle_status_change(self, name: str, old_status: HealthStatus, new_status: HealthStatus, 
                                  result: HealthResult, health_check: HealthCheck):
        """상태 변경 처리"""
        self.logger.info(f"Service {name} status changed: {old_status.value} -> {new_status.value}")
        
        # 알림 전송
        await self._send_health_notification(name, old_status, new_status, result)
        
        # 자동 복구 시도
        if new_status == HealthStatus.UNHEALTHY and health_check.recovery_action:
            await self._attempt_recovery(name, health_check, result)
    
    async def _send_health_notification(self, name: str, old_status: HealthStatus, 
                                      new_status: HealthStatus, result: HealthResult):
        """헬스 상태 알림 전송"""
        if new_status == HealthStatus.UNHEALTHY:
            priority = NotificationPriority.CRITICAL
            title = f"🚨 서비스 장애 감지: {name}"
        elif new_status == HealthStatus.HEALTHY and old_status == HealthStatus.UNHEALTHY:
            priority = NotificationPriority.MEDIUM
            title = f"✅ 서비스 복구됨: {name}"
        else:
            priority = NotificationPriority.LOW
            title = f"⚠️ 서비스 상태 변경: {name}"
        
        message = f"상태: {old_status.value} → {new_status.value}\n"
        message += f"메시지: {result.message}\n"
        message += f"응답시간: {result.response_time:.2f}ms\n"
        message += f"시간: {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
        
        notification = Notification(
            title=title,
            message=message,
            priority=priority,
            tags=['health_check', name],
            metadata={'service': name, 'status': new_status.value}
        )
        
        await self.notification_system.route_notification(notification)
    
    async def _attempt_recovery(self, name: str, health_check: HealthCheck, result: HealthResult):
        """자동 복구 시도"""
        state = self.health_states[name]
        
        # 최근 복구 시도 시간 체크 (너무 자주 시도하지 않도록)
        if state['last_recovery_attempt']:
            time_since_last_attempt = datetime.now() - state['last_recovery_attempt']
            if time_since_last_attempt < timedelta(minutes=5):
                self.logger.info(f"Skipping recovery for {name} - too soon since last attempt")
                return
        
        state['last_recovery_attempt'] = datetime.now()
        
        try:
            self.logger.info(f"Attempting recovery for service {name}")
            
            # 복구 액션 실행
            recovery_result = await health_check.recovery_action(name, result)
            
            # 복구 결과 알림
            if recovery_result:
                message = f"서비스 {name} 자동 복구 시도 성공"
                priority = NotificationPriority.MEDIUM
            else:
                message = f"서비스 {name} 자동 복구 시도 실패"
                priority = NotificationPriority.HIGH
            
            notification = Notification(
                title="🔧 자동 복구 시도",
                message=message,
                priority=priority,
                tags=['auto_recovery', name]
            )
            
            await self.notification_system.route_notification(notification)
            
        except Exception as e:
            self.logger.error(f"Recovery attempt failed for {name}: {e}")
            
            notification = Notification(
                title="❌ 자동 복구 실패",
                message=f"서비스 {name} 자동 복구 중 오류 발생: {str(e)}",
                priority=NotificationPriority.CRITICAL,
                tags=['auto_recovery_failed', name]
            )
            
            await self.notification_system.route_notification(notification)

# 구체적인 헬스체크 함수들
class HealthChecks:
    """헬스체크 함수 모음"""
    
    @staticmethod
    async def check_freqtrade_api(api_url: str) -> Dict[str, Any]:
        """Freqtrade API 헬스체크"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{api_url}/api/v1/ping", timeout=5) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return {
                            'status': HealthStatus.HEALTHY,
                            'message': 'API responding normally',
                            'metadata': data
                        }
                    else:
                        return {
                            'status': HealthStatus.UNHEALTHY,
                            'message': f'API returned status {resp.status}'
                        }
        except Exception as e:
            return {
                'status': HealthStatus.UNHEALTHY,
                'message': f'API connection failed: {str(e)}'
            }
    
    @staticmethod
    async def check_database_connection(db_url: str) -> Dict[str, Any]:
        """데이터베이스 연결 헬스체크"""
        try:
            import asyncpg
            conn = await asyncpg.connect(db_url)
            
            # 간단한 쿼리 실행
            result = await conn.fetchval('SELECT 1')
            await conn.close()
            
            if result == 1:
                return {
                    'status': HealthStatus.HEALTHY,
                    'message': 'Database connection OK'
                }
            else:
                return {
                    'status': HealthStatus.UNHEALTHY,
                    'message': 'Database query failed'
                }
                
        except Exception as e:
            return {
                'status': HealthStatus.UNHEALTHY,
                'message': f'Database connection failed: {str(e)}'
            }
    
    @staticmethod
    async def check_redis_connection(redis_url: str) -> Dict[str, Any]:
        """Redis 연결 헬스체크"""
        try:
            import aioredis
            redis = aioredis.from_url(redis_url)
            
            # PING 명령 실행
            pong = await redis.ping()
            await redis.close()
            
            if pong:
                return {
                    'status': HealthStatus.HEALTHY,
                    'message': 'Redis connection OK'
                }
            else:
                return {
                    'status': HealthStatus.UNHEALTHY,
                    'message': 'Redis ping failed'
                }
                
        except Exception as e:
            return {
                'status': HealthStatus.UNHEALTHY,
                'message': f'Redis connection failed: {str(e)}'
            }
    
    @staticmethod
    async def check_system_resources() -> Dict[str, Any]:
        """시스템 리소스 헬스체크"""
        try:
            # CPU 사용률
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 메모리 사용률
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # 디스크 사용률
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            
            # 임계값 체크
            warnings = []
            if cpu_percent > 80:
                warnings.append(f"High CPU usage: {cpu_percent}%")
            if memory_percent > 85:
                warnings.append(f"High memory usage: {memory_percent}%")
            if disk_percent > 90:
                warnings.append(f"High disk usage: {disk_percent}%")
            
            if warnings:
                status = HealthStatus.WARNING if len(warnings) == 1 else HealthStatus.UNHEALTHY
                message = "; ".join(warnings)
            else:
                status = HealthStatus.HEALTHY
                message = f"System resources OK (CPU: {cpu_percent}%, Memory: {memory_percent}%, Disk: {disk_percent}%)"
            
            return {
                'status': status,
                'message': message,
                'metadata': {
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory_percent,
                    'disk_percent': disk_percent
                }
            }
            
        except Exception as e:
            return {
                'status': HealthStatus.UNHEALTHY,
                'message': f'System resource check failed: {str(e)}'
            }

class RecoveryActions:
    """복구 액션 함수 모음"""
    
    def __init__(self, docker_client):
        self.docker_client = docker_client
    
    async def restart_container(self, container_name: str, result: HealthResult) -> bool:
        """컨테이너 재시작"""
        try:
            container = self.docker_client.containers.get(container_name)
            
            logging.info(f"Restarting container: {container_name}")
            container.restart(timeout=30)
            
            # 재시작 후 잠시 대기
            await asyncio.sleep(10)
            
            # 컨테이너 상태 확인
            container.reload()
            if container.status == 'running':
                logging.info(f"Container {container_name} restarted successfully")
                return True
            else:
                logging.error(f"Container {container_name} failed to start after restart")
                return False
                
        except Exception as e:
            logging.error(f"Failed to restart container {container_name}: {e}")
            return False
    
    async def restart_service(self, service_name: str, result: HealthResult) -> bool:
        """systemd 서비스 재시작"""
        try:
            import subprocess
            
            # 서비스 재시작
            subprocess.run(['systemctl', 'restart', service_name], check=True)
            
            # 재시작 후 상태 확인
            await asyncio.sleep(5)
            result = subprocess.run(['systemctl', 'is-active', service_name], 
                                 capture_output=True, text=True)
            
            if result.stdout.strip() == 'active':
                logging.info(f"Service {service_name} restarted successfully")
                return True
            else:
                logging.error(f"Service {service_name} failed to start after restart")
                return False
                
        except Exception as e:
            logging.error(f"Failed to restart service {service_name}: {e}")
            return False
    
    async def clear_cache(self, cache_type: str, result: HealthResult) -> bool:
        """캐시 정리"""
        try:
            if cache_type == 'redis':
                import aioredis
                redis = aioredis.from_url("redis://localhost:6379")
                await redis.flushdb()
                await redis.close()
                
                logging.info("Redis cache cleared successfully")
                return True
            
            return False
            
        except Exception as e:
            logging.error(f"Failed to clear {cache_type} cache: {e}")
            return False

### 🔥 **서킷 브레이커 패턴**

```python
# automation/circuit_breaker.py
from typing import Optional, Callable, Any
from enum import Enum
import asyncio
import time
from dataclasses import dataclass

class CircuitState(Enum):
    """서킷 브레이커 상태"""
    CLOSED = "closed"      # 정상 동작
    OPEN = "open"          # 차단됨
    HALF_OPEN = "half_open"  # 테스트 중

@dataclass
class CircuitBreakerConfig:
    """서킷 브레이커 설정"""
    failure_threshold: int = 5         # 실패 임계값
    recovery_timeout: int = 60         # 복구 타임아웃 (초)
    expected_exception: type = Exception
    success_threshold: int = 3         # 반열림 상태에서 성공 임계값

class CircuitBreaker:
    """서킷 브레이커 구현"""
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.listeners = []
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """서킷 브레이커를 통한 함수 호출"""
        
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
            else:
                raise CircuitOpenException("Circuit breaker is OPEN")
        
        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
            
        except self.config.expected_exception as e:
            await self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """리셋 시도 여부 확인"""
        return (
            self.last_failure_time is not None and
            time.time() - self.last_failure_time >= self.config.recovery_timeout
        )
    
    async def _on_success(self):
        """성공 시 처리"""
        self.failure_count = 0
        
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitState.CLOSED
                await self._notify_listeners('state_changed', CircuitState.CLOSED)
    
    async def _on_failure(self):
        """실패 시 처리"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.config.failure_threshold:
            if self.state != CircuitState.OPEN:
                self.state = CircuitState.OPEN
                await self._notify_listeners('state_changed', CircuitState.OPEN)
    
    def add_listener(self, listener: Callable):
        """이벤트 리스너 추가"""
        self.listeners.append(listener)
    
    async def _notify_listeners(self, event_type: str, data: Any):
        """리스너들에게 이벤트 알림"""
        for listener in self.listeners:
            try:
                await listener(event_type, data)
            except Exception as e:
                logging.error(f"Circuit breaker listener error: {e}")

class CircuitOpenException(Exception):
    """서킷 브레이커 열림 예외"""
    pass

### 🔄 **백업 시스템 자동 전환**

```python
# automation/failover_manager.py
import asyncio
import aioredis
import asyncpg
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass
import logging
import time

class ServiceRole(Enum):
    """서비스 역할"""
    PRIMARY = "primary"
    SECONDARY = "secondary"
    STANDBY = "standby"

class FailoverTrigger(Enum):
    """장애 전환 트리거"""
    HEALTH_CHECK_FAILURE = "health_check_failure"
    MANUAL_TRIGGER = "manual_trigger"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    RESOURCE_EXHAUSTION = "resource_exhaustion"

@dataclass
class ServiceEndpoint:
    """서비스 엔드포인트"""
    name: str
    host: str
    port: int
    role: ServiceRole
    priority: int = 0  # 낮을수록 높은 우선순위
    health_check_url: Optional[str] = None

class FailoverManager:
    """장애 전환 관리자"""
    
    def __init__(self, notification_system):
        self.notification_system = notification_system
        self.service_groups: Dict[str, List[ServiceEndpoint]] = {}
        self.current_primary: Dict[str, ServiceEndpoint] = {}
        self.failover_history: List[Dict] = []
        self.is_monitoring = False
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def register_service_group(self, group_name: str, endpoints: List[ServiceEndpoint]):
        """서비스 그룹 등록"""
        self.service_groups[group_name] = sorted(endpoints, key=lambda x: x.priority)
        
        # 현재 프라이머리 선택
        primary = next((ep for ep in endpoints if ep.role == ServiceRole.PRIMARY), None)
        if primary:
            self.current_primary[group_name] = primary
        else:
            # 우선순위가 가장 높은 것을 프라이머리로 설정
            self.current_primary[group_name] = endpoints[0]
            endpoints[0].role = ServiceRole.PRIMARY
    
    async def trigger_failover(self, group_name: str, trigger: FailoverTrigger, 
                             reason: str = "", target_endpoint: Optional[str] = None) -> bool:
        """장애 전환 실행"""
        if group_name not in self.service_groups:
            self.logger.error(f"Service group not found: {group_name}")
            return False
        
        current_primary = self.current_primary.get(group_name)
        if not current_primary:
            self.logger.error(f"No primary service found for group: {group_name}")
            return False
        
        # 대상 엔드포인트 선택
        candidates = [ep for ep in self.service_groups[group_name] 
                     if ep.name != current_primary.name and ep.role != ServiceRole.STANDBY]
        
        if target_endpoint:
            target = next((ep for ep in candidates if ep.name == target_endpoint), None)
            if not target:
                self.logger.error(f"Target endpoint not found: {target_endpoint}")
                return False
            new_primary = target
        else:
            # 우선순위가 가장 높은 후보 선택
            if not candidates:
                self.logger.error(f"No failover candidates for group: {group_name}")
                return False
            new_primary = min(candidates, key=lambda x: x.priority)
        
        # 새 프라이머리의 헬스체크
        if not await self._verify_endpoint_health(new_primary):
            self.logger.error(f"New primary endpoint is not healthy: {new_primary.name}")
            return False
        
        # 장애 전환 실행
        try:
            await self._execute_failover(group_name, current_primary, new_primary, trigger, reason)
            return True
            
        except Exception as e:
            self.logger.error(f"Failover execution failed: {e}")
            return False
    
    async def _execute_failover(self, group_name: str, old_primary: ServiceEndpoint, 
                              new_primary: ServiceEndpoint, trigger: FailoverTrigger, reason: str):
        """장애 전환 실행"""
        
        self.logger.info(f"Executing failover for {group_name}: {old_primary.name} -> {new_primary.name}")
        
        # 1. 트래픽 드레이닝 (진행중인 요청 완료 대기)
        await self._drain_traffic(old_primary)
        
        # 2. 역할 변경
        old_primary.role = ServiceRole.SECONDARY
        new_primary.role = ServiceRole.PRIMARY
        self.current_primary[group_name] = new_primary
        
        # 3. 설정 업데이트 (로드 밸런서, DNS 등)
        await self._update_service_configuration(group_name, new_primary)
        
        # 4. 새 프라이머리 검증
        await self._verify_failover_success(group_name, new_primary)
        
        # 5. 기록 및 알림
        failover_record = {
            'timestamp': time.time(),
            'group_name': group_name,
            'old_primary': old_primary.name,
            'new_primary': new_primary.name,
            'trigger': trigger.value,
            'reason': reason
        }
        
        self.failover_history.append(failover_record)
        
        # 알림 전송
        await self._send_failover_notification(failover_record)
        
        self.logger.info(f"Failover completed for {group_name}")
    
    async def _drain_traffic(self, endpoint: ServiceEndpoint):
        """트래픽 드레이닝"""
        # 진행중인 연결 완료 대기
        # 실제 구현에서는 로드 밸런서 API 사용
        await asyncio.sleep(5)  # 임시 대기
    
    async def _update_service_configuration(self, group_name: str, new_primary: ServiceEndpoint):
        """서비스 설정 업데이트"""
        # DNS 업데이트, 로드 밸런서 설정 등
        # 실제 구현에서는 인프라 API 사용
        pass
    
    async def _verify_endpoint_health(self, endpoint: ServiceEndpoint) -> bool:
        """엔드포인트 헬스체크"""
        if not endpoint.health_check_url:
            return True  # 헬스체크 URL이 없으면 통과
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(endpoint.health_check_url, timeout=10) as resp:
                    return resp.status == 200
        except Exception as e:
            self.logger.error(f"Health check failed for {endpoint.name}: {e}")
            return False
    
    async def _verify_failover_success(self, group_name: str, new_primary: ServiceEndpoint):
        """장애 전환 성공 검증"""
        # 새 프라이머리가 정상 동작하는지 확인
        max_attempts = 10
        for attempt in range(max_attempts):
            if await self._verify_endpoint_health(new_primary):
                self.logger.info(f"Failover verification successful for {group_name}")
                return True
            
            await asyncio.sleep(2)
        
        raise Exception(f"Failover verification failed for {group_name}")
    
    async def _send_failover_notification(self, record: Dict):
        """장애 전환 알림 전송"""
        title = f"🔄 장애 전환 완료: {record['group_name']}"
        message = f"""
서비스 그룹: {record['group_name']}
이전 프라이머리: {record['old_primary']}
새 프라이머리: {record['new_primary']}
트리거: {record['trigger']}
사유: {record['reason']}
시간: {datetime.fromtimestamp(record['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}
        """.strip()
        
        notification = Notification(
            title=title,
            message=message,
            priority=NotificationPriority.HIGH,
            tags=['failover', record['group_name']]
        )
        
        await self.notification_system.route_notification(notification)

### 🚫 **장애 전파 방지**

```python
# automation/failure_isolation.py
import asyncio
from typing import Dict, Set, List, Optional
from enum import Enum
from dataclasses import dataclass
import networkx as nx
import logging

class IsolationStrategy(Enum):
    """격리 전략"""
    CIRCUIT_BREAKER = "circuit_breaker"
    BULKHEAD = "bulkhead"
    TIMEOUT = "timeout"
    RETRY_WITH_BACKOFF = "retry_with_backoff"
    GRACEFUL_DEGRADATION = "graceful_degradation"

class DependencyType(Enum):
    """의존성 타입"""
    SYNCHRONOUS = "synchronous"
    ASYNCHRONOUS = "asynchronous"
    DATA = "data"
    CONFIGURATION = "configuration"

@dataclass
class ServiceDependency:
    """서비스 의존성"""
    source: str
    target: str
    dependency_type: DependencyType
    criticality: int  # 1-10, 10이 가장 중요
    isolation_strategies: List[IsolationStrategy]

class FailureIsolationManager:
    """장애 격리 관리자"""
    
    def __init__(self):
        self.dependency_graph = nx.DiGraph()
        self.isolation_policies: Dict[str, Dict] = {}
        self.active_isolations: Dict[str, Set[str]] = {}
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def register_dependency(self, dependency: ServiceDependency):
        """서비스 의존성 등록"""
        self.dependency_graph.add_edge(
            dependency.source, 
            dependency.target,
            **{
                'type': dependency.dependency_type,
                'criticality': dependency.criticality,
                'strategies': dependency.isolation_strategies
            }
        )
    
    def set_isolation_policy(self, service: str, policy: Dict):
        """격리 정책 설정"""
        self.isolation_policies[service] = policy
    
    async def handle_service_failure(self, failed_service: str, failure_details: Dict):
        """서비스 장애 처리"""
        self.logger.info(f"Handling failure for service: {failed_service}")
        
        # 1. 직접 의존하는 서비스들 식별
        dependent_services = list(self.dependency_graph.predecessors(failed_service))
        
        # 2. 장애 전파 위험 평가
        propagation_risk = await self._assess_propagation_risk(failed_service, failure_details)
        
        # 3. 격리 전략 적용
        isolation_actions = await self._apply_isolation_strategies(
            failed_service, dependent_services, propagation_risk
        )
        
        # 4. 복구 모니터링 시작
        asyncio.create_task(self._monitor_recovery(failed_service, isolation_actions))
        
        return isolation_actions
    
    async def _assess_propagation_risk(self, failed_service: str, failure_details: Dict) -> int:
        """장애 전파 위험 평가"""
        risk_score = 0
        
        # 실패한 서비스의 중요도
        service_criticality = failure_details.get('criticality', 5)
        risk_score += service_criticality
        
        # 의존 서비스 수
        dependent_count = len(list(self.dependency_graph.predecessors(failed_service)))
        risk_score += min(dependent_count * 2, 20)
        
        # 실패 유형별 위험도
        failure_type = failure_details.get('type', 'unknown')
        if failure_type in ['resource_exhaustion', 'cascade_failure']:
            risk_score += 10
        elif failure_type in ['timeout', 'connection_error']:
            risk_score += 5
        
        return min(risk_score, 100)  # 최대 100점
    
    async def _apply_isolation_strategies(self, failed_service: str, 
                                        dependent_services: List[str], 
                                        risk_score: int) -> List[Dict]:
        """격리 전략 적용"""
        actions = []
        
        for dependent in dependent_services:
            edge_data = self.dependency_graph.get_edge_data(dependent, failed_service)
            strategies = edge_data.get('strategies', [])
            
            for strategy in strategies:
                action = await self._apply_strategy(
                    strategy, dependent, failed_service, risk_score
                )
                if action:
                    actions.append(action)
        
        return actions
    
    async def _apply_strategy(self, strategy: IsolationStrategy, 
                            dependent: str, failed_service: str, risk_score: int) -> Optional[Dict]:
        """개별 격리 전략 적용"""
        
        if strategy == IsolationStrategy.CIRCUIT_BREAKER:
            return await self._apply_circuit_breaker(dependent, failed_service)
        
        elif strategy == IsolationStrategy.BULKHEAD:
            return await self._apply_bulkhead_isolation(dependent, failed_service)
        
        elif strategy == IsolationStrategy.GRACEFUL_DEGRADATION:
            return await self._apply_graceful_degradation(dependent, failed_service, risk_score)
        
        elif strategy == IsolationStrategy.TIMEOUT:
            return await self._apply_timeout_reduction(dependent, failed_service)
        
        return None
    
    async def _apply_circuit_breaker(self, dependent: str, failed_service: str) -> Dict:
        """서킷 브레이커 적용"""
        circuit_key = f"{dependent}->{failed_service}"
        
        if circuit_key not in self.circuit_breakers:
            config = CircuitBreakerConfig(
                failure_threshold=3,
                recovery_timeout=30,
                success_threshold=2
            )
            self.circuit_breakers[circuit_key] = CircuitBreaker(config)
        
        # 서킷 브레이커 강제 개방
        self.circuit_breakers[circuit_key].state = CircuitState.OPEN
        self.circuit_breakers[circuit_key].last_failure_time = time.time()
        
        self.logger.info(f"Circuit breaker opened: {circuit_key}")
        
        return {
            'strategy': 'circuit_breaker',
            'dependent': dependent,
            'target': failed_service,
            'status': 'applied'
        }
    
    async def _apply_bulkhead_isolation(self, dependent: str, failed_service: str) -> Dict:
        """벌크헤드 격리 적용"""
        # 실패한 서비스와의 연결을 별도 스레드 풀로 격리
        if dependent not in self.active_isolations:
            self.active_isolations[dependent] = set()
        
        self.active_isolations[dependent].add(failed_service)
        
        self.logger.info(f"Bulkhead isolation applied: {dependent} -> {failed_service}")
        
        return {
            'strategy': 'bulkhead',
            'dependent': dependent,
            'target': failed_service,
            'status': 'applied'
        }
    
    async def _apply_graceful_degradation(self, dependent: str, failed_service: str, risk_score: int) -> Dict:
        """우아한 성능 저하 적용"""
        # 위험도에 따른 성능 저하 수준 결정
        if risk_score > 70:
            degradation_level = 'high'  # 기능 대폭 제한
        elif risk_score > 40:
            degradation_level = 'medium'  # 일부 기능 제한
        else:
            degradation_level = 'low'  # 최소한의 제한
        
        # 성능 저하 정책 적용 (실제 구현에서는 서비스별 로직)
        policy = self.isolation_policies.get(dependent, {})
        degradation_config = policy.get('graceful_degradation', {})
        
        self.logger.info(f"Graceful degradation applied: {dependent}, level: {degradation_level}")
        
        return {
            'strategy': 'graceful_degradation',
            'dependent': dependent,
            'target': failed_service,
            'level': degradation_level,
            'status': 'applied'
        }
    
    async def _apply_timeout_reduction(self, dependent: str, failed_service: str) -> Dict:
        """타임아웃 단축 적용"""
        # 기존 타임아웃의 50%로 단축
        original_timeout = 30  # 기본값
        reduced_timeout = max(original_timeout * 0.5, 5)  # 최소 5초
        
        self.logger.info(f"Timeout reduced: {dependent} -> {failed_service}, {original_timeout}s -> {reduced_timeout}s")
        
        return {
            'strategy': 'timeout_reduction',
            'dependent': dependent,
            'target': failed_service,
            'original_timeout': original_timeout,
            'reduced_timeout': reduced_timeout,
            'status': 'applied'
        }
    
    async def _monitor_recovery(self, failed_service: str, isolation_actions: List[Dict]):
        """복구 모니터링"""
        recovery_attempts = 0
        max_recovery_attempts = 10
        
        while recovery_attempts < max_recovery_attempts:
            await asyncio.sleep(30)  # 30초마다 체크
            
            # 서비스 복구 상태 확인
            if await self._check_service_recovery(failed_service):
                self.logger.info(f"Service recovery detected: {failed_service}")
                
                # 격리 해제
                await self._remove_isolations(failed_service, isolation_actions)
                break
            
            recovery_attempts += 1
        
        if recovery_attempts >= max_recovery_attempts:
            self.logger.warning(f"Service recovery timeout: {failed_service}")
    
    async def _check_service_recovery(self, service: str) -> bool:
        """서비스 복구 상태 확인"""
        # 실제 구현에서는 헬스체크 수행
        return False  # 임시로 False 반환
    
    async def _remove_isolations(self, recovered_service: str, isolation_actions: List[Dict]):
        """격리 해제"""
        for action in isolation_actions:
            strategy = action['strategy']
            
            if strategy == 'circuit_breaker':
                circuit_key = f"{action['dependent']}->{recovered_service}"
                if circuit_key in self.circuit_breakers:
                    self.circuit_breakers[circuit_key].state = CircuitState.HALF_OPEN
            
            elif strategy == 'bulkhead':
                dependent = action['dependent']
                if dependent in self.active_isolations:
                    self.active_isolations[dependent].discard(recovered_service)
            
            self.logger.info(f"Isolation removed: {strategy} for {recovered_service}")

---

## ⚡ **성과 최적화 자동화**

### 🧠 **ML 기반 하이퍼파라미터 튜닝**

```python
# automation/hyperparameter_optimization.py
import optuna
import asyncio
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
import logging
import json
from dataclasses import dataclass
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
import joblib

@dataclass
class OptimizationTarget:
    """최적화 목표"""
    name: str
    metric: str  # 'sharpe_ratio', 'total_return', 'max_drawdown', etc.
    direction: str  # 'maximize' or 'minimize'
    weight: float = 1.0

@dataclass
class ParameterSpace:
    """파라미터 공간 정의"""
    name: str
    param_type: str  # 'int', 'float', 'categorical'
    low: Optional[float] = None
    high: Optional[float] = None
    choices: Optional[List] = None
    step: Optional[float] = None

class HyperparameterOptimizer:
    """하이퍼파라미터 최적화 시스템"""
    
    def __init__(self, freqtrade_manager, notification_system):
        self.freqtrade_manager = freqtrade_manager
        self.notification_system = notification_system
        self.optimization_history = []
        self.current_studies = {}
        self.surrogate_models = {}
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    async def optimize_strategy(self, strategy_name: str, parameter_spaces: List[ParameterSpace],
                              optimization_targets: List[OptimizationTarget],
                              n_trials: int = 100, timeout_hours: int = 24) -> Dict[str, Any]:
        """전략 하이퍼파라미터 최적화"""
        
        study_name = f"{strategy_name}_optimization_{int(datetime.now().timestamp())}"
        
        # Optuna 스터디 생성
        study = optuna.create_study(
            study_name=study_name,
            directions=['maximize' if target.direction == 'maximize' else 'minimize' 
                       for target in optimization_targets],
            sampler=optuna.samplers.TPESampler(),
            pruner=optuna.pruners.MedianPruner()
        )
        
        self.current_studies[study_name] = study
        
        # 목적 함수 정의
        async def objective(trial):
            return await self._evaluate_trial(trial, strategy_name, parameter_spaces, optimization_targets)
        
        try:
            # 최적화 실행
            await self._run_optimization(study, objective, n_trials, timeout_hours)
            
            # 결과 분석 및 저장
            results = await self._analyze_optimization_results(study, strategy_name, optimization_targets)
            
            # 최적 파라미터 적용
            await self._apply_best_parameters(strategy_name, results['best_params'])
            
            # 결과 알림
            await self._send_optimization_notification(strategy_name, results)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Optimization failed for {strategy_name}: {e}")
            raise e
        finally:
            if study_name in self.current_studies:
                del self.current_studies[study_name]
    
    async def _evaluate_trial(self, trial, strategy_name: str, parameter_spaces: List[ParameterSpace],
                             optimization_targets: List[OptimizationTarget]) -> List[float]:
        """시행 평가"""
        
        # 파라미터 샘플링
        params = {}
        for param_space in parameter_spaces:
            if param_space.param_type == 'int':
                params[param_space.name] = trial.suggest_int(
                    param_space.name, param_space.low, param_space.high, step=param_space.step
                )
            elif param_space.param_type == 'float':
                params[param_space.name] = trial.suggest_float(
                    param_space.name, param_space.low, param_space.high, step=param_space.step
                )
            elif param_space.param_type == 'categorical':
                params[param_space.name] = trial.suggest_categorical(
                    param_space.name, param_space.choices
                )
        
        # 백테스팅 실행
        backtest_results = await self._run_backtest_with_params(strategy_name, params)
        
        # 목표 메트릭 계산
        objective_values = []
        for target in optimization_targets:
            value = backtest_results.get(target.metric, 0)
            
            # 가중치 적용
            weighted_value = value * target.weight
            objective_values.append(weighted_value)
            
            # 중간 결과 보고 (조기 종료를 위한)
            trial.report(weighted_value, step=trial.number)
            
            # 조기 종료 체크
            if trial.should_prune():
                raise optuna.TrialPruned()
        
        return objective_values
    
    async def _run_backtest_with_params(self, strategy_name: str, params: Dict[str, Any]) -> Dict[str, float]:
        """파라미터를 적용한 백테스팅 실행"""
        
        # 임시 설정 파일 생성
        config = await self._create_temp_config(strategy_name, params)
        
        # 백테스팅 실행
        backtest_command = [
            'freqtrade', 'backtesting',
            '--config', config['config_path'],
            '--strategy', strategy_name,
            '--timerange', '20241001-20241201',  # 최근 2개월
            '--breakdown', 'day'
        ]
        
        result = await self.freqtrade_manager.run_command(backtest_command)
        
        # 결과 파싱
        return await self._parse_backtest_results(result)
    
    async def _create_temp_config(self, strategy_name: str, params: Dict[str, Any]) -> Dict[str, str]:
        """임시 설정 파일 생성"""
        
        base_config = await self.freqtrade_manager.get_base_config()
        
        # 파라미터 적용
        strategy_config = base_config.get('strategy_parameters', {})
        strategy_config.update(params)
        base_config['strategy_parameters'] = strategy_config
        
        # 임시 파일로 저장
        temp_config_path = f"/tmp/config_{strategy_name}_{int(time.time())}.json"
        with open(temp_config_path, 'w') as f:
            json.dump(base_config, f, indent=2)
        
        return {'config_path': temp_config_path}
    
    async def _parse_backtest_results(self, backtest_output: str) -> Dict[str, float]:
        """백테스팅 결과 파싱"""
        # 실제 구현에서는 Freqtrade 결과 JSON 파싱
        # 여기서는 예시 데이터 반환
        
        return {
            'total_return': np.random.uniform(0.05, 0.25),
            'sharpe_ratio': np.random.uniform(0.5, 2.5),
            'max_drawdown': np.random.uniform(0.05, 0.2),
            'win_rate': np.random.uniform(0.4, 0.7),
            'profit_factor': np.random.uniform(1.1, 2.0),
            'calmar_ratio': np.random.uniform(0.5, 1.5)
        }
    
    async def _run_optimization(self, study, objective_func: Callable, 
                               n_trials: int, timeout_hours: int):
        """최적화 실행"""
        
        start_time = time.time()
        timeout_seconds = timeout_hours * 3600
        
        for trial_num in range(n_trials):
            # 타임아웃 체크
            if time.time() - start_time > timeout_seconds:
                self.logger.info(f"Optimization timeout reached after {timeout_hours} hours")
                break
            
            try:
                # 비동기 목적 함수 실행을 위한 래퍼
                def sync_objective(trial):
                    return asyncio.run(objective_func(trial))
                
                study.optimize(sync_objective, n_trials=1, timeout=3600)  # 시행당 1시간 제한
                
                # 진행 상황 로깅
                if trial_num % 10 == 0:
                    self.logger.info(f"Optimization progress: {trial_num}/{n_trials} trials completed")
                
            except Exception as e:
                self.logger.error(f"Trial {trial_num} failed: {e}")
                continue
    
    async def _analyze_optimization_results(self, study, strategy_name: str, 
                                          optimization_targets: List[OptimizationTarget]) -> Dict[str, Any]:
        """최적화 결과 분석"""
        
        # 최적 시행 선택 (다목적 최적화의 경우 파레토 프론트)
        if len(optimization_targets) == 1:
            best_trial = study.best_trial
            best_params = best_trial.params
            best_values = {optimization_targets[0].metric: best_trial.value}
        else:
            # 다목적 최적화 - 파레토 최적해 중 하나 선택
            pareto_trials = study.best_trials
            if pareto_trials:
                # 가중 합계가 가장 높은 시행 선택
                best_trial = max(pareto_trials, 
                               key=lambda t: sum(v * target.weight for v, target 
                                                in zip(t.values, optimization_targets)))
                best_params = best_trial.params
                best_values = {target.metric: value for target, value 
                             in zip(optimization_targets, best_trial.values)}
            else:
                best_params = {}
                best_values = {}
        
        # 파라미터 중요도 분석
        param_importance = {}
        for target in optimization_targets:
            importance = optuna.importance.get_param_importances(study)
            param_importance[target.metric] = importance
        
        # 최적화 히스토리
        optimization_record = {
            'strategy_name': strategy_name,
            'timestamp': datetime.now().isoformat(),
            'n_trials': len(study.trials),
            'best_params': best_params,
            'best_values': best_values,
            'param_importance': param_importance,
            'optimization_targets': [target.__dict__ for target in optimization_targets]
        }
        
        self.optimization_history.append(optimization_record)
        
        return {
            'best_params': best_params,
            'best_values': best_values,
            'param_importance': param_importance,
            'n_trials': len(study.trials),
            'study': study
        }
    
    async def _apply_best_parameters(self, strategy_name: str, best_params: Dict[str, Any]):
        """최적 파라미터 적용"""
        
        # 프로덕션 설정에 파라미터 적용
        await self.freqtrade_manager.update_strategy_parameters(strategy_name, best_params)
        
        # 전략 재시작
        await self.freqtrade_manager.restart_strategy(strategy_name)
        
        self.logger.info(f"Applied optimized parameters to {strategy_name}: {best_params}")
    
    async def _send_optimization_notification(self, strategy_name: str, results: Dict[str, Any]):
        """최적화 완료 알림"""
        
        title = f"🎯 하이퍼파라미터 최적화 완료: {strategy_name}"
        
        message = f"""
최적화 완료 결과:
- 시행 횟수: {results['n_trials']}
- 최적 파라미터: {json.dumps(results['best_params'], indent=2)}
- 최적 성능: {json.dumps(results['best_values'], indent=2)}
        """.strip()
        
        notification = Notification(
            title=title,
            message=message,
            priority=NotificationPriority.MEDIUM,
            tags=['optimization', strategy_name]
        )
        
        await self.notification_system.route_notification(notification)

class AutoML_StrategySelector:
    """자동 기계학습 기반 전략 선택기"""
    
    def __init__(self, market_data_provider, performance_analyzer):
        self.market_data_provider = market_data_provider
        self.performance_analyzer = performance_analyzer
        self.feature_extractors = {}
        self.selection_models = {}
        self.strategy_performance_history = {}
        
    async def train_selection_model(self, historical_data_months: int = 12):
        """전략 선택 모델 훈련"""
        
        # 1. 과거 데이터 수집
        end_date = datetime.now()
        start_date = end_date - timedelta(days=historical_data_months * 30)
        
        market_data = await self.market_data_provider.get_historical_data(
            start_date, end_date, ['BTCUSDT', 'ETHUSDT', 'ADAUSDT']
        )
        
        # 2. 특징 추출
        features = await self._extract_market_features(market_data)
        
        # 3. 전략별 성과 레이블 생성
        strategy_labels = await self._generate_strategy_labels(market_data)
        
        # 4. 모델 훈련
        for strategy_name, labels in strategy_labels.items():
            model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
            
            model.fit(features, labels)
            self.selection_models[strategy_name] = model
            
            # 모델 저장
            joblib.dump(model, f'models/strategy_selector_{strategy_name}.pkl')
        
        self.logger.info("Strategy selection models trained successfully")
    
    async def _extract_market_features(self, market_data: pd.DataFrame) -> np.ndarray:
        """시장 특징 추출"""
        
        features = []
        
        for symbol in ['BTCUSDT', 'ETHUSDT', 'ADAUSDT']:
            symbol_data = market_data[market_data['symbol'] == symbol]
            
            if len(symbol_data) == 0:
                continue
            
            # 기술적 지표
            prices = symbol_data['close'].values
            
            # 이동평균
            ma_20 = pd.Series(prices).rolling(20).mean().iloc[-1]
            ma_50 = pd.Series(prices).rolling(50).mean().iloc[-1]
            
            # RSI
            delta = pd.Series(prices).diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs)).iloc[-1]
            
            # 변동성
            volatility = pd.Series(prices).pct_change().rolling(20).std().iloc[-1]
            
            # 거래량 특징
            volume_ma = symbol_data['volume'].rolling(20).mean().iloc[-1]
            volume_ratio = symbol_data['volume'].iloc[-1] / volume_ma
            
            features.extend([ma_20, ma_50, rsi, volatility, volume_ratio])
        
        # 거시경제 특징 (추가 가능)
        # 예: VIX, DXY, 금리 등
        
        return np.array(features).reshape(1, -1)
    
    async def _generate_strategy_labels(self, market_data: pd.DataFrame) -> Dict[str, np.ndarray]:
        """전략별 성과 레이블 생성"""
        
        strategy_labels = {}
        
        # 각 전략의 과거 성과 데이터 수집
        for strategy_name in ['FuturesAIRiskStrategy', 'RossCameronFuturesStrategy']:
            performance_data = await self.performance_analyzer.get_strategy_performance(
                strategy_name, market_data.index
            )
            
            # 성과 지표를 레이블로 사용 (예: 일일 수익률)
            daily_returns = performance_data.get('daily_returns', [])
            strategy_labels[strategy_name] = np.array(daily_returns)
        
        return strategy_labels
    
    async def select_optimal_strategy(self, current_market_conditions: Dict[str, Any]) -> str:
        """현재 시장 상황에 최적인 전략 선택"""
        
        # 현재 시장 특징 추출
        current_features = await self._extract_current_market_features(current_market_conditions)
        
        # 각 전략의 예상 성과 예측
        strategy_predictions = {}
        
        for strategy_name, model in self.selection_models.items():
            predicted_performance = model.predict(current_features.reshape(1, -1))[0]
            strategy_predictions[strategy_name] = predicted_performance
        
        # 최고 성과 예상 전략 선택
        optimal_strategy = max(strategy_predictions, key=strategy_predictions.get)
        
        self.logger.info(f"Optimal strategy selected: {optimal_strategy}")
        self.logger.info(f"Strategy predictions: {strategy_predictions}")
        
        return optimal_strategy
    
    async def _extract_current_market_features(self, market_conditions: Dict[str, Any]) -> np.ndarray:
        """현재 시장 특징 추출"""
        # 실시간 시장 데이터를 사용한 특징 추출
        # _extract_market_features와 유사하지만 실시간 데이터 사용
        pass

### 🧪 **A/B 테스트 프레임워크**

```python
# automation/ab_testing.py
import asyncio
import random
import numpy as np
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from scipy import stats
import pandas as pd

class TestStatus(Enum):
    """테스트 상태"""
    PLANNING = "planning"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class SignificanceMethod(Enum):
    """유의성 검정 방법"""
    T_TEST = "t_test"
    MANN_WHITNEY = "mann_whitney"
    CHI_SQUARE = "chi_square"
    BAYESIAN = "bayesian"

@dataclass
class TestVariant:
    """테스트 변형"""
    name: str
    allocation_percent: float
    strategy_name: str
    parameters: Dict[str, Any]
    description: str = ""

@dataclass
class TestMetric:
    """테스트 메트릭"""
    name: str
    metric_type: str  # 'ratio', 'mean', 'count'
    primary: bool = False
    direction: str = "increase"  # "increase" or "decrease"
    min_detectable_effect: float = 0.05  # 최소 감지 가능한 효과 크기

@dataclass
class ABTestConfig:
    """A/B 테스트 설정"""
    test_id: str
    name: str
    description: str
    variants: List[TestVariant]
    metrics: List[TestMetric]
    duration_days: int
    confidence_level: float = 0.95
    power: float = 0.8
    significance_method: SignificanceMethod = SignificanceMethod.T_TEST
    early_stopping: bool = True
    minimum_sample_size: int = 100

class ABTestManager:
    """A/B 테스트 관리자"""
    
    def __init__(self, strategy_manager, performance_analyzer, notification_system):
        self.strategy_manager = strategy_manager
        self.performance_analyzer = performance_analyzer
        self.notification_system = notification_system
        self.active_tests: Dict[str, ABTestConfig] = {}
        self.test_data: Dict[str, Dict] = {}
        self.allocation_cache: Dict[str, str] = {}  # 사용자 -> 변형 매핑
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    async def create_test(self, config: ABTestConfig) -> bool:
        """A/B 테스트 생성"""
        
        # 설정 검증
        if not await self._validate_test_config(config):
            return False
        
        # 표본 크기 계산
        required_sample_size = await self._calculate_sample_size(config)
        if required_sample_size > config.minimum_sample_size * 10:
            self.logger.warning(f"Required sample size is very large: {required_sample_size}")
        
        # 테스트 데이터 초기화
        self.test_data[config.test_id] = {
            'start_time': datetime.now(),
            'status': TestStatus.PLANNING,
            'variant_data': {variant.name: {'metrics': {}, 'samples': 0} 
                           for variant in config.variants},
            'required_sample_size': required_sample_size
        }
        
        self.active_tests[config.test_id] = config
        
        self.logger.info(f"A/B test created: {config.test_id}")
        return True
    
    async def start_test(self, test_id: str) -> bool:
        """A/B 테스트 시작"""
        
        if test_id not in self.active_tests:
            self.logger.error(f"Test not found: {test_id}")
            return False
        
        config = self.active_tests[test_id]
        test_data = self.test_data[test_id]
        
        # 전략 변형들 배포
        for variant in config.variants:
            success = await self.strategy_manager.deploy_strategy_variant(
                variant.strategy_name, variant.parameters, f"{test_id}_{variant.name}"
            )
            if not success:
                self.logger.error(f"Failed to deploy variant: {variant.name}")
                return False
        
        # 테스트 상태 업데이트
        test_data['status'] = TestStatus.RUNNING
        test_data['actual_start_time'] = datetime.now()
        
        # 모니터링 태스크 시작
        asyncio.create_task(self._monitor_test(test_id))
        
        # 시작 알림
        await self._send_test_notification(test_id, "started")
        
        self.logger.info(f"A/B test started: {test_id}")
        return True
    
    async def allocate_user_to_variant(self, test_id: str, user_id: str) -> Optional[str]:
        """사용자를 테스트 변형에 할당"""
        
        if test_id not in self.active_tests:
            return None
        
        # 캐시된 할당 확인
        cache_key = f"{test_id}_{user_id}"
        if cache_key in self.allocation_cache:
            return self.allocation_cache[cache_key]
        
        config = self.active_tests[test_id]
        test_data = self.test_data[test_id]
        
        if test_data['status'] != TestStatus.RUNNING:
            return None
        
        # 해시 기반 일관된 할당
        hash_value = hash(f"{test_id}_{user_id}") % 100
        
        cumulative_percent = 0
        for variant in config.variants:
            cumulative_percent += variant.allocation_percent
            if hash_value < cumulative_percent:
                self.allocation_cache[cache_key] = variant.name
                return variant.name
        
        # 기본값 (마지막 변형)
        default_variant = config.variants[-1].name
        self.allocation_cache[cache_key] = default_variant
        return default_variant
    
    async def record_metric(self, test_id: str, user_id: str, metric_name: str, value: float):
        """메트릭 기록"""
        
        if test_id not in self.active_tests:
            return
        
        variant = await self.allocate_user_to_variant(test_id, user_id)
        if not variant:
            return
        
        test_data = self.test_data[test_id]
        variant_data = test_data['variant_data'][variant]
        
        # 메트릭 데이터 저장
        if metric_name not in variant_data['metrics']:
            variant_data['metrics'][metric_name] = []
        
        variant_data['metrics'][metric_name].append({
            'value': value,
            'timestamp': datetime.now(),
            'user_id': user_id
        })
        
        variant_data['samples'] += 1
    
    async def _monitor_test(self, test_id: str):
        """테스트 모니터링 루프"""
        
        config = self.active_tests[test_id]
        test_data = self.test_data[test_id]
        
        end_time = test_data['actual_start_time'] + timedelta(days=config.duration_days)
        
        while test_data['status'] == TestStatus.RUNNING and datetime.now() < end_time:
            
            # 통계적 유의성 검정
            if config.early_stopping:
                significance_result = await self._check_statistical_significance(test_id)
                
                if significance_result['significant']:
                    await self._stop_test(test_id, "statistical_significance")
                    break
            
            # 표본 크기 체크
            await self._check_sample_size_adequacy(test_id)
            
            # 1시간마다 체크
            await asyncio.sleep(3600)
        
        # 테스트 종료 시간 도달
        if test_data['status'] == TestStatus.RUNNING:
            await self._stop_test(test_id, "duration_completed")
    
    async def _check_statistical_significance(self, test_id: str) -> Dict[str, Any]:
        """통계적 유의성 검정"""
        
        config = self.active_tests[test_id]
        test_data = self.test_data[test_id]
        
        results = {
            'significant': False,
            'winning_variant': None,
            'p_value': 1.0,
            'effect_size': 0.0,
            'confidence_interval': None
        }
        
        # 주요 메트릭에 대해 검정 수행
        primary_metrics = [m for m in config.metrics if m.primary]
        
        for metric in primary_metrics:
            # 각 변형의 데이터 수집
            variant_data = {}
            for variant in config.variants:
                metrics_data = test_data['variant_data'][variant.name]['metrics']
                if metric.name in metrics_data:
                    values = [d['value'] for d in metrics_data[metric.name]]
                    variant_data[variant.name] = values
            
            if len(variant_data) < 2:
                continue
            
            # 변형들 간 비교 (첫 번째를 컨트롤로 가정)
            variants = list(variant_data.keys())
            control_data = variant_data[variants[0]]
            
            for i in range(1, len(variants)):
                treatment_data = variant_data[variants[i]]
                
                if len(control_data) < 30 or len(treatment_data) < 30:
                    continue  # 표본 크기 부족
                
                # 통계적 검정 수행
                if config.significance_method == SignificanceMethod.T_TEST:
                    statistic, p_value = stats.ttest_ind(control_data, treatment_data)
                elif config.significance_method == SignificanceMethod.MANN_WHITNEY:
                    statistic, p_value = stats.mannwhitneyu(control_data, treatment_data)
                
                # 효과 크기 계산 (Cohen's d)
                pooled_std = np.sqrt(((len(control_data) - 1) * np.var(control_data) + 
                                    (len(treatment_data) - 1) * np.var(treatment_data)) / 
                                   (len(control_data) + len(treatment_data) - 2))
                
                effect_size = (np.mean(treatment_data) - np.mean(control_data)) / pooled_std
                
                # 유의성 판정
                alpha = 1 - config.confidence_level
                if p_value < alpha and abs(effect_size) >= metric.min_detectable_effect:
                    results['significant'] = True
                    results['winning_variant'] = variants[i] if effect_size > 0 else variants[0]
                    results['p_value'] = p_value
                    results['effect_size'] = effect_size
                    
                    # 신뢰구간 계산
                    se = pooled_std * np.sqrt(1/len(control_data) + 1/len(treatment_data))
                    margin_of_error = stats.t.ppf(1 - alpha/2, len(control_data) + len(treatment_data) - 2) * se
                    
                    mean_diff = np.mean(treatment_data) - np.mean(control_data)
                    results['confidence_interval'] = (
                        mean_diff - margin_of_error,
                        mean_diff + margin_of_error
                    )
                    
                    break
            
            if results['significant']:
                break
        
        return results
    
    async def _stop_test(self, test_id: str, reason: str):
        """테스트 중지"""
        
        config = self.active_tests[test_id]
        test_data = self.test_data[test_id]
        
        test_data['status'] = TestStatus.COMPLETED
        test_data['end_time'] = datetime.now()
        test_data['stop_reason'] = reason
        
        # 최종 결과 분석
        final_results = await self._analyze_final_results(test_id)
        test_data['final_results'] = final_results
        
        # 승리 변형 배포 (통계적으로 유의한 경우)
        if final_results['significant']:
            await self._deploy_winning_variant(test_id, final_results['winning_variant'])
        
        # 테스트 변형들 정리
        await self._cleanup_test_variants(test_id)
        
        # 완료 알림
        await self._send_test_notification(test_id, "completed", final_results)
        
        self.logger.info(f"A/B test completed: {test_id}, reason: {reason}")
    
    async def _analyze_final_results(self, test_id: str) -> Dict[str, Any]:
        """최종 결과 분석"""
        
        # 통계적 유의성 재확인
        significance_result = await self._check_statistical_significance(test_id)
        
        # 비즈니스 메트릭 계산
        config = self.active_tests[test_id]
        test_data = self.test_data[test_id]
        
        variant_summaries = {}
        
        for variant in config.variants:
            variant_data = test_data['variant_data'][variant.name]
            summary = {
                'sample_size': variant_data['samples'],
                'metrics': {}
            }
            
            for metric in config.metrics:
                if metric.name in variant_data['metrics']:
                    values = [d['value'] for d in variant_data['metrics'][metric.name]]
                    summary['metrics'][metric.name] = {
                        'mean': np.mean(values),
                        'std': np.std(values),
                        'count': len(values),
                        'confidence_interval': self._calculate_confidence_interval(values, config.confidence_level)
                    }
            
            variant_summaries[variant.name] = summary
        
        return {
            **significance_result,
            'variant_summaries': variant_summaries,
            'test_duration_hours': (test_data['end_time'] - test_data['actual_start_time']).total_seconds() / 3600
        }
    
    def _calculate_confidence_interval(self, values: List[float], confidence_level: float) -> tuple:
        """신뢰구간 계산"""
        if len(values) < 2:
            return (0, 0)
        
        alpha = 1 - confidence_level
        mean = np.mean(values)
        se = stats.sem(values)
        margin_of_error = stats.t.ppf(1 - alpha/2, len(values) - 1) * se
        
        return (mean - margin_of_error, mean + margin_of_error)
    
    async def _deploy_winning_variant(self, test_id: str, winning_variant: str):
        """승리 변형 배포"""
        
        config = self.active_tests[test_id]
        
        # 승리 변형 찾기
        winner = next((v for v in config.variants if v.name == winning_variant), None)
        if not winner:
            return
        
        # 프로덕션에 배포
        await self.strategy_manager.deploy_strategy_to_production(
            winner.strategy_name, winner.parameters
        )
        
        self.logger.info(f"Deployed winning variant: {winning_variant} for test {test_id}")
    
    async def _cleanup_test_variants(self, test_id: str):
        """테스트 변형들 정리"""
        
        config = self.active_tests[test_id]
        
        for variant in config.variants:
            variant_id = f"{test_id}_{variant.name}"
            await self.strategy_manager.remove_strategy_variant(variant_id)
        
        # 할당 캐시 정리
        cache_keys_to_remove = [k for k in self.allocation_cache.keys() if k.startswith(f"{test_id}_")]
        for key in cache_keys_to_remove:
            del self.allocation_cache[key]
    
    async def _send_test_notification(self, test_id: str, event_type: str, results: Dict = None):
        """테스트 이벤트 알림"""
        
        config = self.active_tests[test_id]
        
        if event_type == "started":
            title = f"🧪 A/B 테스트 시작: {config.name}"
            message = f"테스트 ID: {test_id}\n기간: {config.duration_days}일\n변형 수: {len(config.variants)}"
            priority = NotificationPriority.LOW
            
        elif event_type == "completed":
            title = f"✅ A/B 테스트 완료: {config.name}"
            
            if results and results.get('significant'):
                message = f"""
테스트 ID: {test_id}
결과: 통계적으로 유의함 (p={results['p_value']:.4f})
승리 변형: {results['winning_variant']}
효과 크기: {results['effect_size']:.4f}
                """.strip()
                priority = NotificationPriority.MEDIUM
            else:
                message = f"""
테스트 ID: {test_id}
결과: 통계적으로 유의하지 않음
결론: 변형들 간 의미있는 차이 없음
                """.strip()
                priority = NotificationPriority.LOW
        
        notification = Notification(
            title=title,
            message=message,
            priority=priority,
            tags=['ab_test', test_id]
        )
        
        await self.notification_system.route_notification(notification)

---

## 🔐 **보안 및 컴플라이언스**

### 🔐 **API 키 관리 (HashiCorp Vault)**

```python
# automation/secrets_management.py
import hvac
import asyncio
import aiohttp
from typing import Dict, Optional, Any
import logging
import time
from datetime import datetime, timedelta
import json
import os

class VaultSecretManager:
    """HashiCorp Vault 기반 비밀 관리"""
    
    def __init__(self, vault_url: str, vault_token: str = None):
        self.vault_url = vault_url
        self.client = hvac.Client(url=vault_url, token=vault_token)
        self.secret_cache = {}
        self.cache_ttl = 300  # 5분
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    async def authenticate_with_kubernetes(self, role: str, jwt_path: str = "/var/run/secrets/kubernetes.io/serviceaccount/token"):
        """Kubernetes 서비스 어카운트를 통한 인증"""
        try:
            with open(jwt_path, 'r') as f:
                jwt_token = f.read()
            
            auth_response = self.client.auth.kubernetes.login(
                role=role,
                jwt=jwt_token
            )
            
            self.client.token = auth_response['auth']['client_token']
            self.logger.info("Successfully authenticated with Vault using Kubernetes")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Kubernetes authentication failed: {e}")
            return False
    
    async def get_secret(self, path: str, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """비밀 정보 조회"""
        
        cache_key = f"secret_{path}"
        
        # 캐시 확인 (강제 새로고침이 아닌 경우)
        if not force_refresh and cache_key in self.secret_cache:
            cached_data = self.secret_cache[cache_key]
            if time.time() - cached_data['timestamp'] < self.cache_ttl:
                return cached_data['data']
        
        try:
            # Vault에서 비밀 정보 조회
            response = self.client.secrets.kv.v2.read_secret_version(path=path)
            secret_data = response['data']['data']
            
            # 캐시에 저장
            self.secret_cache[cache_key] = {
                'data': secret_data,
                'timestamp': time.time()
            }
            
            self.logger.info(f"Retrieved secret from path: {path}")
            return secret_data
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve secret from {path}: {e}")
            return None
    
    async def store_secret(self, path: str, secret_data: Dict[str, Any]) -> bool:
        """비밀 정보 저장"""
        try:
            self.client.secrets.kv.v2.create_or_update_secret(
                path=path,
                secret=secret_data
            )
            
            # 캐시 업데이트
            cache_key = f"secret_{path}"
            self.secret_cache[cache_key] = {
                'data': secret_data,
                'timestamp': time.time()
            }
            
            self.logger.info(f"Stored secret at path: {path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to store secret at {path}: {e}")
            return False
    
    async def rotate_secret(self, path: str, rotation_function) -> bool:
        """비밀 정보 순환"""
        try:
            # 현재 비밀 정보 조회
            current_secret = await self.get_secret(path)
            if not current_secret:
                self.logger.error(f"Cannot rotate secret - current secret not found at {path}")
                return False
            
            # 새 비밀 정보 생성
            new_secret = await rotation_function(current_secret)
            
            # 새 비밀 정보 저장
            success = await self.store_secret(path, new_secret)
            
            if success:
                self.logger.info(f"Successfully rotated secret at {path}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Secret rotation failed for {path}: {e}")
            return False
    
    async def delete_secret(self, path: str) -> bool:
        """비밀 정보 삭제"""
        try:
            self.client.secrets.kv.v2.delete_metadata_and_all_versions(path=path)
            
            # 캐시에서도 제거
            cache_key = f"secret_{path}"
            if cache_key in self.secret_cache:
                del self.secret_cache[cache_key]
            
            self.logger.info(f"Deleted secret at path: {path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete secret at {path}: {e}")
            return False

class APIKeyManager:
    """API 키 관리 시스템"""
    
    def __init__(self, vault_manager: VaultSecretManager):
        self.vault_manager = vault_manager
        self.key_rotation_schedule = {}
        self.key_usage_tracking = {}
        
    async def get_binance_credentials(self, environment: str = "production") -> Optional[Dict[str, str]]:
        """Binance API 자격증명 조회"""
        path = f"freqtrade/{environment}/binance"
        
        credentials = await self.vault_manager.get_secret(path)
        if not credentials:
            return None
        
        # 사용량 추적
        self._track_key_usage(path)
        
        return {
            'api_key': credentials.get('api_key'),
            'api_secret': credentials.get('api_secret'),
            'testnet': credentials.get('testnet', False)
        }
    
    async def rotate_binance_keys(self, environment: str = "production") -> bool:
        """Binance API 키 순환"""
        
        def rotation_function(current_credentials):
            # 실제 구현에서는 Binance API를 통해 새 키 생성
            # 여기서는 예시 로직
            return {
                'api_key': f"new_api_key_{int(time.time())}",
                'api_secret': f"new_api_secret_{int(time.time())}",
                'testnet': current_credentials.get('testnet', False),
                'created_at': datetime.now().isoformat(),
                'previous_key': current_credentials.get('api_key')
            }
        
        path = f"freqtrade/{environment}/binance"
        return await self.vault_manager.rotate_secret(path, rotation_function)
    
    async def schedule_key_rotation(self, key_path: str, rotation_interval_days: int):
        """키 순환 스케줄링"""
        next_rotation = datetime.now() + timedelta(days=rotation_interval_days)
        
        self.key_rotation_schedule[key_path] = {
            'next_rotation': next_rotation,
            'interval_days': rotation_interval_days
        }
        
        # 백그라운드 태스크로 순환 모니터링
        asyncio.create_task(self._monitor_key_rotation(key_path))
    
    async def _monitor_key_rotation(self, key_path: str):
        """키 순환 모니터링"""
        while key_path in self.key_rotation_schedule:
            schedule_info = self.key_rotation_schedule[key_path]
            
            if datetime.now() >= schedule_info['next_rotation']:
                # 키 순환 실행
                if "binance" in key_path:
                    environment = key_path.split('/')[1]
                    await self.rotate_binance_keys(environment)
                
                # 다음 순환 시간 업데이트
                schedule_info['next_rotation'] = datetime.now() + timedelta(
                    days=schedule_info['interval_days']
                )
            
            # 1시간마다 체크
            await asyncio.sleep(3600)
    
    def _track_key_usage(self, key_path: str):
        """키 사용량 추적"""
        if key_path not in self.key_usage_tracking:
            self.key_usage_tracking[key_path] = {
                'usage_count': 0,
                'last_used': None,
                'first_used': datetime.now()
            }
        
        tracking_info = self.key_usage_tracking[key_path]
        tracking_info['usage_count'] += 1
        tracking_info['last_used'] = datetime.now()
    
    async def get_key_usage_stats(self) -> Dict[str, Dict]:
        """키 사용량 통계 조회"""
        return self.key_usage_tracking.copy()

### 🌐 **네트워크 보안 설정**

```python
# automation/network_security.py
import asyncio
import subprocess
import ipaddress
from typing import List, Dict, Optional, Set
import logging
import json
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class FirewallRule:
    """방화벽 규칙"""
    name: str
    source_ip: str
    destination_port: int
    protocol: str = "tcp"
    action: str = "allow"  # allow, deny
    priority: int = 100

@dataclass
class RateLimitRule:
    """속도 제한 규칙"""
    endpoint: str
    requests_per_minute: int
    burst_size: int = 10
    whitelist_ips: List[str] = None

class NetworkSecurityManager:
    """네트워크 보안 관리자"""
    
    def __init__(self, notification_system):
        self.notification_system = notification_system
        self.firewall_rules: List[FirewallRule] = []
        self.rate_limit_rules: List[RateLimitRule] = []
        self.blocked_ips: Set[str] = set()
        self.connection_tracking: Dict[str, Dict] = {}
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    async def setup_firewall_rules(self):
        """기본 방화벽 규칙 설정"""
        
        # 기본 규칙들
        default_rules = [
            FirewallRule("ssh_access", "0.0.0.0/0", 22, "tcp", "allow", 50),
            FirewallRule("http_access", "0.0.0.0/0", 80, "tcp", "allow", 100),
            FirewallRule("https_access", "0.0.0.0/0", 443, "tcp", "allow", 100),
            FirewallRule("freqtrade_api", "10.0.0.0/8", 8080, "tcp", "allow", 200),
            FirewallRule("database_access", "10.0.0.0/8", 5432, "tcp", "allow", 300),
            FirewallRule("redis_access", "10.0.0.0/8", 6379, "tcp", "allow", 300),
            FirewallRule("deny_all", "0.0.0.0/0", 0, "tcp", "deny", 1000)
        ]
        
        for rule in default_rules:
            await self.add_firewall_rule(rule)
    
    async def add_firewall_rule(self, rule: FirewallRule) -> bool:
        """방화벽 규칙 추가"""
        try:
            # iptables 규칙 생성
            if rule.action == "allow":
                action = "ACCEPT"
            else:
                action = "DROP"
            
            # 규칙 추가 명령
            if rule.destination_port > 0:
                cmd = [
                    "iptables", "-A", "INPUT",
                    "-s", rule.source_ip,
                    "-p", rule.protocol,
                    "--dport", str(rule.destination_port),
                    "-j", action,
                    "-m", "comment", "--comment", rule.name
                ]
            else:
                cmd = [
                    "iptables", "-A", "INPUT",
                    "-s", rule.source_ip,
                    "-j", action,
                    "-m", "comment", "--comment", rule.name
                ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.firewall_rules.append(rule)
                self.logger.info(f"Added firewall rule: {rule.name}")
                return True
            else:
                self.logger.error(f"Failed to add firewall rule: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error adding firewall rule: {e}")
            return False
    
    async def block_ip_address(self, ip_address: str, duration_minutes: int = 60, reason: str = ""):
        """IP 주소 차단"""
        try:
            # IP 주소 유효성 검증
            ipaddress.ip_address(ip_address)
            
            # iptables 규칙 추가
            cmd = [
                "iptables", "-A", "INPUT",
                "-s", ip_address,
                "-j", "DROP",
                "-m", "comment", "--comment", f"blocked_{reason}"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.blocked_ips.add(ip_address)
                
                # 자동 해제 스케줄링
                if duration_minutes > 0:
                    asyncio.create_task(
                        self._schedule_ip_unblock(ip_address, duration_minutes)
                    )
                
                # 차단 알림
                await self._send_security_alert(
                    "IP_BLOCKED",
                    f"IP 주소 차단: {ip_address}",
                    f"사유: {reason}\n지속시간: {duration_minutes}분"
                )
                
                self.logger.info(f"Blocked IP address: {ip_address} for {duration_minutes} minutes")
                return True
            else:
                self.logger.error(f"Failed to block IP: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error blocking IP {ip_address}: {e}")
            return False
    
    async def _schedule_ip_unblock(self, ip_address: str, duration_minutes: int):
        """IP 차단 해제 스케줄링"""
        await asyncio.sleep(duration_minutes * 60)
        await self.unblock_ip_address(ip_address)
    
    async def unblock_ip_address(self, ip_address: str) -> bool:
        """IP 주소 차단 해제"""
        try:
            # iptables 규칙 제거
            cmd = [
                "iptables", "-D", "INPUT",
                "-s", ip_address,
                "-j", "DROP"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.blocked_ips.discard(ip_address)
                self.logger.info(f"Unblocked IP address: {ip_address}")
                return True
            else:
                self.logger.warning(f"Failed to unblock IP (may not be blocked): {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error unblocking IP {ip_address}: {e}")
            return False
    
    async def setup_rate_limiting(self):
        """속도 제한 설정"""
        
        # Nginx 설정을 통한 속도 제한
        nginx_config = """
# Rate limiting zones
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/m;
limit_req_zone $binary_remote_addr zone=login_limit:10m rate=5r/m;
limit_req_zone $binary_remote_addr zone=general_limit:10m rate=60r/m;

server {
    listen 80;
    server_name freqtrade-api.local;
    
    # API 엔드포인트 속도 제한
    location /api/ {
        limit_req zone=api_limit burst=5 nodelay;
        limit_req_status 429;
        proxy_pass http://freqtrade-backend;
    }
    
    # 로그인 엔드포인트 속도 제한
    location /api/v1/token/login {
        limit_req zone=login_limit burst=2 nodelay;
        limit_req_status 429;
        proxy_pass http://freqtrade-backend;
    }
    
    # 일반 요청 속도 제한
    location / {
        limit_req zone=general_limit burst=20 nodelay;
        limit_req_status 429;
        proxy_pass http://freqtrade-backend;
    }
}
        """
        
        # 설정 파일 저장
        with open('/etc/nginx/sites-available/freqtrade-rate-limit', 'w') as f:
            f.write(nginx_config)
        
        # Nginx 재로드
        subprocess.run(['nginx', '-s', 'reload'])
        
        self.logger.info("Rate limiting configured")
    
    async def monitor_suspicious_activity(self):
        """의심스러운 활동 모니터링"""
        while True:
            try:
                # 로그 파일 분석
                await self._analyze_access_logs()
                
                # 연결 추적 분석
                await self._analyze_connection_patterns()
                
                # 비정상적인 API 사용 패턴 감지
                await self._detect_api_abuse()
                
                await asyncio.sleep(60)  # 1분마다 체크
                
            except Exception as e:
                self.logger.error(f"Security monitoring error: {e}")
                await asyncio.sleep(300)  # 오류 시 5분 대기
    
    async def _analyze_access_logs(self):
        """접근 로그 분석"""
        try:
            # Nginx 접근 로그 분석
            with open('/var/log/nginx/access.log', 'r') as f:
                lines = f.readlines()[-1000:]  # 최근 1000줄
            
            suspicious_patterns = [
                'sql injection', 'script>', '<script', 'union select',
                '../../', 'cmd.exe', '/bin/bash', 'wget', 'curl'
            ]
            
            for line in lines:
                for pattern in suspicious_patterns:
                    if pattern.lower() in line.lower():
                        # 의심스러운 요청 감지
                        ip_address = line.split()[0]
                        await self._handle_suspicious_activity(
                            ip_address, f"Suspicious pattern detected: {pattern}", line
                        )
                        break
                        
        except Exception as e:
            self.logger.error(f"Log analysis error: {e}")
    
    async def _analyze_connection_patterns(self):
        """연결 패턴 분석"""
        try:
            # netstat을 통한 연결 분석
            result = subprocess.run(
                ['netstat', '-tn'], 
                capture_output=True, text=True
            )
            
            if result.returncode != 0:
                return
            
            connections = {}
            for line in result.stdout.split('\n'):
                if 'ESTABLISHED' in line:
                    parts = line.split()
                    if len(parts) >= 5:
                        foreign_address = parts[4].split(':')[0]
                        if foreign_address not in connections:
                            connections[foreign_address] = 0
                        connections[foreign_address] += 1
            
            # 비정상적으로 많은 연결을 가진 IP 감지
            for ip, count in connections.items():
                if count > 50:  # 50개 이상 연결
                    await self._handle_suspicious_activity(
                        ip, f"Too many connections: {count}", ""
                    )
                    
        except Exception as e:
            self.logger.error(f"Connection pattern analysis error: {e}")
    
    async def _detect_api_abuse(self):
        """API 남용 감지"""
        # API 사용량 로그 분석
        # 실제 구현에서는 Freqtrade API 로그나 메트릭 분석
        pass
    
    async def _handle_suspicious_activity(self, ip_address: str, reason: str, details: str):
        """의심스러운 활동 처리"""
        
        # IP 주소가 이미 차단되었는지 확인
        if ip_address in self.blocked_ips:
            return
        
        # 내부 IP는 스킵
        try:
            ip_obj = ipaddress.ip_address(ip_address)
            if ip_obj.is_private or ip_obj.is_loopback:
                return
        except:
            return
        
        # IP 차단
        await self.block_ip_address(ip_address, duration_minutes=60, reason=reason)
        
        # 보안 알림 전송
        await self._send_security_alert(
            "SUSPICIOUS_ACTIVITY",
            f"의심스러운 활동 감지: {ip_address}",
            f"사유: {reason}\n상세: {details[:500]}"
        )
    
    async def _send_security_alert(self, alert_type: str, title: str, message: str):
        """보안 알림 전송"""
        notification = Notification(
            title=f"🚨 {title}",
            message=f"유형: {alert_type}\n\n{message}",
            priority=NotificationPriority.HIGH,
            tags=['security', alert_type.lower()]
        )
        
        await self.notification_system.route_notification(notification)

### 📋 **감사 로그 시스템**

```python
# automation/audit_logging.py
import asyncio
import json
import hashlib
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
import logging
import os
from dataclasses import dataclass, asdict

class AuditEventType(Enum):
    """감사 이벤트 타입"""
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    API_KEY_ACCESS = "api_key_access"
    STRATEGY_CHANGE = "strategy_change"
    TRADE_EXECUTION = "trade_execution"
    CONFIGURATION_CHANGE = "configuration_change"
    SYSTEM_START = "system_start"
    SYSTEM_STOP = "system_stop"
    SECURITY_ALERT = "security_alert"
    DATA_ACCESS = "data_access"
    BACKUP_OPERATION = "backup_operation"
    ADMIN_ACTION = "admin_action"

class AuditLevel(Enum):
    """감사 레벨"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class AuditEvent:
    """감사 이벤트"""
    event_id: str
    timestamp: datetime
    event_type: AuditEventType
    level: AuditLevel
    user_id: Optional[str]
    session_id: Optional[str]
    source_ip: Optional[str]
    user_agent: Optional[str]
    resource: str
    action: str
    details: Dict[str, Any]
    result: str  # success, failure, partial
    risk_score: int = 0  # 0-100
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['event_type'] = self.event_type.value
        data['level'] = self.level.value
        return data
    
    def calculate_hash(self) -> str:
        """이벤트 무결성 해시 계산"""
        content = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()

class AuditLogger:
    """감사 로깅 시스템"""
    
    def __init__(self, log_directory: str = "/var/log/freqtrade/audit"):
        self.log_directory = log_directory
        self.current_log_file = None
        self.log_rotation_size = 100 * 1024 * 1024  # 100MB
        self.retention_days = 365  # 1년
        self.event_buffer = []
        self.buffer_size = 100
        self.encryption_key = self._load_or_generate_encryption_key()
        
        # 로그 디렉토리 생성
        os.makedirs(log_directory, exist_ok=True)
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # 백그라운드 태스크 시작
        asyncio.create_task(self._background_tasks())
    
    def _load_or_generate_encryption_key(self) -> bytes:
        """암호화 키 로드 또는 생성"""
        key_file = os.path.join(self.log_directory, '.audit_key')
        
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            # 새 키 생성
            key = os.urandom(32)  # 256-bit key
            with open(key_file, 'wb') as f:
                f.write(key)
            os.chmod(key_file, 0o600)  # 소유자만 읽기 가능
            return key
    
    async def log_event(self, event: AuditEvent):
        """감사 이벤트 로깅"""
        
        # 이벤트 ID 생성 (없는 경우)
        if not event.event_id:
            event.event_id = self._generate_event_id()
        
        # 버퍼에 추가
        self.event_buffer.append(event)
        
        # 버퍼가 가득 찬 경우 즉시 플러시
        if len(self.event_buffer) >= self.buffer_size:
            await self._flush_buffer()
        
        # 중요한 이벤트는 즉시 기록
        if event.level in [AuditLevel.ERROR, AuditLevel.CRITICAL] or event.risk_score > 70:
            await self._flush_buffer()
    
    def _generate_event_id(self) -> str:
        """이벤트 ID 생성"""
        timestamp = int(time.time() * 1000000)  # 마이크로초
        return f"audit_{timestamp}_{os.urandom(4).hex()}"
    
    async def _flush_buffer(self):
        """버퍼 플러시"""
        if not self.event_buffer:
            return
        
        try:
            current_file = await self._get_current_log_file()
            
            with open(current_file, 'a', encoding='utf-8') as f:
                for event in self.event_buffer:
                    # 이벤트 무결성 해시 추가
                    event_data = event.to_dict()
                    event_data['integrity_hash'] = event.calculate_hash()
                    
                    # JSON 라인으로 기록
                    f.write(json.dumps(event_data) + '\n')
            
            self.logger.info(f"Flushed {len(self.event_buffer)} audit events")
            self.event_buffer.clear()
            
        except Exception as e:
            self.logger.error(f"Failed to flush audit buffer: {e}")
    
    async def _get_current_log_file(self) -> str:
        """현재 로그 파일 경로 반환"""
        today = datetime.now().strftime('%Y-%m-%d')
        log_file = os.path.join(self.log_directory, f"audit_{today}.jsonl")
        
        # 파일 크기 체크 및 로테이션
        if os.path.exists(log_file) and os.path.getsize(log_file) > self.log_rotation_size:
            # 로테이션 실행
            timestamp = datetime.now().strftime('%H%M%S')
            rotated_file = os.path.join(self.log_directory, f"audit_{today}_{timestamp}.jsonl")
            os.rename(log_file, rotated_file)
        
        return log_file
    
    async def _background_tasks(self):
        """백그라운드 태스크"""
        while True:
            try:
                # 주기적 버퍼 플러시 (30초마다)
                await asyncio.sleep(30)
                await self._flush_buffer()
                
                # 오래된 로그 파일 정리 (1시간마다)
                if int(time.time()) % 3600 < 30:
                    await self._cleanup_old_logs()
                
            except Exception as e:
                self.logger.error(f"Audit background task error: {e}")
                await asyncio.sleep(60)
    
    async def _cleanup_old_logs(self):
        """오래된 로그 파일 정리"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            
            for filename in os.listdir(self.log_directory):
                if filename.startswith('audit_') and filename.endswith('.jsonl'):
                    file_path = os.path.join(self.log_directory, filename)
                    file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                    
                    if file_mtime < cutoff_date:
                        os.remove(file_path)
                        self.logger.info(f"Removed old audit log: {filename}")
                        
        except Exception as e:
            self.logger.error(f"Log cleanup error: {e}")
    
    async def search_events(self, 
                          start_time: datetime, 
                          end_time: datetime,
                          event_types: List[AuditEventType] = None,
                          user_id: str = None,
                          source_ip: str = None,
                          resource: str = None) -> List[AuditEvent]:
        """감사 이벤트 검색"""
        
        events = []
        
        # 검색 대상 날짜 범위의 로그 파일들
        current_date = start_time.date()
        end_date = end_time.date()
        
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            pattern = f"audit_{date_str}*.jsonl"
            
            for filename in os.listdir(self.log_directory):
                if filename.startswith(f"audit_{date_str}") and filename.endswith('.jsonl'):
                    file_path = os.path.join(self.log_directory, filename)
                    
                    with open(file_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            try:
                                event_data = json.loads(line.strip())
                                event_time = datetime.fromisoformat(event_data['timestamp'])
                                
                                # 시간 범위 체크
                                if not (start_time <= event_time <= end_time):
                                    continue
                                
                                # 필터 적용
                                if event_types and event_data['event_type'] not in [et.value for et in event_types]:
                                    continue
                                
                                if user_id and event_data.get('user_id') != user_id:
                                    continue
                                
                                if source_ip and event_data.get('source_ip') != source_ip:
                                    continue
                                
                                if resource and resource not in event_data.get('resource', ''):
                                    continue
                                
                                # AuditEvent 객체로 변환
                                event = AuditEvent(
                                    event_id=event_data['event_id'],
                                    timestamp=event_time,
                                    event_type=AuditEventType(event_data['event_type']),
                                    level=AuditLevel(event_data['level']),
                                    user_id=event_data.get('user_id'),
                                    session_id=event_data.get('session_id'),
                                    source_ip=event_data.get('source_ip'),
                                    user_agent=event_data.get('user_agent'),
                                    resource=event_data['resource'],
                                    action=event_data['action'],
                                    details=event_data.get('details', {}),
                                    result=event_data['result'],
                                    risk_score=event_data.get('risk_score', 0)
                                )
                                
                                events.append(event)
                                
                            except Exception as e:
                                self.logger.error(f"Error parsing audit event: {e}")
                                continue
            
            current_date += timedelta(days=1)
        
        # 시간순 정렬
        events.sort(key=lambda x: x.timestamp)
        
        return events
    
    async def verify_integrity(self, event: AuditEvent) -> bool:
        """이벤트 무결성 검증"""
        calculated_hash = event.calculate_hash()
        # 실제 구현에서는 저장된 해시와 비교
        return True  # 임시로 True 반환

class ComplianceReporter:
    """컴플라이언스 보고서 생성기"""
    
    def __init__(self, audit_logger: AuditLogger):
        self.audit_logger = audit_logger
    
    async def generate_security_report(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """보안 보고서 생성"""
        
        # 보안 관련 이벤트 조회
        security_events = await self.audit_logger.search_events(
            start_date, end_date,
            event_types=[
                AuditEventType.USER_LOGIN,
                AuditEventType.API_KEY_ACCESS,
                AuditEventType.SECURITY_ALERT,
                AuditEventType.ADMIN_ACTION
            ]
        )
        
        # 통계 계산
        total_events = len(security_events)
        failed_logins = len([e for e in security_events 
                           if e.event_type == AuditEventType.USER_LOGIN and e.result == 'failure'])
        
        unique_ips = len(set(e.source_ip for e in security_events if e.source_ip))
        high_risk_events = len([e for e in security_events if e.risk_score > 70])
        
        # 시간별 분포
        hourly_distribution = {}
        for event in security_events:
            hour = event.timestamp.hour
            hourly_distribution[hour] = hourly_distribution.get(hour, 0) + 1
        
        return {
            'report_period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'summary': {
                'total_security_events': total_events,
                'failed_login_attempts': failed_logins,
                'unique_source_ips': unique_ips,
                'high_risk_events': high_risk_events
            },
            'hourly_distribution': hourly_distribution,
            'top_source_ips': self._get_top_source_ips(security_events),
            'recommendations': self._generate_security_recommendations(security_events)
        }
    
    def _get_top_source_ips(self, events: List[AuditEvent]) -> List[Dict[str, Any]]:
        """상위 소스 IP 분석"""
        ip_counts = {}
        
        for event in events:
            if event.source_ip:
                if event.source_ip not in ip_counts:
                    ip_counts[event.source_ip] = {'count': 0, 'risk_events': 0}
                
                ip_counts[event.source_ip]['count'] += 1
                if event.risk_score > 50:
                    ip_counts[event.source_ip]['risk_events'] += 1
        
        # 상위 10개 IP
        top_ips = sorted(ip_counts.items(), key=lambda x: x[1]['count'], reverse=True)[:10]
        
        return [{'ip': ip, 'count': data['count'], 'risk_events': data['risk_events']} 
                for ip, data in top_ips]
    
    def _generate_security_recommendations(self, events: List[AuditEvent]) -> List[str]:
        """보안 권장사항 생성"""
        recommendations = []
        
        failed_logins = [e for e in events 
                        if e.event_type == AuditEventType.USER_LOGIN and e.result == 'failure']
        
        if len(failed_logins) > 50:
            recommendations.append("로그인 실패 횟수가 많습니다. 계정 잠금 정책을 강화하세요.")
        
        high_risk_events = [e for e in events if e.risk_score > 80]
        if len(high_risk_events) > 10:
            recommendations.append("고위험 보안 이벤트가 다수 발생했습니다. 보안 모니터링을 강화하세요.")
        
        # 야간 활동 체크
        night_events = [e for e in events if 0 <= e.timestamp.hour <= 6]
        if len(night_events) > len(events) * 0.3:
            recommendations.append("야간 시간대 활동이 많습니다. 비정상적인 접근인지 확인하세요.")
        
        return recommendations

---

## 🚀 **운영 및 유지보수 자동화**

### 💾 **자동 백업 및 복구**

```python
# automation/backup_automation.py
import asyncio
import os
import shutil
import tarfile
import gzip
import boto3
import subprocess
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
import json
from dataclasses import dataclass
from pathlib import Path

@dataclass
class BackupConfig:
    """백업 설정"""
    name: str
    source_paths: List[str]
    destination: str
    schedule_cron: str
    retention_days: int
    compression: bool = True
    encryption: bool = True
    cloud_sync: bool = False
    verification: bool = True

class AutomatedBackupManager:
    """자동화된 백업 관리자"""
    
    def __init__(self, notification_system):
        self.notification_system = notification_system
        self.backup_configs: Dict[str, BackupConfig] = {}
        self.active_backups: Dict[str, asyncio.Task] = {}
        self.backup_history: List[Dict] = []
        
        # AWS S3 클라이언트 (클라우드 백업용)
        self.s3_client = None
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def setup_s3_client(self, aws_access_key: str, aws_secret_key: str, region: str = 'us-east-1'):
        """S3 클라이언트 설정"""
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=region
        )
    
    async def register_backup_job(self, config: BackupConfig):
        """백업 작업 등록"""
        self.backup_configs[config.name] = config
        
        # 스케줄된 백업 태스크 시작
        if config.name not in self.active_backups:
            task = asyncio.create_task(self._scheduled_backup_loop(config))
            self.active_backups[config.name] = task
        
        self.logger.info(f"Registered backup job: {config.name}")
    
    async def _scheduled_backup_loop(self, config: BackupConfig):
        """스케줄된 백업 루프"""
        while True:
            try:
                # 다음 실행 시간 계산 (간단한 구현 - 실제로는 croniter 사용)
                next_run = self._calculate_next_run_time(config.schedule_cron)
                
                # 다음 실행 시간까지 대기
                wait_seconds = (next_run - datetime.now()).total_seconds()
                if wait_seconds > 0:
                    await asyncio.sleep(wait_seconds)
                
                # 백업 실행
                await self.execute_backup(config.name)
                
            except Exception as e:
                self.logger.error(f"Scheduled backup error for {config.name}: {e}")
                await asyncio.sleep(3600)  # 오류 시 1시간 대기
    
    def _calculate_next_run_time(self, cron_expression: str) -> datetime:
        """다음 실행 시간 계산 (간단한 구현)"""
        # 실제 구현에서는 croniter 라이브러리 사용
        # 여기서는 예시로 1시간 후 반환
        return datetime.now() + timedelta(hours=1)
    
    async def execute_backup(self, backup_name: str, force: bool = False) -> bool:
        """백업 실행"""
        if backup_name not in self.backup_configs:
            self.logger.error(f"Backup config not found: {backup_name}")
            return False
        
        config = self.backup_configs[backup_name]
        backup_id = f"{backup_name}_{int(datetime.now().timestamp())}"
        
        try:
            self.logger.info(f"Starting backup: {backup_name}")
            
            # 백업 시작 알림
            await self._send_backup_notification(backup_name, "started", backup_id)
            
            # 1. 백업 디렉토리 생성
            backup_dir = await self._create_backup_directory(config, backup_id)
            
            # 2. 데이터 백업
            backup_files = await self._backup_data(config, backup_dir)
            
            # 3. 압축 및 암호화
            if config.compression or config.encryption:
                backup_archive = await self._compress_and_encrypt(backup_dir, config)
                
                # 원본 디렉토리 제거
                shutil.rmtree(backup_dir)
                backup_files = [backup_archive]
            
            # 4. 검증
            if config.verification:
                verification_result = await self._verify_backup(backup_files)
                if not verification_result:
                    raise Exception("Backup verification failed")
            
            # 5. 클라우드 동기화
            if config.cloud_sync and self.s3_client:
                await self._sync_to_cloud(backup_files, config)
            
            # 6. 오래된 백업 정리
            await self._cleanup_old_backups(config)
            
            # 백업 완료 기록
            backup_record = {
                'backup_id': backup_id,
                'backup_name': backup_name,
                'timestamp': datetime.now().isoformat(),
                'status': 'completed',
                'files': backup_files,
                'size_mb': sum(os.path.getsize(f) for f in backup_files) / (1024 * 1024)
            }
            
            self.backup_history.append(backup_record)
            
            # 완료 알림
            await self._send_backup_notification(backup_name, "completed", backup_id, backup_record)
            
            self.logger.info(f"Backup completed successfully: {backup_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Backup failed for {backup_name}: {e}")
            
            # 실패 알림
            await self._send_backup_notification(backup_name, "failed", backup_id, {'error': str(e)})
            
            return False
    
    async def _create_backup_directory(self, config: BackupConfig, backup_id: str) -> str:
        """백업 디렉토리 생성"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = os.path.join(config.destination, f"{backup_id}_{timestamp}")
        
        os.makedirs(backup_dir, exist_ok=True)
        return backup_dir
    
    async def _backup_data(self, config: BackupConfig, backup_dir: str) -> List[str]:
        """데이터 백업"""
        backup_files = []
        
        for source_path in config.source_paths:
            if not os.path.exists(source_path):
                self.logger.warning(f"Source path not found: {source_path}")
                continue
            
            # 소스 경로의 베이스네임 얻기
            basename = os.path.basename(source_path)
            dest_path = os.path.join(backup_dir, basename)
            
            if os.path.isfile(source_path):
                # 파일 복사
                shutil.copy2(source_path, dest_path)
                backup_files.append(dest_path)
                
            elif os.path.isdir(source_path):
                # 디렉토리 복사
                shutil.copytree(source_path, dest_path)
                backup_files.append(dest_path)
        
        # 데이터베이스 백업 (PostgreSQL)
        if "database" in config.name.lower():
            await self._backup_database(backup_dir)
        
        return backup_files
    
    async def _backup_database(self, backup_dir: str):
        """데이터베이스 백업"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            dump_file = os.path.join(backup_dir, f"database_dump_{timestamp}.sql")
            
            # PostgreSQL 덤프
            cmd = [
                'pg_dump',
                '-h', 'localhost',
                '-U', 'freqtrade',
                '-d', 'freqtrade',
                '-f', dump_file,
                '--no-password'
            ]
            
            # 환경 변수로 비밀번호 설정
            env = os.environ.copy()
            env['PGPASSWORD'] = os.getenv('DB_PASSWORD', '')
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.logger.info(f"Database backup completed: {dump_file}")
            else:
                self.logger.error(f"Database backup failed: {result.stderr}")
                
        except Exception as e:
            self.logger.error(f"Database backup error: {e}")
    
    async def _compress_and_encrypt(self, backup_dir: str, config: BackupConfig) -> str:
        """백업 압축 및 암호화"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        archive_name = f"{config.name}_{timestamp}.tar.gz"
        archive_path = os.path.join(config.destination, archive_name)
        
        # tar.gz 압축
        with tarfile.open(archive_path, 'w:gz') as tar:
            tar.add(backup_dir, arcname=os.path.basename(backup_dir))
        
        # 암호화 (GPG 사용)
        if config.encryption:
            encrypted_path = f"{archive_path}.gpg"
            
            cmd = [
                'gpg', '--cipher-algo', 'AES256',
                '--compress-algo', '1',
                '--symmetric',
                '--batch', '--yes',
                '--passphrase', os.getenv('BACKUP_PASSPHRASE', 'default_passphrase'),
                '--output', encrypted_path,
                archive_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                os.remove(archive_path)  # 원본 압축 파일 삭제
                archive_path = encrypted_path
            else:
                self.logger.error(f"Encryption failed: {result.stderr}")
        
        return archive_path
    
    async def _verify_backup(self, backup_files: List[str]) -> bool:
        """백업 검증"""
        try:
            for backup_file in backup_files:
                if not os.path.exists(backup_file):
                    self.logger.error(f"Backup file not found: {backup_file}")
                    return False
                
                # 파일 크기 확인
                file_size = os.path.getsize(backup_file)
                if file_size == 0:
                    self.logger.error(f"Backup file is empty: {backup_file}")
                    return False
                
                # 압축 파일 무결성 검사
                if backup_file.endswith('.tar.gz'):
                    try:
                        with tarfile.open(backup_file, 'r:gz') as tar:
                            tar.getmembers()  # 압축 파일 구조 확인
                    except Exception as e:
                        self.logger.error(f"Backup file integrity check failed: {e}")
                        return False
            
            self.logger.info("Backup verification completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Backup verification error: {e}")
            return False
    
    async def _sync_to_cloud(self, backup_files: List[str], config: BackupConfig):
        """클라우드 동기화"""
        if not self.s3_client:
            self.logger.warning("S3 client not configured, skipping cloud sync")
            return
        
        bucket_name = os.getenv('BACKUP_S3_BUCKET', 'freqtrade-backups')
        
        for backup_file in backup_files:
            try:
                filename = os.path.basename(backup_file)
                s3_key = f"freqtrade/{config.name}/{filename}"
                
                self.s3_client.upload_file(backup_file, bucket_name, s3_key)
                
                self.logger.info(f"Uploaded to S3: {s3_key}")
                
            except Exception as e:
                self.logger.error(f"S3 upload failed for {backup_file}: {e}")
    
    async def _cleanup_old_backups(self, config: BackupConfig):
        """오래된 백업 정리"""
        try:
            cutoff_date = datetime.now() - timedelta(days=config.retention_days)
            
            # 로컬 백업 정리
            for filename in os.listdir(config.destination):
                if filename.startswith(config.name):
                    file_path = os.path.join(config.destination, filename)
                    file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                    
                    if file_mtime < cutoff_date:
                        os.remove(file_path)
                        self.logger.info(f"Removed old backup: {filename}")
            
            # S3 백업 정리 (있는 경우)
            if config.cloud_sync and self.s3_client:
                await self._cleanup_s3_backups(config, cutoff_date)
                
        except Exception as e:
            self.logger.error(f"Backup cleanup error: {e}")
    
    async def _cleanup_s3_backups(self, config: BackupConfig, cutoff_date: datetime):
        """S3 백업 정리"""
        try:
            bucket_name = os.getenv('BACKUP_S3_BUCKET', 'freqtrade-backups')
            prefix = f"freqtrade/{config.name}/"
            
            response = self.s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
            
            if 'Contents' in response:
                for obj in response['Contents']:
                    if obj['LastModified'].replace(tzinfo=None) < cutoff_date:
                        self.s3_client.delete_object(Bucket=bucket_name, Key=obj['Key'])
                        self.logger.info(f"Removed old S3 backup: {obj['Key']}")
                        
        except Exception as e:
            self.logger.error(f"S3 cleanup error: {e}")
    
    async def _send_backup_notification(self, backup_name: str, status: str, 
                                      backup_id: str, details: Dict = None):
        """백업 알림 전송"""
        
        if status == "started":
            title = f"💾 백업 시작: {backup_name}"
            message = f"백업 ID: {backup_id}\n시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            priority = NotificationPriority.LOW
            
        elif status == "completed":
            title = f"✅ 백업 완료: {backup_name}"
            message = f"백업 ID: {backup_id}\n"
            if details:
                message += f"크기: {details.get('size_mb', 0):.2f} MB\n"
                message += f"파일 수: {len(details.get('files', []))}"
            priority = NotificationPriority.LOW
            
        elif status == "failed":
            title = f"❌ 백업 실패: {backup_name}"
            message = f"백업 ID: {backup_id}\n"
            if details and 'error' in details:
                message += f"오류: {details['error']}"
            priority = NotificationPriority.HIGH
        
        notification = Notification(
            title=title,
            message=message,
            priority=priority,
            tags=['backup', backup_name, status]
        )
        
        await self.notification_system.route_notification(notification)
    
    async def restore_from_backup(self, backup_id: str, restore_path: str) -> bool:
        """백업에서 복원"""
        
        # 백업 기록에서 찾기
        backup_record = next((r for r in self.backup_history if r['backup_id'] == backup_id), None)
        
        if not backup_record:
            self.logger.error(f"Backup record not found: {backup_id}")
            return False
        
        try:
            self.logger.info(f"Starting restore from backup: {backup_id}")
            
            backup_files = backup_record['files']
            
            for backup_file in backup_files:
                if backup_file.endswith('.gpg'):
                    # 복호화
                    decrypted_file = await self._decrypt_backup(backup_file)
                    backup_file = decrypted_file
                
                if backup_file.endswith('.tar.gz'):
                    # 압축 해제
                    with tarfile.open(backup_file, 'r:gz') as tar:
                        tar.extractall(restore_path)
                else:
                    # 단순 파일 복사
                    shutil.copy2(backup_file, restore_path)
            
            self.logger.info(f"Restore completed successfully to: {restore_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Restore failed: {e}")
            return False
    
    async def _decrypt_backup(self, encrypted_file: str) -> str:
        """백업 복호화"""
        decrypted_file = encrypted_file[:-4]  # .gpg 제거
        
        cmd = [
            'gpg', '--batch', '--yes',
            '--passphrase', os.getenv('BACKUP_PASSPHRASE', 'default_passphrase'),
            '--decrypt',
            '--output', decrypted_file,
            encrypted_file
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            return decrypted_file
        else:
            raise Exception(f"Decryption failed: {result.stderr}")

### 🔄 **시스템 업데이트 자동화**

```python
# automation/system_updates.py
import asyncio
import subprocess
import os
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from enum import Enum

class UpdateType(Enum):
    """업데이트 타입"""
    SECURITY = "security"
    SYSTEM = "system"
    APPLICATION = "application"
    DOCKER = "docker"
    STRATEGY = "strategy"

class UpdateStatus(Enum):
    """업데이트 상태"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"

@dataclass
class UpdatePackage:
    """업데이트 패키지"""
    name: str
    current_version: str
    new_version: str
    update_type: UpdateType
    security_update: bool = False
    auto_install: bool = False
    requires_restart: bool = False

class SystemUpdateManager:
    """시스템 업데이트 관리자"""
    
    def __init__(self, notification_system, backup_manager):
        self.notification_system = notification_system
        self.backup_manager = backup_manager
        self.update_schedule = {}
        self.update_history = []
        self.maintenance_windows = []
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    async def check_available_updates(self) -> Dict[UpdateType, List[UpdatePackage]]:
        """사용 가능한 업데이트 확인"""
        
        updates = {
            UpdateType.SECURITY: [],
            UpdateType.SYSTEM: [],
            UpdateType.APPLICATION: [],
            UpdateType.DOCKER: [],
            UpdateType.STRATEGY: []
        }
        
        # 시스템 패키지 업데이트 확인
        system_updates = await self._check_system_updates()
        updates[UpdateType.SYSTEM].extend(system_updates)
        
        # 보안 업데이트 확인
        security_updates = await self._check_security_updates()
        updates[UpdateType.SECURITY].extend(security_updates)
        
        # Docker 이미지 업데이트 확인
        docker_updates = await self._check_docker_updates()
        updates[UpdateType.DOCKER].extend(docker_updates)
        
        # Freqtrade 업데이트 확인
        app_updates = await self._check_freqtrade_updates()
        updates[UpdateType.APPLICATION].extend(app_updates)
        
        # 전략 업데이트 확인
        strategy_updates = await self._check_strategy_updates()
        updates[UpdateType.STRATEGY].extend(strategy_updates)
        
        return updates
    
    async def _check_system_updates(self) -> List[UpdatePackage]:
        """시스템 패키지 업데이트 확인"""
        try:
            # apt list --upgradable 실행
            result = subprocess.run(
                ['apt', 'list', '--upgradable'],
                capture_output=True, text=True
            )
            
            updates = []
            lines = result.stdout.strip().split('\n')[1:]  # 헤더 제외
            
            for line in lines:
                if '/' in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        package_name = parts[0].split('/')[0]
                        version_info = parts[1]
                        
                        # 현재 버전과 새 버전 추출
                        if '[upgradable from:' in line:
                            current_version = line.split('[upgradable from: ')[1].split(']')[0]
                            new_version = version_info
                        else:
                            current_version = "unknown"
                            new_version = version_info
                        
                        update = UpdatePackage(
                            name=package_name,
                            current_version=current_version,
                            new_version=new_version,
                            update_type=UpdateType.SYSTEM,
                            auto_install=not self._is_critical_package(package_name)
                        )
                        
                        updates.append(update)
            
            return updates
            
        except Exception as e:
            self.logger.error(f"System update check failed: {e}")
            return []
    
    async def _check_security_updates(self) -> List[UpdatePackage]:
        """보안 업데이트 확인"""
        try:
            # unattended-upgrades를 통한 보안 업데이트 확인
            result = subprocess.run(
                ['unattended-upgrade', '--dry-run'],
                capture_output=True, text=True
            )
            
            updates = []
            # 결과 파싱하여 보안 업데이트 추출
            # 실제 구현에서는 더 정교한 파싱 필요
            
            return updates
            
        except Exception as e:
            self.logger.error(f"Security update check failed: {e}")
            return []
    
    async def _check_docker_updates(self) -> List[UpdatePackage]:
        """Docker 이미지 업데이트 확인"""
        try:
            updates = []
            
            # 사용 중인 이미지 목록
            images = [
                'freqtradeorg/freqtrade:stable',
                'postgres:14',
                'redis:alpine',
                'nginx:alpine'
            ]
            
            for image in images:
                try: