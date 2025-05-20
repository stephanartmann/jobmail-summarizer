# Job Monitoring System

[![Build Status](http://your-jenkins-server/job/your-job/badge/icon)](http://your-jenkins-server/job/your-job/)
[![Coverage](https://img.shields.io/jenkins/coverage/jacoco/your-job/main.svg)](http://your-jenkins-server/job/your-job/lastBuild/jacoco/)

This system automatically monitors your email for new job listings, processes them, and sends a summarized report to your specified email address.

This system automatically monitors your email for new job listings, processes them, and sends a summarized report to your specified email address.

## CI/CD with Jenkins

This project includes a Jenkins pipeline for continuous integration and deployment. The pipeline includes the following stages:

1. **Checkout**: Fetches the latest code from the repository
2. **Build**: Builds the Docker image
3. **Test**: Runs unit and integration tests with coverage reporting
4. **Push to Registry**: Pushes the built image to a container registry (on main branch)
5. **Deploy**: Deploys the application (on main branch)

### Jenkins Setup

1. **Prerequisites**:
   - Jenkins server with Docker and Docker Pipeline plugins installed
   - Docker installed on the Jenkins agent
   - Credentials configured in Jenkins for:
     - Docker registry access
     - Any deployment keys/secrets

2. **Configure Jenkins Job**:
   - Create a new Pipeline job
   - Set the Pipeline definition to "Pipeline script from SCM"
   - Configure your repository URL and credentials
   - Set the script path to `Jenkinsfile`

3. **Environment Variables**:
   The following environment variables need to be set in Jenkins:
   - `DOCKER_REGISTRY`: Your Docker registry URL
   - `DOCKER_CREDENTIALS_ID`: Jenkins credentials ID for Docker registry
   - Any application-specific environment variables from `.env.example`

4. **Build Triggers**:
   - Configure webhooks in your repository to trigger builds on push
   - Or set up polling in the Jenkins job configuration

## Local Development Setup Instructions

### Using Dev Container

1. Open the Command Palette (Ctrl+Shift+P) and run:
   - "Dev Containers: Reopen in Container" (if you already have the project open)
   - OR "Dev Containers: Open Folder in Container" (if you want to open a new folder in a container)

2. The container will automatically:
   - Build the development environment
   - Install all dependencies
   - Configure VS Code extensions
   - Set up Chrome and ChromeDriver for Selenium

### Manual Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Copy the `.env.example` file to `.env` and update the values:
```bash
cp .env.example .env
```
Then edit the `.env` file with your actual values. The `.env.example` file contains all required and optional configuration variables with placeholder values.

3. Set up Gmail API:
   - Go to Google Cloud Console (https://console.cloud.google.com/)
   - Create a new project
   - Enable Gmail API
   - Create credentials (OAuth 2.0 Client IDs)
   - Download the credentials.json file and place it in the project root

4. Run the script:
```bash
python job_monitor.py
```

## On-Premises Deployment

### Prerequisites

1. A server with:
   - Docker and Docker Compose installed
   - SSH access
   - Sufficient resources to run your application

### Automated Deployment with Jenkins

The Jenkins pipeline is configured to automatically deploy to your on-premises server when changes are pushed to the `main` branch.

### Manual Deployment

For manual deployments, you can use the `deploy-to-onprem.sh` script:

1. First, create a `.env.prod` file with your production environment variables:
   ```bash
   cp .env .env.prod
   # Edit .env.prod with your production values
   ```

2. Update the deployment script with your server details:
   ```bash
   # Edit these variables at the top of deploy-to-onprem.sh
   REMOTE_USER="your-ssh-user"
   REMOTE_HOST="your-onprem-server-ip-or-hostname"
   REMOTE_APP_DIR="/path/to/your/app"
   ```

3. Run the deployment script:
   ```bash
   ./deploy-to-onprem.sh
   ```

### Updating the Application

To update the application:

1. Push your changes to the repository
2. The Jenkins pipeline will automatically:
   - Build and test the application
   - Deploy to your on-premises server
   - Restart the containers with the new version

## Development

### Testing

Run tests locally:
```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Run tests with coverage
pytest tests/ -v --cov=. --cov-report=html
```

## Features

- Automatically checks for new emails
- Extracts job listing links from emails
- Uses OpenAI's GPT to summarize job listings
- Creates a formatted summary table
- Sends summaries to specified email address
- Handles LinkedIn authentication for protected job listings

## Configuration

All configuration is done through the `.env` file. The main settings are:

- OpenAI API Configuration
- Gmail API Configuration
- Email Configuration (for sending summaries)
- LinkedIn Configuration (for job listings)
- Optional Configuration (check interval, max emails to process)
- Logging Configuration

## Note

- For Gmail, you'll need to use an App Password instead of your regular password
- The script needs to be run periodically (e.g., using cron) to check for new emails
- Make sure to handle your API keys and passwords securely
- The `.env` file should never be committed to version control
