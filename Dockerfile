# Freqtrade Futures Trading Bot - Production Dockerfile
# Phase 8: Cloud Deployment Configuration

FROM python:3.11-slim

# 시스템 종속성 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    libssl-dev \
    git \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /freqtrade

# Python 의존성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Freqtrade 설치
RUN pip install freqtrade[complete]

# 애플리케이션 코드 복사
COPY . .

# 권한 설정
RUN chmod +x /freqtrade/scripts/*.sh

# 포트 노출
EXPOSE 8080 5000

# 환경 변수 설정
ENV PYTHONPATH=/freqtrade
ENV FREQTRADE_USERDIR=/freqtrade/user_data

# 헬스체크 설정
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/api/v1/ping || exit 1

# 기본 명령어
CMD ["python", "-c", "print('Freqtrade Futures Bot - Ready for deployment')"]