# Use Miniconda base image
FROM continuumio/miniconda3:latest

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install JDK 19 and system dependencies
RUN cd /opt && \
    apt-get update -y && \
    wget https://download.oracle.com/java/19/archive/jdk-19.0.2_linux-x64_bin.deb && \
    apt-get install libc6-i386 libc6-x32 libxi6 libxtst6 libasound2 libfreetype6 -y && \
    dpkg -i jdk-19.0.2_linux-x64_bin.deb
    
# Set JAVA_HOME
ENV JAVA_HOME=/usr/lib/jvm/jdk-19/
ENV PATH=$JAVA_HOME/bin:$PATH

# Verify Java installation
RUN java -version

# Download and install Joern 1.2.1
RUN apt-get install curl unzip -y && \
    mkdir joern && cd joern && \
    curl -L "https://github.com/joernio/joern/releases/latest/download/joern-install.sh" -o joern-install.sh && \
    chmod u+x joern-install.sh && \
    ./joern-install.sh --version=v1.2.1

# Setup Joern
ENV JOERN_HOME=/opt/joern/joern-cli
ENV PATH=$JOERN_HOME:$PATH

# Set working directory
WORKDIR /app

# Copy project files
COPY . /app

# Create conda environment with Python 3.12.2
RUN conda create -y -n env python=3.12.2 && \
    conda clean -afy

# Activate environment and install dependencies
RUN /bin/bash -c "source activate env && \
    pip install --no-cache-dir -r requirements.txt"

# Ensure conda environment activates automatically
RUN echo "source activate env" > ~/.bashrc
ENV PATH=/opt/conda/envs/env/bin:$PATH
