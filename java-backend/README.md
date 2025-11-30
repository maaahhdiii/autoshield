# AutoShield Java Backend

Production-ready Spring Boot backend for AutoShield security platform.

## Features

- **Spring Boot 3.2** with Java 17
- **PostgreSQL** database with JPA/Hibernate
- **RESTful API** for security operations
- **JWT Authentication** ready
- **MCP Integration** with Python AI and Kali modules
- **Health Monitoring** and metrics
- **Docker support**

## Architecture

```
com.autoshield
├── config/          # Security, WebClient configuration
├── controller/      # REST API endpoints
├── dto/            # Data Transfer Objects
├── entity/         # JPA entities
├── repository/     # Spring Data repositories
└── service/        # Business logic
```

## API Endpoints

### Alerts
- `GET /api/alerts` - List all alerts
- `POST /api/alerts` - Create new alert
- `GET /api/alerts/{id}` - Get alert by ID
- `PUT /api/alerts/{id}/status` - Update alert status
- `PUT /api/alerts/{id}/acknowledge` - Acknowledge alert
- `DELETE /api/alerts/{id}` - Delete alert

### Threats
- `GET /api/threats` - List all threats
- `POST /api/threats` - Create new threat
- `GET /api/threats/{id}` - Get threat by ID
- `PUT /api/threats/{id}/status` - Update threat status
- `PUT /api/threats/{id}/mitigate` - Apply mitigation
- `DELETE /api/threats/{id}` - Delete threat

### Scans
- `GET /api/scans` - List all scans
- `POST /api/scans` - Initiate new scan
- `GET /api/scans/{id}` - Get scan by ID
- `PUT /api/scans/{id}/cancel` - Cancel scan
- `PUT /api/scans/{id}/results` - Update scan results
- `DELETE /api/scans/{id}` - Delete scan

### Dashboard
- `GET /api/dashboard` - Get dashboard statistics and health

### Health
- `GET /api/health` - Service health check

## Configuration

Environment variables in `.env`:
```env
DB_HOST=postgres
DB_PORT=5432
DB_NAME=autoshield
DB_USER=autoshield
DB_PASSWORD=autoshield_secure_pass

SERVER_PORT=8080
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123

PYTHON_AI_URL=http://python-ai:8000
KALI_MCP_URL=http://kali-mcp:8001

JWT_SECRET=your-secret-key-minimum-256-bits
```

## Local Development

### Prerequisites
- Java 17+
- Maven 3.9+
- PostgreSQL 14+

### Run locally
```bash
# Build
mvn clean package

# Run
java -jar target/autoshield-backend-2.0.0.jar

# Or with Maven
mvn spring-boot:run
```

### Docker Build
```bash
# Build image
docker build -t autoshield-backend:2.0.0 .

# Run container
docker run -p 8080:8080 \
  -e DB_HOST=postgres \
  -e DB_USER=autoshield \
  -e DB_PASSWORD=secret \
  autoshield-backend:2.0.0
```

## Testing

```bash
# Run tests
mvn test

# Run with coverage
mvn test jacoco:report
```

## Database Schema

The application uses JPA with automatic schema generation (`ddl-auto: update`).

Main entities:
- **Alert** - Security alerts with severity and status
- **Threat** - Detected threats with mitigation info
- **Scan** - Security scans with results
- **Configuration** - System configuration

## Security

- **HTTP Basic Auth** for API access
- **CORS** enabled for frontend
- **Stateless** session management
- **BCrypt** password encoding
- **JWT** ready for token-based auth

Default credentials:
- Username: `admin`
- Password: `admin123`

**⚠️ Change default credentials in production!**

## Monitoring

Spring Boot Actuator endpoints:
- `/actuator/health` - Health status
- `/actuator/metrics` - Application metrics
- `/actuator/info` - Application info

## Integration with MCP Servers

The backend communicates with:
1. **Python AI** (port 8000) - Threat analysis
2. **Kali MCP** (port 8001) - Security scanning

WebClient configured with timeouts and resilience.

## Production Considerations

1. **Database**: Use managed PostgreSQL in production
2. **Secrets**: Use vault or secrets manager
3. **Logging**: Configure centralized logging
4. **Monitoring**: Enable Prometheus metrics
5. **Scaling**: Stateless design allows horizontal scaling

## License

MIT License - See LICENSE file
