openssl enc -e -aes-256-cbc -base64 -pbkdf2 -in secrets/django_secrets.yaml -out secrets/django.secrets.enc
openssl enc -e -aes-256-cbc -base64 -pbkdf2 -in secrets/kubeconfig.dev.yaml -out secrets/kubeconfig.dev.enc
openssl enc -e -aes-256-cbc -base64 -pbkdf2 -in secrets/kubeconfig.prod.yaml -out secrets/kubeconfig.prod.enc
openssl enc -e -aes-256-cbc -base64 -pbkdf2 -in secrets/aws.yaml -out secrets/aws.enc