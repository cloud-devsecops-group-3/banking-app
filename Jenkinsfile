pipeline {
    agent any

    environment {
        BANKING_SERVER = 'ubuntu@54.211.30.30'
        REMOTE_DIR = '/home/ubuntu/qr-prototype'

        IMAGE_NAME = 'banking-app'
        DOCKERHUB_IMAGE = 'lebaiidesuu/banking-app'
        CONTAINER_NAME = 'banking-app'
        TAR_NAME = 'banking-app.tar'

        DB_CONTAINER = 'banking-mysql'
        DB_NAME = 'bankdb'
        DB_USER = 'bankuser'
        DB_PASSWORD = 'devpass'
        DB_ROOT_PASSWORD = 'root123'

        NGINX_CONTAINER = 'nginx'

        ECOM_API_BASE = 'http://98-95-123-28.nip.io'
    }

    stages {
        stage('Checkout Code') {
            steps {
                checkout scm
            }
        }

        stage('Check Files') {
            steps {
                sh '''
                echo "Current workspace files:"
                ls -la
                '''
            }
        }

        stage('Run Tests If Available') {
            steps {
                sh '''
                if [ -d tests ]; then
                    echo "Tests folder found. Running tests..."

                    rm -rf venv
                    python3 -m venv venv
                    . venv/bin/activate

                    pip install --upgrade pip
                    pip install -r requirements.txt
                    pip install pytest

                    export PYTHONPATH=$WORKSPACE
                    pytest
                else
                    echo "No tests folder found. Skipping tests."
                fi
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                sh '''
                echo "Building banking Docker image..."
                docker build -t $IMAGE_NAME:latest .
                '''
            }
        }

        stage('Push Image to Docker Hub') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-creds',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    sh '''
                    echo "Logging in to Docker Hub..."
                    echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin

                    echo "Tagging banking image..."
                    docker tag $IMAGE_NAME:latest $DOCKERHUB_IMAGE:latest

                    echo "Pushing banking image to Docker Hub..."
                    docker push $DOCKERHUB_IMAGE:latest
                    '''
                }
            }
        }

        stage('Save Docker Image') {
            steps {
                sh '''
                echo "Saving Docker image as tar file..."
                docker save $IMAGE_NAME:latest -o $TAR_NAME
                ls -lh $TAR_NAME
                '''
            }
        }

        stage('Prepare Remote Folder') {
            steps {
                sh '''
                echo "Preparing banking server folder..."
                ssh -o StrictHostKeyChecking=no $BANKING_SERVER "
                    mkdir -p $REMOTE_DIR
                "
                '''
            }
        }

        stage('Copy Image to Banking Server') {
            steps {
                sh '''
                echo "Copying banking Docker image to banking server..."
                scp -o StrictHostKeyChecking=no $TAR_NAME $BANKING_SERVER:$REMOTE_DIR/
                '''
            }
        }

        stage('Deploy Banking App with Nginx') {
            steps {
                sh '''
                echo "Deploying banking app on banking server..."

                ssh -o StrictHostKeyChecking=no $BANKING_SERVER "
                    cd $REMOTE_DIR &&

                    echo 'Cleaning previous Docker Compose deployment...' &&

                    docker compose down || true &&

                    docker rm -f banking banking-app nginx banking-mysql || true &&

                    docker network rm qr-prototype_default || true &&

                    echo 'Creating Docker network if not existing...' &&
                    docker network create banking-net || true &&

                    echo 'Checking MySQL container...' &&
                    if ! docker ps -a --format '{{.Names}}' | grep -w $DB_CONTAINER; then
                        echo 'Starting new banking MySQL container...' &&
                        docker run -d \
                            --name $DB_CONTAINER \
                            --network banking-net \
                            -e MYSQL_ROOT_PASSWORD=$DB_ROOT_PASSWORD \
                            -e MYSQL_DATABASE=$DB_NAME \
                            -e MYSQL_USER=$DB_USER \
                            -e MYSQL_PASSWORD=$DB_PASSWORD \
                            -v banking_mysql_data:/var/lib/mysql \
                            mysql:8.0
                    else
                        echo 'MySQL container already exists. Starting it if stopped...' &&
                        docker start $DB_CONTAINER || true
                    fi &&

                    echo 'Waiting for MySQL to initialize...' &&
                    sleep 25 &&

                    echo 'Loading banking Docker image...' &&
                    docker load -i $TAR_NAME &&

                    echo 'Stopping old banking app container if existing...' &&
                    docker stop $CONTAINER_NAME || true &&
                    docker rm $CONTAINER_NAME || true &&

                    echo 'Starting new banking app container internally on port 5001...' &&
                    docker run -d \
                        --name $CONTAINER_NAME \
                        --network banking-net \
                        -e DB_HOST=$DB_CONTAINER \
                        -e DB_NAME=$DB_NAME \
                        -e DB_USER=$DB_USER \
                        -e DB_PASSWORD=$DB_PASSWORD \
                        -e ECOM_API_BASE=$ECOM_API_BASE \
                        $IMAGE_NAME:latest &&

                    echo 'Creating nginx.conf...' &&
                    cat > nginx.conf <<'NGINX'
events {}

http {
    server {
        listen 80;

        location / {
            proxy_pass http://banking-app:5001;
            proxy_set_header Host \\$host;
            proxy_set_header X-Real-IP \\$remote_addr;
            proxy_set_header X-Forwarded-For \\$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \\$scheme;
        }
    }
}
NGINX

                    echo 'Restarting nginx container...' &&
                    docker stop $NGINX_CONTAINER || true &&
                    docker rm $NGINX_CONTAINER || true &&

                    docker run -d \
                        --name $NGINX_CONTAINER \
                        --network banking-net \
                        -p 80:80 \
                        -v $REMOTE_DIR/nginx.conf:/etc/nginx/nginx.conf:ro \
                        nginx:alpine &&

                    echo 'Current running containers:' &&
                    docker ps
                "
                '''
            }
        }

        stage('Health Check') {
            steps {
                sh '''
                echo "Waiting before health check..."
                sleep 10

                echo "Checking container status on banking server..."
                ssh -o StrictHostKeyChecking=no $BANKING_SERVER "docker ps -a"

                echo "Checking banking app locally from banking server..."
                ssh -o StrictHostKeyChecking=no $BANKING_SERVER "curl --connect-timeout 10 --max-time 20 -f http://localhost/health"

                echo "Checking banking app publicly from Jenkins..."
                curl --connect-timeout 10 --max-time 20 -f http://54-211-30-30.nip.io/health
                '''
            }
        }
    }

    post {
        success {
            echo 'Banking app deployed successfully and pushed to Docker Hub.'
        }

        failure {
            echo 'Banking app deployment failed. Showing remote logs...'

            sh '''
            ssh -o StrictHostKeyChecking=no $BANKING_SERVER "
                echo '--- Docker containers ---' &&
                docker ps -a &&
                echo '--- Banking app logs ---' &&
                docker logs $CONTAINER_NAME || true &&
                echo '--- Nginx logs ---' &&
                docker logs $NGINX_CONTAINER || true &&
                echo '--- Banking MySQL logs ---' &&
                docker logs $DB_CONTAINER --tail 50 || true
            "
            '''
        }
    }
}
