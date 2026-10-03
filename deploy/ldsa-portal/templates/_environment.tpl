{{- define "ldsa-portal.environment" -}}
- name: EDITION_RELEASE
  value: {{ .Values.image.tag | quote }}
- name: EDITION_ENVIRONMENT
  value: {{ .Values.environment | quote }}
- name: EDITION_BACKUP_DIR
  value: /tmp/ldsa-portal-backups
{{- range $key := list "DJANGO_SECRET_KEY" "ELASTICMAIL_API_KEY" "DJANGO_AWS_ACCESS_KEY_ID" "DJANGO_AWS_SECRET_ACCESS_KEY" "POSTGRES_HOST" "POSTGRES_PASSWORD" }}
- name: {{ $key }}
  valueFrom:
    secretKeyRef:
      name: django-secrets
      key: {{ $key }}
{{- end }}
{{- range .Values.env }}
- name: {{ .name }}
  valueFrom:
    configMapKeyRef:
      key: {{ .key }}
      name: {{ .configMapName }}
{{- end }}
{{- end -}}

{{- define "ldsa-portal.graderEnvironment" -}}
- name: KUBECONFIG
  value: /home/django/.kube/config
- name: AWS_CONFIG_FILE
  value: /home/django/.aws/config
- name: AWS_SHARED_CREDENTIALS_FILE
  value: /home/django/.aws/credentials
{{- end -}}
