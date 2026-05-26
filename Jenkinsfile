// pipeline {
//     agent any

//     parameters {
//         booleanParam(
//             name: 'RUN_LIVE_TESTS',
//             defaultValue: false,
//             description: 'Leave UNCHECKED to run offline mock tests (no API key needed). CHECK to run against the live OpenWeatherMap API.'
//         )
//     }

//     environment {
//         OPENWEATHER_BASE_URL = 'https://api.openweathermap.org'
//         ENV                  = 'staging'
//     }

//     stages {
//         stage('Checkout') {
//             steps {
//                 cleanWs()
//                 checkout scm
//             }
//         }

//         stage('Setup Environment') {
//             steps {
//                 sh '''
//                     echo "Setting up Python virtual environment..."
//                     python3 -m venv .venv
//                     .venv/bin/pip install --upgrade pip --quiet
//                     .venv/bin/pip install -r requirements.txt --quiet
//                     mkdir -p reports logs
//                 '''
//             }
//         }

//         // ── DEFAULT ── runs when RUN_LIVE_TESTS = false (unchecked)
//         stage('Execute Mock Tests') {
//             when {
//                 expression { return params.RUN_LIVE_TESTS == false }
//             }
//             steps {
//                 sh '''
//                     echo "Running 100 test cases in offline mock mode (no API key required)..."
//                     .venv/bin/pytest \
//                         --junitxml=reports/junit.xml \
//                         --html=reports/report.html \
//                         --self-contained-html
//                 '''
//             }
//         }

//         // ── OPTIONAL ── runs only when RUN_LIVE_TESTS = true (checked)
//         stage('Execute Live API Tests') {
//             when {
//                 expression { return params.RUN_LIVE_TESTS == true }
//             }
//             steps {
//                 // withCredentials only binds here - credential is NEVER
//                 // touched during mock runs because the stage is fully skipped
//                 withCredentials([string(credentialsId: 'openweather-api-key', variable: 'OPENWEATHER_API_KEY')]) {
//                     sh '''
//                         echo "Running test suite against live OpenWeatherMap API..."
//                         .venv/bin/pytest \
//                             --live \
//                             --junitxml=reports/junit.xml \
//                             --html=reports/report.html \
//                             --self-contained-html
//                     '''
//                 }
//             }
//         }
//     }

//     post {
//         always {
//             junit allowEmptyResults: true, testResults: 'reports/junit.xml'
//             archiveArtifacts(
//                 artifacts: 'reports/report.html, logs/framework.log',
//                 allowEmptyArchive: true,
//                 fingerprint: true
//             )
//         }
//         success {
//             echo 'All API automation tests passed successfully.'
//         }
//         failure {
//             echo 'Pipeline failed - review the Console Output and archived reports above.'
//         }
//     }
// }

pipeline {
    agent any

    parameters {
        booleanParam(
            name: 'RUN_LIVE_TESTS',
            defaultValue: false,
            description: 'Leave UNCHECKED to run offline mock tests (no API key needed). CHECK to run against the live OpenWeatherMap API.'
        )
    }

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
                    echo "Setting up Python virtual environment..."
                    python3 -m venv .venv
                    .venv/bin/pip install --upgrade pip --quiet
                    .venv/bin/pip install -r requirements.txt --quiet
                    mkdir -p reports logs
                '''
            }
        }

        // ── DEFAULT ── runs when RUN_LIVE_TESTS = false (unchecked)
        stage('Execute Mock Tests') {
            when {
                expression { return params.RUN_LIVE_TESTS == false }
            }
            steps {
                sh '''
                    echo "Running 100 test cases in offline mock mode (no API key required)..."
                    .venv/bin/pytest \
                        --junitxml=reports/junit.xml \
                        --html=reports/report.html \
                        --self-contained-html
                '''
            }
        }

        // ── OPTIONAL ── runs only when RUN_LIVE_TESTS = true (checked)
        stage('Execute Live API Tests') {
            when {
                expression { return params.RUN_LIVE_TESTS == true }
            }
            steps {
                script {
                    def apiKey = input(
                        message: 'Enter the OpenWeatherMap API key for live tests',
                        ok: 'Run Live Tests',
                        parameters: [password(name: 'OPENWEATHER_API_KEY', description: 'OpenWeatherMap API key')]
                    )
                    withEnv(["OPENWEATHER_API_KEY=${apiKey}"]) {
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
        }
    }

    post {
        always {
            junit allowEmptyResults: true, testResults: 'reports/junit.xml'
            archiveArtifacts(
                artifacts: 'reports/report.html, logs/framework.log',
                allowEmptyArchive: true,
                fingerprint: true
            )
        }
        success {
            echo 'All API automation tests passed successfully.'
        }
        failure {
            echo 'Pipeline failed - review the Console Output and archived reports above.'
        }
    }
}



