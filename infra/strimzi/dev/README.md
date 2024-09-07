## Strimzi Kafka Cluster

`helm install strimzi-cluster-operator -n kafka oci://quay.io/strimzi-helm/strimzi-kafka-operator --create-namespace`

## Traefik specifics (k3s ingress service)

update traefik LB to include 9094/kafka

update traefik deployment to incude `- '--entrypoints.kafka.address=:9094/tcp'`

update traefik deployment container ports to include 9094/kafka

apply ingresstcproute, if using ingress-nginx, use tcp-services configmap

```yaml
apiVersion: traefik.containo.us/v1alpha1
kind: IngressRouteTCP
metadata:
  name: kafka-ingress-tcp
  namespace: kafka
spec:
  entryPoints:
    - kafka
  routes:
    - match: HostSNI(`*`)
      priority: 10
      services:
        - name: securia-kafka-kafka-external-bootstrap
          port: 9094
          terminationDelay: 400
          weight: 10
```

apply ingress to get a cert, use the kafka-ui service.

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  annotations:
    cert-manager.io/issuer: le-prod-http
    cert-manager.io/issuer-kind: ClusterIssuer
    external-dns.alpha.kubernetes.io/hostname: kafka.marnus.com
    external-dns.alpha.kubernetes.io/target: 165.255.241.184
  name: kafka-ui
  namespace: kafka
spec:
  ingressClassName: traefik
  rules:
    - host: kafka.marnus.com
      http:
        paths:
          - backend:
              service:
                name: kafka-ui
                port:
                  number: 80
            path: /
            pathType: Prefix
  tls:
    - hosts:
        - kafka.marnus.com
      secretName: kafka-cert
```

## Create Strimzi Cluster

`kubectl apply -f strimzi_cluster.yaml`

## Create some users

`kubectl apply -f kafka_users.yaml`

## Install Kafka UI

```bash
helm repo add kafka-ui https://provectus.github.io/kafka-ui-charts
helm repo update
helm --kubeconfig --kubeconfig /home/marnus/iot/kubeconfigs/legion -n kafka upgrade -i kafka-ui kafka-ui/kafka-ui --values dev/kafka-ui-values.yaml --values secrets://dev/kafka-ui-values_secrets.yaml
```