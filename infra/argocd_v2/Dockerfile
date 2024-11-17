ARG ARGOCD_VERSION="v2.12.7"
FROM quay.io/argoproj/argocd:$ARGOCD_VERSION
ARG SOPS_VERSION=3.9.0
ARG KUBECTL_VERSION=1.30.2
ARG CURL_VERSION=v8.11.0
ARG VALS_VERSION=0.37.3
ARG HELM_SECRETS_VERSION=4.6.0
ARG AGE_VERSION="v1.2.0"

# vals or sops
ENV HELM_SECRETS_BACKEND="vals" \
    HELM_SECRETS_HELM_PATH=/usr/local/bin/helm \
    HELM_PLUGINS="/home/argocd/.local/share/helm/plugins/" \
    HELM_SECRETS_VALUES_ALLOW_SYMLINKS=false \
    HELM_SECRETS_VALUES_ALLOW_ABSOLUTE_PATH=false \
    HELM_SECRETS_VALUES_ALLOW_PATH_TRAVERSAL=false \
    HELM_SECRETS_WRAPPER_ENABLED=false \
    HELM_PLUGINS=/gitops-tools/helm-plugins/ \
    HELM_SECRETS_CURL_PATH=/gitops-tools/curl \
    HELM_SECRETS_SOPS_PATH=/gitops-tools/sops \
    HELM_SECRETS_VALS_PATH=/gitops-tools/vals \
    HELM_SECRETS_KUBECTL_PATH=/gitops-tools/kubectl \
    PATH="$PATH:/gitops-tools"

# Optionally, set default gpg key for sops files
# ENV HELM_SECRETS_LOAD_GPG_KEYS=/path/to/gpg.key

USER root
RUN apt-get update && \
    apt-get install -y \
      wget && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* && \
    mkdir -p /gitops-tools/helm-plugins

RUN \
    GO_ARCH=$(uname -m | sed -e 's/x86_64/amd64/') && \
    echo "Architecture is ${GO_ARCH}"

# curl installation
RUN \
    GO_ARCH=$(uname -m | sed -e 's/x86_64/amd64/') && \
    wget -O "/gitops-tools/curl" "https://github.com/moparisthebest/static-curl/releases/download/${CURL_VERSION}/curl-${GO_ARCH}" && \
    true
# kubectl installation
RUN \
    GO_ARCH=$(uname -m | sed -e 's/x86_64/amd64/' -e 's/\(arm\)\(64\)\?.*/\1\2/' -e 's/aarch64$/arm64/') && \
    wget -O "/gitops-tools/kubectl" "https://dl.k8s.io/release/v${KUBECTL_VERSION}/bin/linux/${GO_ARCH}/kubectl" && \
    true

# sops backend installation (optional)
RUN \
    GO_ARCH=$(uname -m | sed -e 's/x86_64/amd64/' -e 's/\(arm\)\(64\)\?.*/\1\2/' -e 's/aarch64$/arm64/') && \
    wget -O "/gitops-tools/sops" "https://github.com/getsops/sops/releases/download/v${SOPS_VERSION}/sops-v${SOPS_VERSION}.linux.${GO_ARCH}" && \
    true

# vals backend installation (optional)
RUN \
    GO_ARCH=$(uname -m | sed -e 's/x86_64/amd64/' -e 's/\(arm\)\(64\)\?.*/\1\2/' -e 's/aarch64$/arm64/') && \
    wget -O- "https://github.com/helmfile/vals/releases/download/v${VALS_VERSION}/vals_${VALS_VERSION}_linux_${GO_ARCH}.tar.gz" | tar zxv -C /gitops-tools vals && \
    true

# age installation
RUN \
    GO_ARCH=$(uname -m | sed -e 's/x86_64/amd64/' -e 's/\(arm\)\(64\)\?.*/\1\2/' -e 's/aarch64$/arm64/') && \
    wget -O- "https://github.com/FiloSottile/age/releases/download/${AGE_VERSION}/age-${AGE_VERSION}-linux-${GO_ARCH}.tar.gz" | tar zxv --strip-components=1 -C /gitops-tools age/age age/age-keygen

# helm secrets installation
RUN \
    wget -O- "https://github.com/jkroepke/helm-secrets/releases/download/v${HELM_SECRETS_VERSION}/helm-secrets.tar.gz" | tar -C /gitops-tools/helm-plugins -xzf- && \
    true

RUN chmod +x /gitops-tools/* && ln -sf /gitops-tools/helm-plugins/helm-secrets/scripts/wrapper/helm.sh /usr/local/sbin/helm

RUN ls -la /gitops-tools

USER argocd