pipeline {
  agent any
  options { timestamps() }

  environment {
    IMAGE               = 'hpgowda/objectdetection:latest'
    REG_CRED            = 'dockerhublogin'
    K8S_NS              = 'kubeedge'
    KUBE_DEPLOY_NAME    = 'object-detection'
    K8S_DEPLOYMENT_YAML = 'server/deployment.yaml'
  }

  stages {
    stage('Checkout') { steps { checkout scm } }

    stage('Build Docker Image') {
      steps {
        sh 'docker build -f server/Dockerfile -t $IMAGE server'
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
                    try {
                        // Echo the deploy name and namespace
                        echo "Deploying ${KUBE_DEPLOY_NAME} to Kubernetes in namespace ${KUBE_NAMESPACE}"

                        // Apply the deployment
                        sh "kubectl apply -f ${K8S_DEPLOYMENT_PATH} -n ${KUBE_NAMESPACE}"

                        // Echo success if the deployment was successful
                        echo "Deployment successful!"
                    } catch (Exception e) {
                        // If the deployment fails, print an error message and rollback
                        echo "Deployment failed! Attempting rollback."
        }
      }
    }
  }
}

    stage('Verify Deployment') {
      steps {
        script {
             withKubeConfig([credentialsId: 'kubeconfig']) {
          // Verify that the pods are running after the deployment
          sh "kubectl get pods -l app=${KUBE_DEPLOY_NAME} -n ${KUBE_NAMESPACE}"
        }
       }
      }
    }
  }

  post {
    always {
      cleanWs() // Clean up the workspace after the pipeline finishes
    }
  }

}
