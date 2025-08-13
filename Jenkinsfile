def dockerImage

pipeline {
  agent any
  options { timestamps() }

  environment {
    IMAGE               = "hpgowda/objectdetection:latest"  // must be lowercase
    REG_CRED            = "dockerhublogin"                  // Docker Hub Jenkins cred ID
    K8S_NS              = "kubeedge"
    KUBE_DEPLOY_NAME    = "object-detection"
    K8S_DEPLOYMENT_YAML = "server/deployment.yaml"
  }

  stages {
    // Use the job's SCM config; DO NOT add another git() here
    stage('Checkout') {
      steps { checkout scm }
    }

    stage('Build Docker Image') {
      steps {
        script {
          echo "Building Docker image..."
          sh 'docker build -f server/Dockerfile -t $IMAGE .'
        }
      }
    }

    stage('Push Docker Image') {
      steps {
        script {
          docker.withRegistry('https://index.docker.io/v1/', env.REG_CRED) {
            sh 'docker push $IMAGE'
          }
        }
      }
    }

    stage('Deploy to Kubernetes') {
      steps {
        script {
          withKubeConfig([credentialsId: 'kubeconfig']) {
            // keep manifest image in sync (safe if already correct)
            sh "sed -i 's|image:[[:space:]]*[^[:space:]]*/objectdetection:latest|image: $IMAGE|' $K8S_DEPLOYMENT_YAML || true"
            sh 'kubectl -n $K8S_NS apply -f $K8S_DEPLOYMENT_YAML'
          }
        }
      }
    }

    stage('Verify Deployment') {
      steps {
        script {
          withKubeConfig([credentialsId: 'kubeconfig']) {
            sh 'kubectl -n $K8S_NS rollout status deploy/$KUBE_DEPLOY_NAME --timeout=180s'
            sh 'kubectl -n $K8S_NS get pods -l app=$KUBE_DEPLOY_NAME -o wide'
            sh 'kubectl -n $K8S_NS get svc $KUBE_DEPLOY_NAME'
          }
        }
      }
    }
  }

  post {
    always {
      sh 'docker logout || true'
      cleanWs()
    }
  }
}
