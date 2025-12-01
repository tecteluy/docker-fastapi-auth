pipeline {
    agent any
    environment {
        REGISTRY = 'docker.tectel.com.uy'
        IMAGE = 'docker.tectel.com.uy/fastapi-auth:latest'
    }
    stages {
        stage('Checkout') {
            steps {
                git url: 'https://github.com/tecteluy/docker-fastapi-auth.git', branch: 'main'
            }
        }
        stage('Build Docker Image') {
            steps {
                sh 'docker build -t $IMAGE -f auth-service/Dockerfile auth-service'
            }
        }
        stage('Push Image') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'docker-registry-cred', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                    sh 'docker login docker.tectel.com.uy -u $DOCKER_USER -p $DOCKER_PASS'
                    sh 'docker push $IMAGE'
                }
            }
        }
        stage('Deploy to Kubernetes') {
            steps {
                withCredentials([file(credentialsId: 'Kubernetes', variable: 'KUBECONFIG')]) {
                    sh 'kubectl apply -f k8s/apps/auth-service/deploy.yaml'
                }
            }
        }
    }
}
