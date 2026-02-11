# Getting Started with Home Climate IQ

This is a quick reference guide. For detailed instructions, see [IMPLEMENTATION_GUIDE.md](./IMPLEMENTATION_GUIDE.md).

## What You'll Need

### Hardware
- [ ] AirGradient sensor (connected to your network)
- [ ] GoVee temperature/humidity sensors
- [ ] Google Nest thermostat
- [ ] HomeKit-compatible devices
- [ ] A computer or Raspberry Pi to run the system

### Software & Accounts
- [ ] Python 3.9 or higher
- [ ] Docker Desktop (or Docker + Docker Compose)
- [ ] Git

### API Keys & Credentials
You'll need to obtain:

1. **AirGradient**: Device IP address or API key
   - Local: Find your device IP in your router
   - Cloud: Get API key from AirGradient dashboard

2. **GoVee**: Developer API key
   - Sign up at https://developer.govee.com
   - Get your API key from the developer portal

3. **Google Nest**: OAuth credentials
   - Create project at https://console.nest.google.com/device-access
   - Enable Device Access API ($5 one-time fee)
   - Create OAuth credentials

4. **HomeKit**: Home Assistant setup
   - Install Home Assistant: https://www.home-assistant.io
   - Get long-lived access token from your profile

5. **Utility Company**: API access or data export
   - Check if your utility offers an API (Green Button, etc.)
   - Alternative: Download CSV exports of your usage

## Installation Steps

### 1. Install Prerequisites

```bash
# Install Python 3.9+ (if not already installed)
python3 --version

# Install Docker
# Visit https://docs.docker.com/get-docker/
docker --version
docker-compose --version

# Install Git (if not already installed)
git --version
```

### 2. Clone and Setup Project

```bash
# Clone the repository
git clone https://github.com/yourusername/homeclimate_iq.git
cd homeclimate_iq

# Create Python virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
```

### 3. Configure Your Sensors

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your favorite editor
nano .env  # or vim, code, etc.
```

Fill in your credentials in the `.env` file:

```bash
# AirGradient - Use either API or local IP
AIRGRADIENT_LOCAL_IP=192.168.1.xxx  # Recommended for local access
# OR
AIRGRADIENT_API_KEY=your_api_key
AIRGRADIENT_DEVICE_ID=your_device_id

# GoVee
GOVEE_API_KEY=your_govee_api_key
GOVEE_DEVICE_IDS=device1,device2  # Comma-separated if multiple

# Google Nest
NEST_PROJECT_ID=your_project_id
NEST_CLIENT_ID=your_client_id
NEST_CLIENT_SECRET=your_client_secret
NEST_DEVICE_ID=your_thermostat_id

# HomeKit (via Home Assistant)
HOMEKIT_URL=http://homeassistant.local:8123
HOMEKIT_TOKEN=your_long_lived_token

# Utility Company
UTILITY_PROVIDER=pge  # or your provider
# Use API:
UTILITY_API_KEY=your_api_key
# OR use CSV:
UTILITY_DATA_PATH=./data/raw/utility_data.csv

# Database (InfluxDB)
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=my-super-secret-token
INFLUXDB_ORG=home_climate
INFLUXDB_BUCKET=climate_data
```

### 4. Start the System

```bash
# Start all services with Docker Compose
docker-compose up -d

# Check that everything is running
docker-compose ps

# View logs
docker-compose logs -f app
```

### 5. Access Your Dashboards

Open your browser and visit:

- **Grafana**: http://localhost:3000
  - Username: `admin`
  - Password: `admin` (you'll be prompted to change this)

- **InfluxDB**: http://localhost:8086
  - Use the token from your `.env` file

- **API Docs**: http://localhost:8000/docs
  - Interactive API documentation

## Verifying Data Collection

### Check if data is being collected:

```bash
# View application logs
docker-compose logs -f app

# You should see messages like:
# "Starting collection for airgradient"
# "Collected 5 data points from airgradient"
# "Successfully stored 15 data points"
```

### Query data directly:

```bash
# Access InfluxDB container
docker-compose exec influxdb influx

# Run a query
> use climate_data
> SELECT * FROM temperature LIMIT 10
```

### Check the API:

Visit http://localhost:8000/api/v1/health in your browser.

## Setting Up Grafana Dashboard

1. Log into Grafana (http://localhost:3000)
2. Go to Configuration → Data Sources
3. Add InfluxDB data source:
   - URL: `http://influxdb:8086`
   - Token: Your `INFLUXDB_TOKEN` from `.env`
   - Organization: `home_climate`
   - Default Bucket: `climate_data`
4. Click "Save & Test"

5. Import dashboard:
   - Go to Dashboards → Import
   - Upload `dashboards/climate_overview.json`

## Troubleshooting

### No data appearing?

1. Check collector logs:
   ```bash
   docker-compose logs app | grep -i error
   ```

2. Verify API credentials are correct in `.env`

3. Test individual sensors:
   ```bash
   # For AirGradient local:
   curl http://192.168.1.xxx/measures/current

   # For GoVee:
   curl -H "Govee-API-Key: YOUR_KEY" https://developer-api.govee.com/v1/devices
   ```

4. Check network connectivity from Docker container

### Grafana can't connect to InfluxDB?

- Make sure you're using `http://influxdb:8086` (the service name, not localhost)
- Verify the InfluxDB token is correct
- Check that both containers are running: `docker-compose ps`

### Port already in use?

If ports 3000, 8000, or 8086 are already used:

Edit `docker-compose.yml` and change the port mappings:
```yaml
ports:
  - "3001:3000"  # Change 3000 to another port
```

## Next Steps

1. **Customize Your Dashboard**
   - Add panels for specific sensors
   - Create custom visualizations
   - Set up alerts for anomalies

2. **Schedule Reports**
   - Daily summary emails
   - Weekly trend analysis
   - Monthly efficiency reports

3. **Optimize Data Collection**
   - Adjust collection intervals
   - Filter specific sensors
   - Add more data sources

4. **Advanced Analysis**
   - Set up correlation tracking
   - Enable machine learning predictions
   - Create custom analysis scripts

## Getting Help

- Check the [IMPLEMENTATION_GUIDE.md](./IMPLEMENTATION_GUIDE.md) for detailed instructions
- Review sensor documentation in the guide's appendix
- Open an issue on GitHub for bugs or questions

## Stopping the System

```bash
# Stop all services
docker-compose down

# Stop and remove all data (WARNING: deletes database!)
docker-compose down -v
```

## Regular Maintenance

```bash
# View logs
docker-compose logs -f

# Restart a service
docker-compose restart app

# Update to latest code
git pull
docker-compose build
docker-compose up -d

# Backup database
docker-compose exec influxdb influx backup /tmp/backup
docker cp $(docker-compose ps -q influxdb):/tmp/backup ./backups/
```
