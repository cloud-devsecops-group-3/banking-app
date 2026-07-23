pipeline {
    agent any

    environment {
        BANKING_SERVER = 'ubuntu@54.211.30.30'
        REMOTE_DIR = '/home/ubuntu/capstone/banking-app'

        IMAGE_NAME = 'banking-app'
        CONTAINER_NAME = 'banking-app'
        TAR_NAME = 'banking-app.tar'

        APP_PORT = '5001'

        DB_CONTAINER = 'banking-mysql'
        DB_NAME = 'bankdb'
        DB_USER = 'bankuser'
        DB_PASSWORD = 'bankpass'
        DB_ROOT_PASSWORD = 'root123'

        ECOM_CALLBACK_BASE = 'http://98.95.123.28:5000'
    }

    stages {
        stage('Checkout Code') {
            steps {
                checkout scm
            }
        }

        stage('Check Files') {
            steps {
                sh 'ls -la'
            }
        }

        stage('Run Tests If Available') {
            steps {
                sh '''
                if [ -d tests ]; then
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
                sh 'docker build -t $IMAGE_NAME:latest .'
            }
        }

        stage('Save Docker Image') {
            steps {
                sh 'docker save $IMAGE_NAME:latest -o $TAR_NAME'
            }
        }

        stage('Prepare Remote Folder') {
            steps {
                sh '''
                ssh -o StrictHostKeyChecking=no $BANKING_SERVER "
                    mkdir -p $REMOTE_DIR
                "
                '''
            }
        }

        stage('Copy Image to Banking Server') {
            steps {
                sh 'scp -o StrictHostKeyChecking=no $TAR_NAME $BANKING_SERVER:$REMOTE_DIR/'
            }
        }

        stage('Deploy Banking App') {
            steps {
                sh '''
                ssh -o StrictHostKeyChecking=no $BANKING_SERVER "
                    cd $REMOTE_DIR &&

                    docker network create banking-net || true &&

                    docker ps -a --format '{{.Names}}' | grep -w $DB_CONTAINER ||
                    docker run -d \
                        --name $DB_CONTAINER \
                        --network banking-net \
                        -e MYSQL_ROOT_PASSWORD=$DB_ROOT_PASSWORD \
                        -e MYSQL_DATABASE=$DB_NAME \
                        -e MYSQL_USER=$DB_USER \
                        -e MYSQL_PASSWORD=$DB_PASSWORD \
                        -v banking_mysql_data:/var/lib/mysql \
                        mysql:8.0 &&

                    echo 'Waiting for MySQL to initialize...' &&
                    sleep 25 &&

                    docker load -i $TAR_NAME &&

                    docker stop $CONTAINER_NAME || true &&
                    docker rm $CONTAINER_NAME || true &&

                    docker run -d \
                        --name $CONTAINER_NAME \
                        --network banking-net \
                        -p $APP_PORT:$APP_PORT \
                        -e DB_HOST=$DB_CONTAINER \
                        -e DB_NAME=$DB_NAME \
                        -e DB_USER=$DB_USER \
                        -e DB_PASSWORD=$DB_PASSWORD \
                        -e ECOM_CALLBACK_BASE=$ECOM_CALLBACK_BASE \
                        $IMAGE_NAME:latest
                "
                '''
            }
        }

        stage('Health Check') {
            steps {
                sh '''
                sleep 5
                curl -f http://54.211.30.30:5001/health
                '''
            }
        }
    }

    post {
        success {
            echo 'Banking app deployed successfully.'
        }

        failure {
            echo 'Banking app deployment failed. Check Jenkins console output.'
        }
    }
}
