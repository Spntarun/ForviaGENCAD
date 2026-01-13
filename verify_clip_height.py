import sys
from clip_generator import ClipParameters, ClipGenerator
from groove_generator import GrooveParameters, GrooveType
from OCC.Core.BRepBndLib import brepbndlib
from OCC.Core.Bnd import Bnd_Box

def verify_clip_height():
    # Setup parameters
    user_height = 10.0
    groove_depth = 5.0
    groove_width = 5.0
    
    # Create Dummy Groove Params
    groove_params = GrooveParameters(
        width=groove_width,
        depth=groove_depth,
        height=20.0, # Groove is longer/different
        type=GrooveType.RECTANGULAR
    )
    
    # Create Clip Params with User Height
    clip_params = ClipParameters(
        groove_params=groove_params,
        height=user_height,
        assembly_clearance=0.0,
        retention_offset=0.0
    )
    
    print(f"Input User Height: {user_height}")
    
    # Generate
    generator = ClipGenerator(clip_params)
    shape = generator.create_shape()
    
    # Measure Bounding Box
    bbox = Bnd_Box()
    brepbndlib.Add(shape, bbox)
    
    xmin, ymin, zmin, xmax, ymax, zmax = bbox.Get()
    
    measured_height = ymax - ymin
    print(f"Measured Geometry Height (Y-extent): {measured_height}")
    
    # Verify
    if abs(measured_height - user_height) < 1e-6:
        print("SUCCESS: Clip Height matches User Input exactly.")
    else:
        print(f"FAILURE: Height mismatch! {measured_height} != {user_height}")
        sys.exit(1)

if __name__ == "__main__":
    verify_clip_height()
