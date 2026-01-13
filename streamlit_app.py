import streamlit as st
import os
import sys
import time
import base64
import streamlit.components.v1 as components
from datetime import datetime

# Import core pipeline logic
from gen_cad_pipeline import run_pipeline, GrooveType

def get_step_files(directory):
    """Returns a list of .stp and .step files in the directory."""
    return [f for f in os.listdir(directory) if f.lower().endswith(('.stp', '.step'))]

def render_stl(stl_path):
    """Renders an STL file using a Three.js viewer in an iframe."""
    if not os.path.exists(stl_path):
        return
    
    with open(stl_path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/STLLoader.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
        <style>
            body {{ margin: 0; overflow: hidden; background-color: #f0f2f6; }}
            canvas {{ width: 100%; height: 100%; }}
        </style>
    </head>
    <body>
        <div id="container" style="width: 100%; height: 500px;"></div>
        <script>
            const container = document.getElementById('container');
            const scene = new THREE.Scene();
            scene.background = new THREE.Color(0xf0f2f6);
            
            const camera = new THREE.PerspectiveCamera(75, container.clientWidth / container.clientHeight, 0.1, 1000);
            camera.position.z = 50;

            const renderer = new THREE.WebGLRenderer({{ antialias: true }});
            renderer.setSize(container.clientWidth, container.clientHeight);
            container.appendChild(renderer.domElement);

            const controls = new THREE.OrbitControls(camera, renderer.domElement);
            
            const ambientLight = new THREE.AmbientLight(0x404040, 2);
            scene.add(ambientLight);
            
            const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
            directionalLight.position.set(1, 1, 1).normalize();
            scene.add(directionalLight);

            const loader = new THREE.STLLoader();
            const binaryData = atob("{data}");
            const arrayBuffer = new ArrayBuffer(binaryData.length);
            const uint8Array = new Uint8Array(arrayBuffer);
            for (let i = 0; i < binaryData.length; i++) {{
                uint8Array[i] = binaryData.charCodeAt(i);
            }}

            const geometry = loader.parse(arrayBuffer);
            const material = new THREE.MeshPhongMaterial({{ color: 0x3498db, specular: 0x111111, shininess: 200 }});
            const mesh = new THREE.Mesh(geometry, material);
            
            // Center the mesh
            geometry.computeBoundingBox();
            const center = new THREE.Vector3();
            geometry.boundingBox.getCenter(center);
            mesh.position.sub(center);
            
            scene.add(mesh);

            // Adjust camera to fit the mesh
            const box = new THREE.Box3().setFromObject(mesh);
            const size = box.getSize(new THREE.Vector3()).length();
            camera.position.z = size * 1.5;

            function animate() {{
                requestAnimationFrame(animate);
                controls.update();
                renderer.render(scene, camera);
            }}
            animate();

            window.addEventListener('resize', () => {{
                camera.aspect = container.clientWidth / container.clientHeight;
                camera.updateProjectionMatrix();
                renderer.setSize(container.clientWidth, container.clientHeight);
            }});
        </script>
    </body>
    </html>
    """
    components.html(html_code, height=520)

def main():
    st.set_page_config(page_title="Forvia CAD Automation", layout="wide")
    
    st.title("🚗 Forvia CAD Automation UI")
    
    
    # Sidebar: File Selection
    st.sidebar.header("📁 File Settings")
    
    # Option 1: Select existing file
    existing_files = get_step_files(".")
    selected_file = st.sidebar.selectbox("Select Existing Input File", existing_files if existing_files else ["No files found"])
    
    # Option 2: Upload new file
    uploaded_file = st.sidebar.file_uploader("Or Upload New STEP File", type=['stp', 'step'])
    
    if uploaded_file:
        input_path = uploaded_file.name
        with open(input_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.sidebar.success(f"Uploaded: {input_path}")
    else:
        input_path = selected_file

    output_dir = st.sidebar.text_input("Output Directory", value=os.getcwd())
    output_filename = st.sidebar.text_input("Output Filename", value="Generated_Part.stp")
    output_path = os.path.join(output_dir, output_filename)

    # Main Panel: Parameters
    st.header("⚙️ Design Parameters")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Global Parameters")
        thickness = st.number_input("Body Thickness (mm)", min_value=0.1, max_value=20.0, value=2.65, help="Example: 2.5 - 2.8 mm")
        groove_count = st.slider("Groove/Clip Count", 1, 7, 5, help="Number of features to place at reference locations.")
        
        st.subheader("Groove Settings")
        groove_shape = st.selectbox("Groove Shape", [gt.value for gt in GrooveType], index=0)
        groove_height = st.number_input("Groove Height (mm)", value=10.0, help="Total vertical height of the groove.")
        groove_width = st.number_input("Groove Width (mm)", value=5.0, help="Example: 5.0 mm for standard fit")
        groove_depth = st.number_input("Groove Depth (mm)", value=2.5, help="How deep it cuts into the material.")

    with col2:
        st.subheader("Clip Settings")
        clip_height = st.number_input("Clip Height (mm)", value=20.0, help="Total height of the protruding clip.")
        
        st.subheader("Clearances")
        assembly_clearance = st.number_input("Assembly Clearance (mm)", value=0.2, step=0.05, help="Reduction in clip width for fit. Default: 0.2")
        retention_offset = st.number_input("Retention Offset (mm)", value=0.1, step=0.05, help="Reduction in clip depth for retention. Default: 0.1")

    # Validation and Processing
    if st.button("🚀 Generate Model", use_container_width=True):
        if not input_path or input_path == "No files found":
            st.error("Please select or upload a valid STEP file.")
            return

        runtime_params = {
            "thickness": thickness,
            "groove_count": groove_count,
            "groove_shape": GrooveType(groove_shape),
            "groove_height": groove_height,
            "groove_width": groove_width,
            "groove_depth": groove_depth,
            "clip_height": clip_height,
            "assembly_clearance": assembly_clearance,
            "retention_offset": retention_offset
        }
        
        log_container = st.empty()
        status_container = st.empty()
        
        with st.spinner("Processing CAD Geometry..."):
            # Redirect stdout to capture logs (Simplified version for Streamlit)
            start_time = time.time()
            try:
                success, message = run_pipeline(input_path, output_path, runtime_params)
                
                duration = time.time() - start_time
                if success:
                    st.success(f"✔️ Model generated successfully in {duration:.2f} seconds!")
                    st.info(f"Saved to: {output_path}")
                    
                    # Provide download link if file exists
                    if os.path.exists(output_path):
                        with open(output_path, "rb") as f:
                            st.download_button(
                                label="📥 Download Generated STEP File",
                                data=f,
                                file_name=output_filename,
                                mime="application/octet-stream"
                            )
                        
                        # Display 3D Preview
                        st.subheader("🌐 3D Model Preview")
                        stl_path = output_path.replace(".stp", ".stl").replace(".step", ".stl")
                        render_stl(stl_path)
                else:
                    st.error(f"❌ Pipeline Failed: {message}")
            except Exception as e:
                st.error(f"⚠️ Critical Error: {str(e)}")

if __name__ == "__main__":
    main()
