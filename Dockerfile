FROM centos:centos8.4.2105

RUN sed -i 's/mirrorlist/#mirrorlist/g' /etc/yum.repos.d/CentOS-* \
    && sed -i 's|#baseurl=http://mirror.centos.org|baseurl=http://vault.centos.org|g' /etc/yum.repos.d/CentOS-*

RUN dnf -y module install nodejs:12 && dnf clean all
RUN npm install -g npm
RUN curl -Ls "https://github.com/googlecodelabs/tools/releases/download/v2.2.4/claat-linux-amd64" -o /usr/local/bin/claat \
    && chmod +x /usr/local/bin/claat
