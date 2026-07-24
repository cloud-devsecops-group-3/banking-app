pipeline {
    agent any

    environment {
        DOCKERHUB_USER   = 'lebaiidesuu'
        IMAGE            = "${DOCKERHUB_USER}/banking-app"
        TAG              = "${env.GIT_COMMIT.take(7)}"

        BANKING_SERVER   = 'ubuntu@54.211.30.30'
        REMOTE_DIR       = '/home/ubuntu/qr-prototype'
    }

    stages {
        stage('Checkout Code') {
            steps {
                checkout scm
            }
        }

        stage('Run Tests If Available') {
            steps {
                sh '''
                if [ -d tests ]; then
                    echo "Tests folder found. Running tests..."
                    pip3 install -r requirements.txt
                    pip3 install pytest
                    pytest
                else
                    echo "No tests folder found. Skipping tests."
                fi
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                sh "docker build -t ${IMAGE}:${TAG} -t ${IMAGE}:latest ."
            }
        }

        stage('Push to Docker Hub') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-credentials',
                    usernameVariable: 'DH_USER',
                    passwordVariable: 'DH_TOKEN'
                )]) {
                    sh '''
                        echo $DH_TOKEN | docker login -u $DH_USER --password-stdin
                        docker push ${IMAGE}:${TAG}
                        docker push ${IMAGE}:latest
                    '''
                }
            }
        }

        stage('Deploy via docker compose') {
            steps {
                sshagent(credentials: ['bank-vm-ssh-key']) {
                    sh '''
                        ssh -o StrictHostKeyChecking=no $BANKING_SERVER "
                            cd $REMOTE_DIR &&
                            docker compose pull &&
                            docker compose up -d &&
                            docker compose ps
                        "
                    '''
                }
            }
        }

        stage('Health Check') {
            steps {
                sh '''
                echo "Waiting before health check..."
                sleep 10
                echo "Checking containers on banking server..."
                ssh -o StrictHostKeyChecking=no $BANKING_SERVER "cd $REMOTE_DIR && docker compose ps"
                echo "Checking banking app locally from banking server..."
                ssh -o StrictHostKeyChecking=no $BANKING_SERVER "curl --connect-timeout 10 --max-time 20 -f http://localhost/health"
                echo "Checking banking app publicly from Jenkins..."
                curl --connect-timeout 10 --max-time 20 -f -H "Host: bank.54-211-30-30.nip.io" http://54.211.30.30/health
                '''
            }
        }
    }

    post {
        success {
            echo 'Banking app deployed successfully.'
        }
        failure {
            echo 'Banking app deployment failed. Showing remote logs...'
            sh '''
            ssh -o StrictHostKeyChecking=no $BANKING_SERVER "
                cd $REMOTE_DIR &&
                echo '--- Containers ---' &&
                docker compose ps &&
                echo '--- Banking app logs ---' &&
                docker compose logs banking --tail 50 &&
                echo '--- nginx logs ---' &&
                docker compose logs nginx --tail 50
            "
            '''
        }
    }
}
