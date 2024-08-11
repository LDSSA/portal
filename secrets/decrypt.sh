openssl enc -d -aes-256-cbc -pbkdf2 -base64 -in secrets/django.secrets.enc -out secrets/django_secrets.yaml
openssl enc -d -aes-256-cbc -pbkdf2 -base64 -in secrets/kubeconfig.dev.enc -out secrets/kubeconfig.dev.yaml
openssl enc -d -aes-256-cbc -pbkdf2 -base64 -in secrets/kubeconfig.prod.enc -out secrets/kubeconfig.prod.yaml
openssl enc -d -aes-256-cbc -pbkdf2 -base64 -in secrets/aws.enc -out secrets/aws.yaml