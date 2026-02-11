# Home Climate IQ

A comprehensive multi-sensor correlation tool that integrates data from various climate sensors and correlates it with utility company data to identify energy usage trends and optimization opportunities.

## Features

- **Multi-Sensor Integration**: Collect data from AirGradient, GoVee, Google Nest, and HomeKit devices
- **Utility Data Correlation**: Link sensor data with energy consumption from utility companies
- **Advanced Analytics**: Identify correlations, trends, and energy-saving opportunities
- **Real-time Monitoring**: Continuous data collection and storage
- **Beautiful Dashboards**: Visualize your data with Grafana and custom web interfaces
- **Actionable Insights**: Automated recommendations based on data analysis

## Supported Devices

- **AirGradient** - Air quality monitoring (PM2.5, CO2, TVOC, temperature, humidity)
- **GoVee Sensors** - Temperature and humidity sensors
- **Google Nest Thermostat** - HVAC status, setpoints, and climate control
- **HomeKit Devices** - Any HomeKit-compatible sensors via Home Assistant
- **Utility Companies** - Energy usage data via API or CSV import

## Quick Start

See the comprehensive [IMPLEMENTATION_GUIDE.md](./IMPLEMENTATION_GUIDE.md) for detailed step-by-step instructions.

### Prerequisites

- Python 3.9+
- Docker and Docker Compose
- API keys for your sensors and services

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/homeclimate_iq.git
cd homeclimate_iq

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys and credentials

# Start services
docker-compose up -d
```

### Access Points

- **Grafana Dashboard**: http://localhost:3000 (default: admin/admin)
- **InfluxDB**: http://localhost:8086
- **API Documentation**: http://localhost:8000/docs

## Architecture

```
Data Sources → Collectors → Time-Series DB → Analysis Engine → Dashboards
```

The system continuously collects data from all configured sensors, stores it in InfluxDB, and provides real-time analysis and visualizations through Grafana and a custom API.

## Documentation

- [Implementation Guide](./IMPLEMENTATION_GUIDE.md) - Complete setup instructions
- [API Documentation](http://localhost:8000/docs) - Interactive API docs (when running)

## Project Structure

```
homeclimate_iq/
├── src/
│   ├── collectors/          # Sensor data collectors
│   ├── storage/             # Database interfaces
│   ├── analysis/            # Correlation and analysis engines
│   ├── api/                 # REST API
│   └── utils/               # Utility functions
├── config/                  # Configuration files
├── data/                    # Data storage
├── dashboards/              # Grafana dashboards
├── tests/                   # Unit tests
├── docker-compose.yml       # Container orchestration
└── requirements.txt         # Python dependencies
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see LICENSE file for details

## Support

For issues and questions, please open an issue on GitHub.