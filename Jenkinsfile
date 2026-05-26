pipeline {
    agent any

    parameters {
        booleanParam(
            name: 'RUN_LIVE_TESTS',
            defaultValue: false,
            description: 'Check to execute integration tests against the live OpenWeatherMap API'
        )
    }

    // Only static env vars here - no credentials() call at pipeline level
    environment {
        OPENWEATHER_BASE_URL = 'https://api.openweathermap.org'
        ENV                  = 'staging'
    }

    stages {
        stage('Checkout') {
            steps {
                cleanWs()
                checkout scm
            }
        }

        stage('Setup Environment') {
            steps {
                sh '''
                    echo "Initializing virtual environment..."
                    python3 -m venv .venv
                    .venv/bin/pip install --upgrade pip --quiet
                    .venv/bin/pip install -r requirements.txt --quiet
                    mkdir -p reports logs
                '''
            }
        }

        stage('Execute Mock Tests') {
            when {
                expression { return !params.RUN_LIVE_TESTS }
            }
            steps {
                sh '''
                    echo "Running test suite in offline mock mode (no API key required)..."
                    .venv/bin/pytest \
                        --junitxml=reports/junit.xml \
                        --html=reports/report.html \
                        --self-contained-html
                '''
            }
        }

        stage('Execute Live API Tests') {
            when {
                expression { return params.RUN_LIVE_TESTS }
            }
            // Credential is only bound here - live stage only
            environment {
                OPENWEATHER_API_KEY = credentials('openweather-api-key')
            }
            steps {
                sh '''
                    echo "Running test suite against live OpenWeatherMap API..."
                    .venv/bin/pytest \
                        --live \
                        --junitxml=reports/junit.xml \
                        --html=reports/report.html \
                        --self-contained-html
                '''
            }
        }
    }

    post {
        always {
            // junit and archiveArtifacts require a node/workspace context
            // agent any at pipeline level guarantees this block runs on a node
            junit allowEmptyResults: true, testResults: 'reports/junit.xml'
            archiveArtifacts(
                artifacts: 'reports/report.html, logs/framework.log',
                allowEmptyArchive: true,
                fingerprint: true
            )
        }
        success {
            echo 'Pipeline completed successfully - all API automation tests passed.'
        }
        failure {
            echo 'Pipeline failed - check the Console Output and archived artifacts above for details.'
        }
    }
}
