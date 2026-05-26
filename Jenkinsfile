pipeline {
    agent any

    parameters {
        booleanParam(name: 'RUN_LIVE_TESTS', defaultValue: false, description: 'Check to execute integration tests against the live OpenWeatherMap API')
    }

    environment {
        // Safe mapping of API key credential. Set up a secret text credential in Jenkins named 'openweather-api-key'
        OPENWEATHER_API_KEY = credentials('openweather-api-key')
        OPENWEATHER_BASE_URL = 'https://api.openweathermap.org'
        ENV = 'staging'
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
                script {
                    sh '''
                        echo "Initializing virtual environment..."
                        python3 -m venv .venv
                        .venv/bin/pip install --upgrade pip
                        .venv/bin/pip install -r requirements.txt
                    '''
                }
            }
        }

        stage('Execute Mock Tests') {
            when {
                expression { return !params.RUN_LIVE_TESTS }
            }
            steps {
                script {
                    sh '''
                        echo "Running test suite in offline mock mode..."
                        # Output JUnit XML report for Jenkins tracking and self-contained HTML report
                        .venv/bin/pytest --junitxml=reports/junit.xml --html=reports/report.html --self-contained-html
                    '''
                }
            }
        }

        stage('Execute Live API Tests') {
            when {
                expression { return params.RUN_LIVE_TESTS }
            }
            steps {
                script {
                    sh '''
                        echo "Running test suite in live API mode..."
                        # Execute against live endpoints using credentials injection
                        .venv/bin/pytest --live --junitxml=reports/junit.xml --html=reports/report.html --self-contained-html
                    '''
                }
            }
        }
    }

    post {
        always {
            script {
                // Publish JUnit test results in Jenkins UI
                junit allowEmptyResults: true, testResults: 'reports/junit.xml'
                
                // Archive HTML test reports and framework logs as build artifacts
                archiveArtifacts artifacts: 'reports/report.html, logs/framework.log', fingerprint: true
            }
        }
        success {
            echo "API automation execution completed successfully."
        }
        failure {
            echo "API automation execution encountered test failures or environmental errors."
        }
    }
}
