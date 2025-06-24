pipeline {
    agent { label 'local-docker' } 
    
    environment {
        // Test reports directory
        JUNIT_REPORT_PATH = 'reports/junit.xml'
        
        // Local image tags
        BASE_IMAGE = "job-mail-summarizer-base:local"
        TEST_IMAGE = "job-mail-summarizer-test:local"
        PROD_IMAGE = "job-mail-summarizer:local"
    }
    
    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timeout(time: 30, unit: 'MINUTES')
        disableConcurrentBuilds()
    }
    
    stages {
        stage('Checkout') {
            steps {
                echo "[DEBUG] Starting Checkout stage"
                checkout scm
                // Removed cleanWs() from here as it's handled in the post section
                echo "[DEBUG] Checkout completed"
            }
            post {
                success { echo '✅ Checkout stage succeeded' }
                failure { echo '❌ Checkout stage failed' }
            }
        }
        
        stage('Setup Environment') {
            steps {
                echo "[DEBUG] Starting Setup Environment stage"
                script {
                    // Create reports directory
                    sh 'mkdir -p reports'
                    echo "[DEBUG] Created reports directory"
                }
                echo "[DEBUG] Setup Environment completed"
            }
            post {
                success { echo '✅ Setup Environment stage succeeded' }
                failure { echo '❌ Setup Environment stage failed' }
            }
        }
        
        stage('Build Base Image') {
            steps {
                echo "[DEBUG] Starting Build Base Image stage"
                script {
                    // Build the base Docker image locally
                    docker.build(env.BASE_IMAGE, "-f Dockerfile.base .")
                    echo "[DEBUG] Base image built locally"
                }
                echo "[DEBUG] Build Base Image completed"
            }
            post {
                success { echo '✅ Build Base Image stage succeeded' }
                failure { echo '❌ Build Base Image stage failed' }
            }
        }
        
        stage('Build & Test') {
            steps {
                echo "[DEBUG] Starting Build & Test stage"
                script {
                    // Build the test image using the base image
                    def testImage = docker.build(
                        env.TEST_IMAGE,
                        "--build-arg BASE_IMAGE=${env.BASE_IMAGE} -f Dockerfile.jenkins ."
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
                    echo "[DEBUG] Tests completed"
                }
                echo "[DEBUG] Build & Test completed"
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
                success { echo '✅ Build & Test stage succeeded' }
                failure { echo '❌ Build & Test stage failed' }
            }
        }
        
        stage('Build Production Image') {
            when {
                branch 'main'
            }
            steps {
                echo "[DEBUG] Starting Build Production Image stage"
                script {
                    // Build the production Docker image using the base image
                    docker.build(
                        env.PROD_IMAGE,
                        "--build-arg BASE_IMAGE=${env.BASE_IMAGE} -f Dockerfile ."
                    )
                    echo "[DEBUG] Production image built"
                }
                echo "[DEBUG] Build Production Image completed"
            }
            post {
                success { echo '✅ Build Production Image stage succeeded' }
                failure { echo '❌ Build Production Image stage failed' }
            }
        }
        
        stage('Tag for Local Use') {
            when {
                branch 'main'
            }
            steps {
                echo "[DEBUG] Starting Tag for Local Use stage"
                script {
                    // Tag the production image as 'latest' for local use
                    sh "docker tag ${env.PROD_IMAGE} ${env.PROD_IMAGE.split(':')[0]}:latest"
                    echo "[DEBUG] Tagged ${env.PROD_IMAGE} as latest"
                }
                echo "[DEBUG] Tag for Local Use completed"
            }
            post {
                success { echo '✅ Tag for Local Use stage succeeded' }
                failure { echo '❌ Tag for Local Use stage failed' }
            }
        }
        
        stage('Deploy to On-Prem') {
            when {
                branch 'main'
            }
            steps {
                echo "[DEBUG] Starting Deploy to On-Prem stage"
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
                    echo "[DEBUG] Deployment commands sent to remote server"
                }
                echo "[DEBUG] Deploy to On-Prem completed"
            }
            post {
                success { echo '✅ Deploy to On-Prem stage succeeded' }
                failure { echo '❌ Deploy to On-Prem stage failed' }
            }
        }
    }
    
    post {
        always {
            script {
                // Ensure we're on a node for cleanup
                node('local-docker') {
                    // Clean up workspace
                    cleanWs()
                    
                    // Clean up Docker images
                    sh 'docker system prune -f'
                }
            }
        }
        success {
            echo '✅ Pipeline completed successfully! ✅'
        }
        failure {
            echo '❌ Pipeline failed! ❌'
            // Add notification here (e.g., email, Slack)
        }
    }
}
