## Installation steps

1. Set up your k8s cluster, install helm client and configure it for your cluster.

2. Create and tag image from the provided `Dockerfile`. 

3. Upload the image to a registry and tag it. 

4. Copy the `config.yaml` to `values.yaml`

5. Edit `values.yaml`
    - add authentication configuration (see https://z2jh.jupyter.org/en/stable/administrator/authentication.html for details)
    - replace the image name and tag placeholders
    - insert an OpenAI API key in the environment variable placeholder

6. Run the helm chart:

        helm upgrade --cleanup-on-fail \
            --install scalescihub jupyterhub/jupyterhub \
            --namespace scalesci \
            --create-namespace \
            --version=2.0.0 \
            --values values.yaml
