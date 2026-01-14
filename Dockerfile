FROM continuumio/miniconda3

WORKDIR /code

# 1. Install System Dependencies (GL libraries for CAD)
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

# 2. Copy Environment File & Create Conda Env
COPY environment.yml .
RUN conda env create -f environment.yml

# 3. Make sure commands run inside the conda env
SHELL ["conda", "run", "-n", "cad_env", "/bin/bash", "-c"]

# 4. Copy Application Code
COPY . .

# 5. Expose Streamlit Port
EXPOSE 7860

# 6. Run the App
CMD ["conda", "run", "--no-capture-output", "-n", "cad_env", "streamlit", "run", "streamlit_app.py", "--server.port=7860", "--server.address=0.0.0.0"]
