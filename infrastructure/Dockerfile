FROM jupyter/scipy-notebook:hub-3.1.1

USER root

WORKDIR /tmp

# nbgitpuller to enable auto-populate from scalesci-demo
RUN pip install --no-cache-dir nbgitpuller

# clone and install gpt-engineer
RUN git clone https://github.com/kbuma/gpt-engineer.git && \
    cd gpt-engineer && \
    pip install --no-cache-dir . && \
    cd /tmp && \
    rm -rf /tmp/gpt-engineer && \
    fix-permissions "${CONDA_DIR}" && \
    fix-permissions "/home/${NB_USER}"


# clone and install jupyter-ai
RUN git clone https://github.com/kbuma/jupyter-ai.git && \
    cd jupyter-ai && \
    ./scripts/install.sh && \
    fix-permissions "${CONDA_DIR}" && \
    fix-permissions "/home/${NB_USER}"

# set things back to way scipy left them
USER ${NB_UID}
WORKDIR "${HOME}"