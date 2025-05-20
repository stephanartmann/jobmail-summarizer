pipeline {
    agent any
    
    environment {
        // These will be set in Jenkins credentials
        DOCKER_REGISTRY = credentials('docker-registry')
        DOCKER_CREDENTIALS_ID = 'docker-credentials'
        
        // Test reports directory
        JUNIT_REPORT_PATH = 'reports/junit.xml'
    }
    
    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timeout(time: 30, unit: 'MINUTES')
        disableConcurrentBuilds()
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
                // Clean workspace
                cleanWs()
            }
        }
        
        stage('Setup Environment') {
            steps {
                script {
                    // Create reports directory
                    sh 'mkdir -p reports'
                }
            }
        }
        
        stage('Build & Test') {
            steps {
                script {
                    // Build the Docker image with Jenkins-specific Dockerfile
                    def testImage = docker.build(
                        "job-mail-summarizer-test:${env.BUILD_NUMBER}",
                        "-f Dockerfile.jenkins ."
                    )
                    
                    // Run tests in the container
                    testImage.inside(
                        // Mount the reports directory
                        "-v ${env.WORKSPACE}/reports:/app/reports"
                    ) {
                        // Run tests with coverage and JUnit output
                        sh '''
                        python -m pytest tests/ \
                            -v \
                            --junitxml=${JUNIT_REPORT_PATH} \
                            --cov=. \
                            --cov-report=xml:reports/coverage.xml
                        '''
                    }
                }
            }
            post {
                always {
                    // Always publish test results
                    junit allowEmptyResults: true, testResults: 'reports/*.xml'
                    // Publish coverage report if it exists
                    script {
                        if (fileExists('reports/coverage.xml')) {
                            publishCoverage adapters: [coberturaAdapter('reports/coverage.xml')]
                        }
                    }
                }
            }
        }
        
        stage('Build Production Image') {
            when {
                branch 'main'
            }
            steps {
                script {
                    // Build the production Docker image
                    docker.build(
                        "${DOCKER_REGISTRY}/job-mail-summarizer:${env.BUILD_NUMBER}",
                        "-f Dockerfile ."
                    )
                }
            }
        }
        
        stage('Push to Registry') {
            when {
                branch 'main'
            }
            steps {
                script {
                    // Log in to Docker registry
                    docker.withRegistry('https://index.docker.io/v1/', DOCKER_CREDENTIALS_ID) {
                        // Push the built image
                        docker.image("${DOCKER_REGISTRY}/job-mail-summarizer:${env.BUILD_NUMBER}").push()
                        // Also tag as latest
                        docker.image("${DOCKER_REGISTRY}/job-mail-summarizer:${env.BUILD_NUMBER}").push('latest')
                    }
                }
            }
        }
        
        stage('Deploy to On-Prem') {
            when {
                branch 'main'
            }
            steps {
                script {
                    // SSH into the on-prem server and deploy
                    def remote = [:]
                    remote.name = 'on-prem-server'
                    remote.host = 'your-onprem-server-ip-or-hostname'
                    remote.user = 'your-ssh-user'
                    remote.identityFile = '/path/to/ssh/private/key'
                    remote.allowAnyHosts = true
                    
                    // Create deployment script
                    def deployScript = '''#!/bin/bash
                    # Navigate to app directory
                    cd /path/to/your/app
                    
                    # Pull the latest image
                    docker-compose pull
                    
                    # Stop and remove existing containers
                    docker-compose down
                    
                    # Start new containers
                    docker-compose up -d
                    
                    # Clean up old images
                    docker image prune -f
                    '''
                    
                    // Write script to file
                    writeFile file: 'deploy.sh', text: deployScript
                    
                    // Copy files to server
                    sshPut remote: remote, from: 'docker-compose.yml', into: '/path/to/your/app/'
                    sshPut remote: remote, from: 'deploy.sh', into: '/path/to/your/app/'
                    
                    // Make script executable and run it
                    sshCommand remote: remote, command: 'chmod +x /path/to/your/app/deploy.sh'
                    sshCommand remote: remote, command: 'cd /path/to/your/app/ && ./deploy.sh'
                }
            }
        }
    }
    
    post {
        always {
            // Clean up workspace
            cleanWs()
            
            // Clean up Docker images
            script {
                try {
                    sh 'docker system prune -f'
                } catch (e) {
                    echo 'Failed to clean up Docker: ' + e.toString()
                }
            }
        }
        success {
            echo 'Pipeline completed successfully!'
        }
        failure {
            echo 'Pipeline failed!'
            // Add notification here (e.g., email, Slack)
        }
    }
}
