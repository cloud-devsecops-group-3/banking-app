pipeline {
    agent any

    environment {
        // Single dev host — same box the ecommerce pipeline deploys to.
        DEV_SERVER   = 'ubuntu@<EC2_PUBLIC_IP>'
        COMPOSE_DIR  = '/home/ubuntu/qr-prototype'   // holds docker-compose.yml + .env

        IMAGE_NAME      = 'banking-app'
        DOCKERHUB_IMAGE = 'lebaiidesuu/banking-app'
        TAG              = "${env.GIT_COMMIT.take(7)}"
    }

    stages {
        stage('Checkout Code') {
            steps { checkout scm }
        }

        stage('Build & Unit Test') {
            steps {
                sh '''
                if [ -d tests ]; then
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt pytest
                    PYTHONPATH=$WORKSPACE pytest
                else
                    echo "No tests folder found. Skipping tests."
                fi
                '''
            }
        }

        stage('Docker Build & Push') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-creds',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    sh '''
                    docker build -t $IMAGE_NAME:$TAG -t $DOCKERHUB_IMAGE:latest -t $DOCKERHUB_IMAGE:$TAG .
                    echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin
                    docker push $DOCKERHUB_IMAGE:$TAG
                    docker push $DOCKERHUB_IMAGE:latest
                    '''
                }
            }
        }

        // Single shared docker-compose.yml lives on the dev host and
        // orchestrates BOTH apps + both databases. This pipeline only
        // ever touches the banking-app service inside it - it never
        // recreates the ecommerce-app or the databases, so this deploy
        // can't clobber the other repo's pipeline.
        stage('Deploy to Dev (docker compose)') {
            steps {
                sshagent(credentials: ['dev-ec2-ssh-key']) {
                    sh '''
                    ssh -o StrictHostKeyChecking=no $DEV_SERVER "
                        cd $COMPOSE_DIR &&
                        sed -i 's|^BANKING_IMAGE=.*|BANKING_IMAGE=$DOCKERHUB_IMAGE:$TAG|' .env &&
                        docker compose pull banking-app &&
                        docker compose up -d banking-mysql banking-app
                    "
                    '''
                }
            }
        }

        stage('Health Check') {
            steps {
                sh '''
                sleep 10
                curl --connect-timeout 10 --max-time 20 -f http://<EC2_PUBLIC_IP>:5001/health
                '''
            }
        }
    }

    post {
        success { echo 'Banking app deployed successfully.' }
        failure {
            sshagent(credentials: ['dev-ec2-ssh-key']) {
                sh '''
                ssh -o StrictHostKeyChecking=no $DEV_SERVER "
                    cd $COMPOSE_DIR &&
                    echo '--- banking-app logs ---' && docker compose logs --tail=80 banking-app &&
                    echo '--- banking-mysql logs ---' && docker compose logs --tail=40 banking-mysql
                "
                '''
            }
        }
    }
}
