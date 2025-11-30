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
                sh 'docker build -t $IMAGE .'
            }
        }
        stage('Push Image') {
            steps {
                sh 'docker push $IMAGE'
            }
        }
        stage('Deploy to Kubernetes') {
            steps {
                withCredentials([file(credentialsId: 'kubeconfig-cred-id', variable: 'KUBECONFIG')]) {
                    sh 'kubectl apply -f k8s/apps/auth-service/deploy.yaml'
                }
            }
        }
    }
}
