pipeline {
    agent any

    stages {

        stage('Checkout') {
            steps {
                git branch: 'main',
                    url: 'https://github.com/Michael91603/projet-devops.git'
            }
        }

        stage('Build') {
            steps {
                sh 'docker build -t app-devops -f docker/Dockerfile .'
            }
        }

        stage('Test') {
            steps {
                sh 'docker run --rm app-devops python -c "import flask; print(\'Flask OK\')"'
            }
        }

        stage('Deploy') {
            steps {
                sh 'docker stop eduresources || true'
                sh 'docker rm eduresources || true'
                sh 'docker run -d -p 8082:5000 --name eduresources app-devops'
            }
        }

    }

    post {
        success {
            echo 'Déploiement réussi !'
        }
        failure {
            echo 'Echec du pipeline !'
        }
    }
}
