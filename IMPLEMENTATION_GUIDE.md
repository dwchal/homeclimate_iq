# Multi-Sensor Climate Correlation Tool - Implementation Guide

## Overview
This guide provides a step-by-step approach to building a comprehensive climate monitoring and correlation tool that integrates data from:
- **AirGradient** sensor (air quality)
- **GoVee** sensors (temperature/humidity)
- **Google Nest** thermostat
- **HomeKit** devices
- **Utility company** data

The tool will collect, store, analyze, and visualize correlations between sensor data and energy consumption.

---

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [Phase 1: Project Setup](#phase-1-project-setup)
4. [Phase 2: Data Collection Layer](#phase-2-data-collection-layer)
5. [Phase 3: Database & Storage](#phase-3-database--storage)
6. [Phase 4: Data Processing & Analysis](#phase-4-data-processing--analysis)
7. [Phase 5: Visualization Dashboard](#phase-5-visualization-dashboard)
8. [Phase 6: Correlation Engine](#phase-6-correlation-engine)
9. [Phase 7: Testing & Deployment](#phase-7-testing--deployment)
10. [Appendix: API References](#appendix-api-references)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Data Sources Layer                      │
├──────────────┬──────────────┬──────────────┬───────────────┤
│  AirGradient │ GoVee Sensors│ Google Nest  │   HomeKit     │
│              │              │  Thermostat  │   Devices     │
└──────┬───────┴──────┬───────┴──────┬───────┴───────┬───────┘
       │              │               │               │
       └──────────────┴───────────────┴───────────────┘
                            │
                            ▼
       ┌────────────────────────────────────────────┐
       │        Data Collection Service             │
       │  (API polling, webhook handlers, MQTT)     │
       └────────────────┬───────────────────────────┘
                        │
                        ▼
       ┌────────────────────────────────────────────┐
       │          Time-Series Database              │
       │         (InfluxDB or PostgreSQL)           │
       └────────────────┬───────────────────────────┘
                        │
                        ▼
       ┌────────────────────────────────────────────┐
       │      Data Processing & Analysis Layer      │
       │    (Correlation engine, aggregations)      │
       └────────────────┬───────────────────────────┘
                        │
                        ▼
       ┌────────────────────────────────────────────┐
       │         Visualization Dashboard            │
       │      (Grafana, Custom Web UI, or both)     │
       └────────────────────────────────────────────┘
```

---

## Prerequisites

### Hardware Requirements
- [ ] Running AirGradient sensor (ensure it's connected to your network)
- [ ] GoVee sensors with Bluetooth or WiFi connectivity
- [ ] Google Nest thermostat with API access enabled
- [ ] HomeKit-enabled devices
- [ ] Server/computer to run the application (Raspberry Pi, NUC, or cloud instance)

### Software Requirements
- [ ] Python 3.9+ installed
- [ ] Docker and Docker Compose (recommended)
- [ ] Git
- [ ] Access to utility company data (check if they have an API or export functionality)

### API Access & Credentials
- [ ] **AirGradient**: API key or local API endpoint
- [ ] **GoVee**: Developer API key from https://developer.govee.com
- [ ] **Google Nest**: Device Access Console project and OAuth credentials
- [ ] **HomeKit**: HomeKit Controller access (via Home Assistant or homebridge)
- [ ] **Utility Company**: API credentials or CSV export access

---

## Phase 1: Project Setup

### Step 1.1: Initialize Python Project Structure

```bash
# Create directory structure
mkdir -p src/{collectors,storage,analysis,api,utils}
mkdir -p config
mkdir -p data/{raw,processed}
mkdir -p tests
mkdir -p dashboards
mkdir -p docs
```

### Step 1.2: Create Virtual Environment

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 1.3: Create requirements.txt

Create `requirements.txt`:
```text
# Core
python-dotenv==1.0.0
pydantic==2.5.0
pydantic-settings==2.1.0

# Data collection
requests==2.31.0
aiohttp==3.9.1
govee-api-laggat==0.2.0
python-nest==4.2.0
pyatv==0.14.5  # For HomeKit

# MQTT (for AirGradient if using MQTT)
paho-mqtt==1.6.1

# Database
influxdb-client==1.38.0
# OR for PostgreSQL:
# psycopg2-binary==2.9.9
# sqlalchemy==2.0.23

# Data processing
pandas==2.1.4
numpy==1.26.2
scipy==1.11.4

# Analysis & ML (optional)
scikit-learn==1.3.2
statsmodels==0.14.1

# Visualization
plotly==5.18.0
matplotlib==3.8.2

# API
fastapi==0.109.0
uvicorn==0.27.0

# Scheduling
apscheduler==3.10.4

# Logging
loguru==0.7.2

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
```

### Step 1.4: Create Environment Configuration

Create `.env.example`:
```bash
# AirGradient Configuration
AIRGRADIENT_API_KEY=your_api_key_here
AIRGRADIENT_DEVICE_ID=your_device_id
# OR for local access:
AIRGRADIENT_LOCAL_IP=192.168.1.xxx

# GoVee Configuration
GOVEE_API_KEY=your_govee_api_key
GOVEE_DEVICE_IDS=device_id_1,device_id_2

# Google Nest Configuration
NEST_PROJECT_ID=your_nest_project_id
NEST_CLIENT_ID=your_client_id
NEST_CLIENT_SECRET=your_client_secret
NEST_REDIRECT_URI=http://localhost:8080/auth/callback
NEST_DEVICE_ID=your_thermostat_id

# HomeKit Configuration
HOMEKIT_CONTROLLER_TYPE=homeassistant  # or homebridge
HOMEKIT_URL=http://homeassistant.local:8123
HOMEKIT_TOKEN=your_homeassistant_token

# Utility Company Configuration
UTILITY_PROVIDER=pge  # or your provider
UTILITY_API_KEY=your_utility_api_key
UTILITY_ACCOUNT_NUMBER=your_account_number
# OR for CSV import:
UTILITY_DATA_PATH=./data/raw/utility_data.csv

# Database Configuration
DB_TYPE=influxdb  # or postgresql
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=your_influxdb_token
INFLUXDB_ORG=your_org
INFLUXDB_BUCKET=climate_data

# Application Settings
LOG_LEVEL=INFO
DATA_COLLECTION_INTERVAL=300  # seconds (5 minutes)
TIMEZONE=America/Los_Angeles

# API Settings
API_HOST=0.0.0.0
API_PORT=8000
```

Create `.env` from the example:
```bash
cp .env.example .env
# Edit .env with your actual credentials
```

### Step 1.5: Create Docker Compose Configuration

Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  influxdb:
    image: influxdb:2.7
    container_name: climate_influxdb
    ports:
      - "8086:8086"
    volumes:
      - influxdb_data:/var/lib/influxdb2
      - ./config/influxdb:/etc/influxdb2
    environment:
      - DOCKER_INFLUXDB_INIT_MODE=setup
      - DOCKER_INFLUXDB_INIT_USERNAME=admin
      - DOCKER_INFLUXDB_INIT_PASSWORD=changeme123
      - DOCKER_INFLUXDB_INIT_ORG=home_climate
      - DOCKER_INFLUXDB_INIT_BUCKET=climate_data
      - DOCKER_INFLUXDB_INIT_ADMIN_TOKEN=my-super-secret-token
    restart: unless-stopped

  grafana:
    image: grafana/grafana:10.2.3
    container_name: climate_grafana
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
      - ./dashboards:/etc/grafana/provisioning/dashboards
      - ./config/grafana:/etc/grafana/provisioning/datasources
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_INSTALL_PLUGINS=grafana-clock-panel
    depends_on:
      - influxdb
    restart: unless-stopped

  app:
    build: .
    container_name: climate_collector
    volumes:
      - ./src:/app/src
      - ./data:/app/data
      - ./config:/app/config
    env_file:
      - .env
    depends_on:
      - influxdb
    restart: unless-stopped
    command: python src/main.py

volumes:
  influxdb_data:
  grafana_data:
```

### Step 1.6: Create Dockerfile

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Run the application
CMD ["python", "src/main.py"]
```

---

## Phase 2: Data Collection Layer

### Step 2.1: Create Base Collector Interface

Create `src/collectors/base_collector.py`:
```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from datetime import datetime
from loguru import logger


class BaseCollector(ABC):
    """Base class for all sensor collectors"""

    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.last_collection = None

    @abstractmethod
    async def collect(self) -> List[Dict[str, Any]]:
        """Collect data from the sensor/service"""
        pass

    @abstractmethod
    async def validate_connection(self) -> bool:
        """Validate connection to the sensor/service"""
        pass

    def format_data_point(self, measurement: str, value: float,
                         tags: Dict[str, str] = None,
                         timestamp: datetime = None) -> Dict[str, Any]:
        """Format data point for storage"""
        return {
            "measurement": measurement,
            "value": value,
            "tags": tags or {},
            "timestamp": timestamp or datetime.utcnow(),
            "source": self.name
        }

    async def run_collection(self) -> List[Dict[str, Any]]:
        """Run collection with error handling"""
        try:
            logger.info(f"Starting collection for {self.name}")
            data = await self.collect()
            self.last_collection = datetime.utcnow()
            logger.info(f"Collected {len(data)} data points from {self.name}")
            return data
        except Exception as e:
            logger.error(f"Error collecting data from {self.name}: {e}")
            return []
```

### Step 2.2: Implement AirGradient Collector

Create `src/collectors/airgradient_collector.py`:
```python
import aiohttp
from typing import List, Dict, Any
from .base_collector import BaseCollector
from loguru import logger


class AirGradientCollector(BaseCollector):
    """Collector for AirGradient sensor data"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__("airgradient", config)
        self.api_key = config.get("api_key")
        self.device_id = config.get("device_id")
        self.local_ip = config.get("local_ip")
        self.use_local = bool(self.local_ip)

    async def validate_connection(self) -> bool:
        """Validate connection to AirGradient"""
        try:
            if self.use_local:
                url = f"http://{self.local_ip}/measures/current"
            else:
                url = f"https://api.airgradient.com/public/api/v1/locations/{self.device_id}/measures/current"

            async with aiohttp.ClientSession() as session:
                headers = {"X-API-Key": self.api_key} if self.api_key else {}
                async with session.get(url, headers=headers, timeout=10) as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"AirGradient connection validation failed: {e}")
            return False

    async def collect(self) -> List[Dict[str, Any]]:
        """Collect data from AirGradient sensor"""
        data_points = []

        try:
            if self.use_local:
                url = f"http://{self.local_ip}/measures/current"
            else:
                url = f"https://api.airgradient.com/public/api/v1/locations/{self.device_id}/measures/current"

            async with aiohttp.ClientSession() as session:
                headers = {"X-API-Key": self.api_key} if self.api_key else {}
                async with session.get(url, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()

                        # Parse AirGradient data
                        tags = {"device_id": self.device_id or "local"}

                        # PM2.5
                        if "pm02" in data:
                            data_points.append(self.format_data_point(
                                "air_quality", data["pm02"],
                                tags={**tags, "type": "pm25"}
                            ))

                        # CO2
                        if "rco2" in data:
                            data_points.append(self.format_data_point(
                                "co2", data["rco2"], tags=tags
                            ))

                        # Temperature
                        if "atmp" in data:
                            data_points.append(self.format_data_point(
                                "temperature", data["atmp"],
                                tags={**tags, "unit": "celsius"}
                            ))

                        # Humidity
                        if "rhum" in data:
                            data_points.append(self.format_data_point(
                                "humidity", data["rhum"], tags=tags
                            ))

                        # TVOC
                        if "tvoc" in data:
                            data_points.append(self.format_data_point(
                                "tvoc", data["tvoc"], tags=tags
                            ))

        except Exception as e:
            logger.error(f"Error collecting AirGradient data: {e}")

        return data_points
```

### Step 2.3: Implement GoVee Collector

Create `src/collectors/govee_collector.py`:
```python
import aiohttp
from typing import List, Dict, Any
from .base_collector import BaseCollector
from loguru import logger


class GoveeCollector(BaseCollector):
    """Collector for GoVee sensor data"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__("govee", config)
        self.api_key = config.get("api_key")
        self.device_ids = config.get("device_ids", [])
        self.base_url = "https://developer-api.govee.com/v1"

    async def validate_connection(self) -> bool:
        """Validate connection to GoVee API"""
        try:
            url = f"{self.base_url}/devices"
            headers = {"Govee-API-Key": self.api_key}

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=10) as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"GoVee connection validation failed: {e}")
            return False

    async def collect(self) -> List[Dict[str, Any]]:
        """Collect data from GoVee sensors"""
        data_points = []

        try:
            headers = {"Govee-API-Key": self.api_key}

            async with aiohttp.ClientSession() as session:
                for device_id in self.device_ids:
                    url = f"{self.base_url}/devices/state"
                    params = {"device": device_id}

                    async with session.get(url, headers=headers, params=params, timeout=10) as response:
                        if response.status == 200:
                            data = await response.json()

                            if "data" in data:
                                device_data = data["data"]
                                tags = {"device_id": device_id}

                                # Parse properties
                                for prop in device_data.get("properties", []):
                                    if "temperature" in prop:
                                        data_points.append(self.format_data_point(
                                            "temperature", prop["temperature"],
                                            tags={**tags, "unit": "celsius", "source": "govee"}
                                        ))

                                    if "humidity" in prop:
                                        data_points.append(self.format_data_point(
                                            "humidity", prop["humidity"],
                                            tags={**tags, "source": "govee"}
                                        ))

        except Exception as e:
            logger.error(f"Error collecting GoVee data: {e}")

        return data_points
```

### Step 2.4: Implement Google Nest Collector

Create `src/collectors/nest_collector.py`:
```python
import aiohttp
from typing import List, Dict, Any
from .base_collector import BaseCollector
from loguru import logger
import asyncio


class NestCollector(BaseCollector):
    """Collector for Google Nest thermostat data"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__("nest", config)
        self.access_token = None
        self.refresh_token = config.get("refresh_token")
        self.client_id = config.get("client_id")
        self.client_secret = config.get("client_secret")
        self.device_id = config.get("device_id")
        self.project_id = config.get("project_id")

    async def _refresh_access_token(self):
        """Refresh OAuth access token"""
        try:
            url = "https://oauth2.googleapis.com/token"
            data = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": self.refresh_token,
                "grant_type": "refresh_token"
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=data) as response:
                    if response.status == 200:
                        token_data = await response.json()
                        self.access_token = token_data["access_token"]
                        return True
        except Exception as e:
            logger.error(f"Error refreshing Nest token: {e}")
        return False

    async def validate_connection(self) -> bool:
        """Validate connection to Nest API"""
        if not self.access_token:
            await self._refresh_access_token()

        try:
            url = f"https://smartdevicemanagement.googleapis.com/v1/enterprises/{self.project_id}/devices"
            headers = {"Authorization": f"Bearer {self.access_token}"}

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=10) as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"Nest connection validation failed: {e}")
            return False

    async def collect(self) -> List[Dict[str, Any]]:
        """Collect data from Nest thermostat"""
        data_points = []

        try:
            if not self.access_token:
                await self._refresh_access_token()

            url = f"https://smartdevicemanagement.googleapis.com/v1/enterprises/{self.project_id}/devices/{self.device_id}"
            headers = {"Authorization": f"Bearer {self.access_token}"}

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        traits = data.get("traits", {})
                        tags = {"device_id": self.device_id, "source": "nest"}

                        # Temperature
                        if "sdm.devices.traits.Temperature" in traits:
                            temp_celsius = traits["sdm.devices.traits.Temperature"]["ambientTemperatureCelsius"]
                            data_points.append(self.format_data_point(
                                "temperature", temp_celsius,
                                tags={**tags, "unit": "celsius"}
                            ))

                        # Humidity
                        if "sdm.devices.traits.Humidity" in traits:
                            humidity = traits["sdm.devices.traits.Humidity"]["ambientHumidityPercent"]
                            data_points.append(self.format_data_point(
                                "humidity", humidity, tags=tags
                            ))

                        # Thermostat mode
                        if "sdm.devices.traits.ThermostatMode" in traits:
                            mode = traits["sdm.devices.traits.ThermostatMode"]["mode"]
                            data_points.append(self.format_data_point(
                                "thermostat_mode", 1,
                                tags={**tags, "mode": mode}
                            ))

                        # HVAC status
                        if "sdm.devices.traits.ThermostatHvac" in traits:
                            hvac_status = traits["sdm.devices.traits.ThermostatHvac"]["status"]
                            data_points.append(self.format_data_point(
                                "hvac_status", 1,
                                tags={**tags, "status": hvac_status}
                            ))

                        # Target temperature
                        if "sdm.devices.traits.ThermostatTemperatureSetpoint" in traits:
                            setpoint = traits["sdm.devices.traits.ThermostatTemperatureSetpoint"]
                            if "heatCelsius" in setpoint:
                                data_points.append(self.format_data_point(
                                    "target_temperature", setpoint["heatCelsius"],
                                    tags={**tags, "type": "heat", "unit": "celsius"}
                                ))
                            if "coolCelsius" in setpoint:
                                data_points.append(self.format_data_point(
                                    "target_temperature", setpoint["coolCelsius"],
                                    tags={**tags, "type": "cool", "unit": "celsius"}
                                ))

        except Exception as e:
            logger.error(f"Error collecting Nest data: {e}")

        return data_points
```

### Step 2.5: Implement HomeKit Collector

Create `src/collectors/homekit_collector.py`:
```python
import aiohttp
from typing import List, Dict, Any
from .base_collector import BaseCollector
from loguru import logger


class HomeKitCollector(BaseCollector):
    """Collector for HomeKit devices via Home Assistant"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__("homekit", config)
        self.ha_url = config.get("url")
        self.ha_token = config.get("token")
        self.entity_ids = config.get("entity_ids", [])

    async def validate_connection(self) -> bool:
        """Validate connection to Home Assistant"""
        try:
            url = f"{self.ha_url}/api/"
            headers = {"Authorization": f"Bearer {self.ha_token}"}

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=10) as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"HomeKit connection validation failed: {e}")
            return False

    async def collect(self) -> List[Dict[str, Any]]:
        """Collect data from HomeKit devices"""
        data_points = []

        try:
            url = f"{self.ha_url}/api/states"
            headers = {"Authorization": f"Bearer {self.ha_token}"}

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        states = await response.json()

                        for state in states:
                            entity_id = state["entity_id"]

                            # Filter if entity_ids specified
                            if self.entity_ids and entity_id not in self.entity_ids:
                                continue

                            # Only process sensors with numeric values
                            try:
                                value = float(state["state"])
                            except (ValueError, TypeError):
                                continue

                            tags = {
                                "entity_id": entity_id,
                                "source": "homekit",
                                "friendly_name": state["attributes"].get("friendly_name", entity_id)
                            }

                            # Determine measurement type
                            domain = entity_id.split(".")[0]
                            device_class = state["attributes"].get("device_class", "")
                            unit = state["attributes"].get("unit_of_measurement", "")

                            measurement = device_class or domain
                            if unit:
                                tags["unit"] = unit

                            data_points.append(self.format_data_point(
                                measurement, value, tags=tags
                            ))

        except Exception as e:
            logger.error(f"Error collecting HomeKit data: {e}")

        return data_points
```

### Step 2.6: Implement Utility Data Collector

Create `src/collectors/utility_collector.py`:
```python
import aiohttp
import pandas as pd
from typing import List, Dict, Any
from pathlib import Path
from .base_collector import BaseCollector
from loguru import logger
from datetime import datetime, timedelta


class UtilityCollector(BaseCollector):
    """Collector for utility company data"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__("utility", config)
        self.provider = config.get("provider")
        self.api_key = config.get("api_key")
        self.account_number = config.get("account_number")
        self.csv_path = config.get("csv_path")
        self.use_csv = bool(self.csv_path)

    async def validate_connection(self) -> bool:
        """Validate connection to utility API or CSV file"""
        if self.use_csv:
            return Path(self.csv_path).exists()

        # Implement API validation based on provider
        # This is provider-specific
        return True

    async def collect(self) -> List[Dict[str, Any]]:
        """Collect utility usage data"""
        if self.use_csv:
            return await self._collect_from_csv()
        else:
            return await self._collect_from_api()

    async def _collect_from_csv(self) -> List[Dict[str, Any]]:
        """Collect data from CSV export"""
        data_points = []

        try:
            df = pd.read_csv(self.csv_path)

            # Assuming CSV has columns: timestamp, usage_kwh, cost
            for _, row in df.iterrows():
                timestamp = pd.to_datetime(row["timestamp"])
                tags = {"account": self.account_number, "source": "utility"}

                if "usage_kwh" in row:
                    data_points.append(self.format_data_point(
                        "energy_usage", float(row["usage_kwh"]),
                        tags={**tags, "unit": "kwh"},
                        timestamp=timestamp
                    ))

                if "cost" in row:
                    data_points.append(self.format_data_point(
                        "energy_cost", float(row["cost"]),
                        tags={**tags, "unit": "usd"},
                        timestamp=timestamp
                    ))

        except Exception as e:
            logger.error(f"Error reading utility CSV: {e}")

        return data_points

    async def _collect_from_api(self) -> List[Dict[str, Any]]:
        """Collect data from utility API"""
        data_points = []

        # Example for PG&E Green Button API
        if self.provider == "pge":
            data_points = await self._collect_pge_data()
        elif self.provider == "sce":
            data_points = await self._collect_sce_data()
        # Add more providers as needed

        return data_points

    async def _collect_pge_data(self) -> List[Dict[str, Any]]:
        """Collect from PG&E API (example)"""
        # Implement PG&E-specific API logic
        # This would use their Green Button Connect API
        return []

    async def _collect_sce_data(self) -> List[Dict[str, Any]]:
        """Collect from SCE API (example)"""
        # Implement SCE-specific API logic
        return []
```

### Step 2.7: Create Collector Manager

Create `src/collectors/manager.py`:
```python
import asyncio
from typing import List, Dict, Any
from loguru import logger
from .airgradient_collector import AirGradientCollector
from .govee_collector import GoveeCollector
from .nest_collector import NestCollector
from .homekit_collector import HomeKitCollector
from .utility_collector import UtilityCollector


class CollectorManager:
    """Manages all data collectors"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.collectors = []
        self._initialize_collectors()

    def _initialize_collectors(self):
        """Initialize all enabled collectors"""

        if self.config.get("airgradient", {}).get("enabled"):
            self.collectors.append(
                AirGradientCollector(self.config["airgradient"])
            )

        if self.config.get("govee", {}).get("enabled"):
            self.collectors.append(
                GoveeCollector(self.config["govee"])
            )

        if self.config.get("nest", {}).get("enabled"):
            self.collectors.append(
                NestCollector(self.config["nest"])
            )

        if self.config.get("homekit", {}).get("enabled"):
            self.collectors.append(
                HomeKitCollector(self.config["homekit"])
            )

        if self.config.get("utility", {}).get("enabled"):
            self.collectors.append(
                UtilityCollector(self.config["utility"])
            )

        logger.info(f"Initialized {len(self.collectors)} collectors")

    async def validate_all_connections(self) -> Dict[str, bool]:
        """Validate all collector connections"""
        results = {}

        for collector in self.collectors:
            is_valid = await collector.validate_connection()
            results[collector.name] = is_valid

            if is_valid:
                logger.info(f"✓ {collector.name} connection validated")
            else:
                logger.warning(f"✗ {collector.name} connection failed")

        return results

    async def collect_all(self) -> List[Dict[str, Any]]:
        """Collect data from all collectors"""
        tasks = [collector.run_collection() for collector in self.collectors]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_data = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Collector failed: {result}")
            else:
                all_data.extend(result)

        return all_data
```

---

## Phase 3: Database & Storage

### Step 3.1: Create Storage Interface

Create `src/storage/base_storage.py`:
```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from datetime import datetime


class BaseStorage(ABC):
    """Base class for storage backends"""

    @abstractmethod
    async def connect(self):
        """Connect to storage backend"""
        pass

    @abstractmethod
    async def disconnect(self):
        """Disconnect from storage backend"""
        pass

    @abstractmethod
    async def write_data_points(self, data_points: List[Dict[str, Any]]) -> bool:
        """Write multiple data points"""
        pass

    @abstractmethod
    async def query_data(self, measurement: str, start_time: datetime,
                        end_time: datetime, tags: Dict[str, str] = None) -> List[Dict[str, Any]]:
        """Query data from storage"""
        pass
```

### Step 3.2: Implement InfluxDB Storage

Create `src/storage/influxdb_storage.py`:
```python
from typing import List, Dict, Any
from datetime import datetime
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from .base_storage import BaseStorage
from loguru import logger


class InfluxDBStorage(BaseStorage):
    """InfluxDB storage implementation"""

    def __init__(self, config: Dict[str, Any]):
        self.url = config["url"]
        self.token = config["token"]
        self.org = config["org"]
        self.bucket = config["bucket"]
        self.client = None
        self.write_api = None
        self.query_api = None

    async def connect(self):
        """Connect to InfluxDB"""
        try:
            self.client = InfluxDBClient(
                url=self.url,
                token=self.token,
                org=self.org
            )
            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
            self.query_api = self.client.query_api()
            logger.info("Connected to InfluxDB")
        except Exception as e:
            logger.error(f"Failed to connect to InfluxDB: {e}")
            raise

    async def disconnect(self):
        """Disconnect from InfluxDB"""
        if self.client:
            self.client.close()
            logger.info("Disconnected from InfluxDB")

    async def write_data_points(self, data_points: List[Dict[str, Any]]) -> bool:
        """Write data points to InfluxDB"""
        try:
            points = []
            for dp in data_points:
                point = Point(dp["measurement"]) \
                    .field("value", dp["value"]) \
                    .time(dp["timestamp"])

                for tag_key, tag_value in dp.get("tags", {}).items():
                    point = point.tag(tag_key, tag_value)

                points.append(point)

            self.write_api.write(bucket=self.bucket, org=self.org, record=points)
            logger.debug(f"Wrote {len(points)} points to InfluxDB")
            return True

        except Exception as e:
            logger.error(f"Error writing to InfluxDB: {e}")
            return False

    async def query_data(self, measurement: str, start_time: datetime,
                        end_time: datetime, tags: Dict[str, str] = None) -> List[Dict[str, Any]]:
        """Query data from InfluxDB"""
        try:
            query = f'''
                from(bucket: "{self.bucket}")
                |> range(start: {start_time.isoformat()}Z, stop: {end_time.isoformat()}Z)
                |> filter(fn: (r) => r["_measurement"] == "{measurement}")
            '''

            if tags:
                for key, value in tags.items():
                    query += f'\n  |> filter(fn: (r) => r["{key}"] == "{value}")'

            tables = self.query_api.query(query, org=self.org)

            results = []
            for table in tables:
                for record in table.records:
                    results.append({
                        "timestamp": record.get_time(),
                        "value": record.get_value(),
                        "measurement": measurement,
                        "tags": {k: v for k, v in record.values.items()
                                if k not in ["_time", "_value", "_field", "_measurement"]}
                    })

            return results

        except Exception as e:
            logger.error(f"Error querying InfluxDB: {e}")
            return []
```

---

## Phase 4: Data Processing & Analysis

### Step 4.1: Create Analysis Module

Create `src/analysis/correlation_engine.py`:
```python
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple
from datetime import datetime, timedelta
from scipy import stats
from sklearn.preprocessing import StandardScaler
from loguru import logger


class CorrelationEngine:
    """Analyzes correlations between sensor data and energy usage"""

    def __init__(self, storage):
        self.storage = storage

    async def get_correlated_data(self, start_time: datetime, end_time: datetime) -> pd.DataFrame:
        """Fetch and align all data sources"""

        # Fetch all measurements
        measurements = {
            "temperature": await self.storage.query_data("temperature", start_time, end_time),
            "humidity": await self.storage.query_data("humidity", start_time, end_time),
            "co2": await self.storage.query_data("co2", start_time, end_time),
            "pm25": await self.storage.query_data("air_quality", start_time, end_time),
            "hvac_status": await self.storage.query_data("hvac_status", start_time, end_time),
            "energy_usage": await self.storage.query_data("energy_usage", start_time, end_time),
        }

        # Convert to DataFrames
        dfs = {}
        for name, data in measurements.items():
            if data:
                df = pd.DataFrame(data)
                df["timestamp"] = pd.to_datetime(df["timestamp"])
                df = df.set_index("timestamp")
                dfs[name] = df["value"].resample("15min").mean()

        # Combine all data
        combined_df = pd.DataFrame(dfs)
        combined_df = combined_df.dropna()

        return combined_df

    def calculate_correlations(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate Pearson correlations with energy usage"""

        if "energy_usage" not in df.columns:
            logger.warning("No energy usage data available")
            return {}

        correlations = {}
        for col in df.columns:
            if col != "energy_usage":
                corr, p_value = stats.pearsonr(df[col], df["energy_usage"])
                correlations[col] = {
                    "correlation": corr,
                    "p_value": p_value,
                    "significant": p_value < 0.05
                }

        return correlations

    def identify_energy_drivers(self, df: pd.DataFrame) -> List[Tuple[str, float]]:
        """Identify top factors driving energy usage"""

        correlations = self.calculate_correlations(df)

        # Sort by absolute correlation value
        sorted_factors = sorted(
            correlations.items(),
            key=lambda x: abs(x[1]["correlation"]),
            reverse=True
        )

        return [(factor, data["correlation"]) for factor, data in sorted_factors
                if data["significant"]]

    def detect_anomalies(self, df: pd.DataFrame, column: str, threshold: float = 3.0) -> pd.Series:
        """Detect anomalies using z-score"""

        z_scores = np.abs(stats.zscore(df[column]))
        return df[z_scores > threshold]

    def calculate_energy_efficiency_score(self, df: pd.DataFrame) -> float:
        """Calculate overall energy efficiency score (0-100)"""

        # Normalize temperature delta from comfort zone (68-72°F / 20-22°C)
        temp_comfort = df["temperature"].apply(
            lambda x: max(0, min(abs(x - 20), abs(x - 22)))
        )
        temp_score = (1 - temp_comfort.mean() / 10) * 100

        # Calculate HVAC utilization efficiency
        if "hvac_status" in df.columns:
            hvac_usage = df["hvac_status"].mean()
            hvac_score = (1 - hvac_usage) * 100
        else:
            hvac_score = 50

        # Overall score
        efficiency_score = (temp_score * 0.6 + hvac_score * 0.4)

        return max(0, min(100, efficiency_score))
```

### Step 4.2: Create Report Generator

Create `src/analysis/report_generator.py`:
```python
import pandas as pd
from typing import Dict, Any
from datetime import datetime, timedelta
from loguru import logger
from .correlation_engine import CorrelationEngine


class ReportGenerator:
    """Generates analysis reports"""

    def __init__(self, correlation_engine: CorrelationEngine):
        self.engine = correlation_engine

    async def generate_daily_report(self, date: datetime = None) -> Dict[str, Any]:
        """Generate daily summary report"""

        if date is None:
            date = datetime.now()

        start_time = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(days=1)

        # Fetch data
        df = await self.engine.get_correlated_data(start_time, end_time)

        if df.empty:
            return {"error": "No data available for this date"}

        # Calculate metrics
        correlations = self.engine.calculate_correlations(df)
        drivers = self.engine.identify_energy_drivers(df)
        efficiency_score = self.engine.calculate_energy_efficiency_score(df)

        report = {
            "date": date.strftime("%Y-%m-%d"),
            "summary": {
                "avg_temperature": df["temperature"].mean() if "temperature" in df else None,
                "avg_humidity": df["humidity"].mean() if "humidity" in df else None,
                "total_energy_usage": df["energy_usage"].sum() if "energy_usage" in df else None,
                "efficiency_score": efficiency_score
            },
            "correlations": correlations,
            "top_energy_drivers": drivers[:5],
            "recommendations": self._generate_recommendations(df, drivers)
        }

        return report

    def _generate_recommendations(self, df: pd.DataFrame, drivers: list) -> List[str]:
        """Generate actionable recommendations"""

        recommendations = []

        # Temperature-based recommendations
        if "temperature" in df.columns:
            avg_temp = df["temperature"].mean()
            if avg_temp > 24:
                recommendations.append(
                    "Average temperature is high. Consider raising thermostat cooling setpoint."
                )
            elif avg_temp < 18:
                recommendations.append(
                    "Average temperature is low. Consider lowering thermostat heating setpoint."
                )

        # Humidity-based recommendations
        if "humidity" in df.columns:
            avg_humidity = df["humidity"].mean()
            if avg_humidity > 60:
                recommendations.append(
                    "High humidity detected. Consider using a dehumidifier for comfort and efficiency."
                )
            elif avg_humidity < 30:
                recommendations.append(
                    "Low humidity detected. Consider using a humidifier for comfort."
                )

        # Energy driver recommendations
        if drivers:
            top_driver, corr = drivers[0]
            if abs(corr) > 0.7:
                recommendations.append(
                    f"Strong correlation detected between {top_driver} and energy usage. "
                    f"Focus on optimizing {top_driver} for maximum energy savings."
                )

        return recommendations
```

---

## Phase 5: Visualization Dashboard

### Step 5.1: Create Grafana Dashboard JSON

Create `dashboards/climate_overview.json`:
```json
{
  "dashboard": {
    "title": "Home Climate Overview",
    "timezone": "browser",
    "panels": [
      {
        "title": "Temperature Comparison",
        "type": "timeseries",
        "gridPos": {"x": 0, "y": 0, "w": 12, "h": 8},
        "targets": [
          {
            "query": "from(bucket: \"climate_data\") |> range(start: -24h) |> filter(fn: (r) => r._measurement == \"temperature\")"
          }
        ]
      },
      {
        "title": "Energy Usage",
        "type": "timeseries",
        "gridPos": {"x": 12, "y": 0, "w": 12, "h": 8},
        "targets": [
          {
            "query": "from(bucket: \"climate_data\") |> range(start: -24h) |> filter(fn: (r) => r._measurement == \"energy_usage\")"
          }
        ]
      },
      {
        "title": "Humidity Levels",
        "type": "timeseries",
        "gridPos": {"x": 0, "y": 8, "w": 12, "h": 8},
        "targets": [
          {
            "query": "from(bucket: \"climate_data\") |> range(start: -24h) |> filter(fn: (r) => r._measurement == \"humidity\")"
          }
        ]
      },
      {
        "title": "Air Quality (PM2.5)",
        "type": "gauge",
        "gridPos": {"x": 12, "y": 8, "w": 6, "h": 8},
        "targets": [
          {
            "query": "from(bucket: \"climate_data\") |> range(start: -1h) |> filter(fn: (r) => r._measurement == \"air_quality\") |> mean()"
          }
        ]
      },
      {
        "title": "CO2 Level",
        "type": "gauge",
        "gridPos": {"x": 18, "y": 8, "w": 6, "h": 8},
        "targets": [
          {
            "query": "from(bucket: \"climate_data\") |> range(start: -1h) |> filter(fn: (r) => r._measurement == \"co2\") |> mean()"
          }
        ]
      }
    ]
  }
}
```

### Step 5.2: Create Custom Web API

Create `src/api/main.py`:
```python
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from typing import Optional
from ..storage.influxdb_storage import InfluxDBStorage
from ..analysis.correlation_engine import CorrelationEngine
from ..analysis.report_generator import ReportGenerator
from pydantic import BaseModel
import os


app = FastAPI(title="Home Climate IQ API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
storage = InfluxDBStorage({
    "url": os.getenv("INFLUXDB_URL"),
    "token": os.getenv("INFLUXDB_TOKEN"),
    "org": os.getenv("INFLUXDB_ORG"),
    "bucket": os.getenv("INFLUXDB_BUCKET")
})

correlation_engine = CorrelationEngine(storage)
report_generator = ReportGenerator(correlation_engine)


@app.on_event("startup")
async def startup():
    await storage.connect()


@app.on_event("shutdown")
async def shutdown():
    await storage.disconnect()


@app.get("/api/v1/data/{measurement}")
async def get_data(
    measurement: str,
    hours: int = 24,
    tags: Optional[str] = None
):
    """Get sensor data"""
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=hours)

    tag_dict = {}
    if tags:
        for tag in tags.split(","):
            key, value = tag.split("=")
            tag_dict[key] = value

    data = await storage.query_data(measurement, start_time, end_time, tag_dict)
    return {"data": data}


@app.get("/api/v1/correlations")
async def get_correlations(days: int = 7):
    """Get correlation analysis"""
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=days)

    df = await correlation_engine.get_correlated_data(start_time, end_time)
    correlations = correlation_engine.calculate_correlations(df)

    return {"correlations": correlations}


@app.get("/api/v1/report/daily")
async def get_daily_report(date: Optional[str] = None):
    """Get daily report"""
    report_date = datetime.fromisoformat(date) if date else datetime.now()
    report = await report_generator.generate_daily_report(report_date)
    return report


@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
```

---

## Phase 6: Correlation Engine

### Step 6.1: Advanced Correlation Analysis

Create `src/analysis/advanced_correlations.py`:
```python
import pandas as pd
import numpy as np
from typing import Dict, List
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler


class AdvancedCorrelationAnalysis:
    """Advanced correlation and feature importance analysis"""

    def __init__(self):
        self.scaler = StandardScaler()
        self.model = None

    def feature_importance_analysis(self, df: pd.DataFrame) -> Dict[str, float]:
        """Use Random Forest to determine feature importance"""

        if "energy_usage" not in df.columns:
            return {}

        # Prepare features and target
        features = df.drop(columns=["energy_usage"])
        target = df["energy_usage"]

        # Scale features
        features_scaled = self.scaler.fit_transform(features)

        # Train Random Forest
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.model.fit(features_scaled, target)

        # Get feature importances
        importance_dict = dict(zip(features.columns, self.model.feature_importances_))

        # Sort by importance
        sorted_importance = dict(
            sorted(importance_dict.items(), key=lambda x: x[1], reverse=True)
        )

        return sorted_importance

    def time_lag_correlation(self, df: pd.DataFrame, feature: str,
                            target: str = "energy_usage", max_lag: int = 24) -> Dict[int, float]:
        """Calculate correlation with different time lags"""

        lag_correlations = {}

        for lag in range(0, max_lag + 1):
            if lag == 0:
                shifted = df[feature]
            else:
                shifted = df[feature].shift(lag)

            # Calculate correlation
            corr = shifted.corr(df[target])
            lag_correlations[lag] = corr

        return lag_correlations

    def seasonal_decomposition(self, df: pd.DataFrame, column: str) -> Dict[str, pd.Series]:
        """Decompose time series into trend, seasonal, and residual components"""

        from statsmodels.tsa.seasonal import seasonal_decompose

        result = seasonal_decompose(df[column], model='additive', period=96)  # 15-min intervals = 96 per day

        return {
            "trend": result.trend,
            "seasonal": result.seasonal,
            "residual": result.resid
        }
```

---

## Phase 7: Testing & Deployment

### Step 7.1: Create Tests

Create `tests/test_collectors.py`:
```python
import pytest
from src.collectors.airgradient_collector import AirGradientCollector


@pytest.mark.asyncio
async def test_airgradient_collector():
    config = {
        "local_ip": "192.168.1.100",
        "enabled": True
    }

    collector = AirGradientCollector(config)
    assert collector.name == "airgradient"

    # Test data collection (mocked)
    # Add mock tests here
```

### Step 7.2: Create Main Application

Create `src/main.py`:
```python
import asyncio
import os
from datetime import datetime
from loguru import logger
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from collectors.manager import CollectorManager
from storage.influxdb_storage import InfluxDBStorage
from analysis.correlation_engine import CorrelationEngine
from analysis.report_generator import ReportGenerator

# Load environment variables
load_dotenv()

# Configure logging
logger.add("logs/climate_iq_{time}.log", rotation="1 day", retention="30 days")


class HomeClimateIQ:
    """Main application class"""

    def __init__(self):
        self.config = self._load_config()
        self.storage = InfluxDBStorage(self.config["database"])
        self.collector_manager = CollectorManager(self.config["collectors"])
        self.correlation_engine = CorrelationEngine(self.storage)
        self.report_generator = ReportGenerator(self.correlation_engine)
        self.scheduler = AsyncIOScheduler()

    def _load_config(self) -> dict:
        """Load configuration from environment variables"""
        return {
            "database": {
                "url": os.getenv("INFLUXDB_URL"),
                "token": os.getenv("INFLUXDB_TOKEN"),
                "org": os.getenv("INFLUXDB_ORG"),
                "bucket": os.getenv("INFLUXDB_BUCKET")
            },
            "collectors": {
                "airgradient": {
                    "enabled": os.getenv("AIRGRADIENT_API_KEY") or os.getenv("AIRGRADIENT_LOCAL_IP"),
                    "api_key": os.getenv("AIRGRADIENT_API_KEY"),
                    "device_id": os.getenv("AIRGRADIENT_DEVICE_ID"),
                    "local_ip": os.getenv("AIRGRADIENT_LOCAL_IP")
                },
                "govee": {
                    "enabled": bool(os.getenv("GOVEE_API_KEY")),
                    "api_key": os.getenv("GOVEE_API_KEY"),
                    "device_ids": os.getenv("GOVEE_DEVICE_IDS", "").split(",")
                },
                "nest": {
                    "enabled": bool(os.getenv("NEST_CLIENT_ID")),
                    "client_id": os.getenv("NEST_CLIENT_ID"),
                    "client_secret": os.getenv("NEST_CLIENT_SECRET"),
                    "refresh_token": os.getenv("NEST_REFRESH_TOKEN"),
                    "device_id": os.getenv("NEST_DEVICE_ID"),
                    "project_id": os.getenv("NEST_PROJECT_ID")
                },
                "homekit": {
                    "enabled": bool(os.getenv("HOMEKIT_URL")),
                    "url": os.getenv("HOMEKIT_URL"),
                    "token": os.getenv("HOMEKIT_TOKEN"),
                    "entity_ids": os.getenv("HOMEKIT_ENTITY_IDS", "").split(",")
                },
                "utility": {
                    "enabled": bool(os.getenv("UTILITY_API_KEY") or os.getenv("UTILITY_DATA_PATH")),
                    "provider": os.getenv("UTILITY_PROVIDER"),
                    "api_key": os.getenv("UTILITY_API_KEY"),
                    "account_number": os.getenv("UTILITY_ACCOUNT_NUMBER"),
                    "csv_path": os.getenv("UTILITY_DATA_PATH")
                }
            }
        }

    async def collect_data(self):
        """Collect data from all sources"""
        logger.info("Starting data collection cycle")

        data_points = await self.collector_manager.collect_all()

        if data_points:
            success = await self.storage.write_data_points(data_points)
            if success:
                logger.info(f"Successfully stored {len(data_points)} data points")
            else:
                logger.error("Failed to store data points")

    async def generate_daily_report(self):
        """Generate and log daily report"""
        logger.info("Generating daily report")

        report = await self.report_generator.generate_daily_report()
        logger.info(f"Daily Report: {report}")

    async def start(self):
        """Start the application"""
        logger.info("Starting Home Climate IQ")

        # Connect to database
        await self.storage.connect()

        # Validate all collectors
        validation_results = await self.collector_manager.validate_all_connections()
        logger.info(f"Collector validation: {validation_results}")

        # Schedule data collection
        collection_interval = int(os.getenv("DATA_COLLECTION_INTERVAL", 300))
        self.scheduler.add_job(
            self.collect_data,
            'interval',
            seconds=collection_interval,
            id='data_collection'
        )

        # Schedule daily report
        self.scheduler.add_job(
            self.generate_daily_report,
            'cron',
            hour=0,
            minute=0,
            id='daily_report'
        )

        # Start scheduler
        self.scheduler.start()
        logger.info("Application started successfully")

        # Keep running
        try:
            while True:
                await asyncio.sleep(1)
        except (KeyboardInterrupt, SystemExit):
            logger.info("Shutting down...")
            await self.storage.disconnect()


if __name__ == "__main__":
    app = HomeClimateIQ()
    asyncio.run(app.start())
```

### Step 7.3: Create Deployment Script

Create `deploy.sh`:
```bash
#!/bin/bash

echo "Deploying Home Climate IQ..."

# Build Docker images
docker-compose build

# Start services
docker-compose up -d

# Wait for InfluxDB to be ready
echo "Waiting for InfluxDB to be ready..."
sleep 10

# Check service health
docker-compose ps

echo "Deployment complete!"
echo "Access Grafana at http://localhost:3000 (admin/admin)"
echo "Access InfluxDB at http://localhost:8086"
echo "Access API at http://localhost:8000/docs"
```

---

## Appendix: API References

### AirGradient API
- **Documentation**: https://api-docs.airgradient.com/
- **Local API**: Most AirGradient devices expose a local HTTP API at `http://<device-ip>/measures/current`

### GoVee API
- **Documentation**: https://govee-public.s3.amazonaws.com/developer-docs/GoveeDeveloperAPIReference.pdf
- **Get API Key**: https://developer.govee.com

### Google Nest API
- **Documentation**: https://developers.google.com/nest/device-access
- **Device Access Console**: https://console.nest.google.com/device-access
- **OAuth Setup**: Follow the Device Access registration process

### HomeKit via Home Assistant
- **Home Assistant**: https://www.home-assistant.io
- **API Documentation**: https://developers.home-assistant.io/docs/api/rest

### Utility Company APIs
- **PG&E Green Button**: https://www.pge.com/en_US/residential/save-energy-money/analyze-your-usage/your-usage/view-and-share-your-data-green-button/green-button-frequently-asked-questions.page
- **SCE**: https://www.sce.com/residential/rebates-savings/usage-data

---

## Quick Start Summary

1. **Clone and setup**:
   ```bash
   git clone <your-repo>
   cd homeclimate_iq
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env
   ```

2. **Configure credentials** in `.env`

3. **Start services**:
   ```bash
   chmod +x deploy.sh
   ./deploy.sh
   ```

4. **Verify data collection**:
   ```bash
   docker-compose logs -f app
   ```

5. **Access dashboards**:
   - Grafana: http://localhost:3000
   - API Docs: http://localhost:8000/docs

---

## Next Steps

- [ ] Set up each sensor integration one at a time
- [ ] Test data collection for each source
- [ ] Configure Grafana dashboards
- [ ] Set up automated backups
- [ ] Configure alerts for anomalies
- [ ] Build custom visualizations
- [ ] Implement machine learning predictions (optional)
