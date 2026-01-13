"""
Runtime Input Collection Module

Handles interactive user input for groove and clip parameters.
Validates all inputs and provides clear error messages.
"""

from typing import Tuple
from groove_generator import GrooveType


def get_groove_shape() -> GrooveType:
    """Prompts user for groove shape with validation (name or number)"""
    # Order matters for numeric selection
    valid_shapes_list = [
        ("rectangular", GrooveType.RECTANGULAR),
        ("circular", GrooveType.CIRCULAR),
        ("square", GrooveType.SQUARE),
        ("triangle", GrooveType.TRIANGLE)
    ]
    
    # Create lookup dictionary for names
    valid_shapes_map = {name: enum_val for name, enum_val in valid_shapes_list}
    
    print("\n" + "="*60)
    print("GROOVE SHAPE SELECTION")
    print("="*60)
    print("Available groove shapes:")
    for i, (name, _) in enumerate(valid_shapes_list, 1):
        print(f"  {i}. {name}")
    print()
    
    while True:
        user_input = input("Enter groove shape (name or number): ").strip().lower()
        
        # Check if input is a number
        if user_input.isdigit():
            idx = int(user_input) - 1
            if 0 <= idx < len(valid_shapes_list):
                name, selected = valid_shapes_list[idx]
                print(f"✓ Selected: {name}")
                return selected
        
        # Check if input is a name
        if user_input in valid_shapes_map:
            selected = valid_shapes_map[user_input]
            print(f"✓ Selected: {user_input}")
            return selected
            
        # Error message
        valid_names = [name for name, _ in valid_shapes_list]
        print(f"✗ Invalid input '{user_input}'. Please enter a number (1-{len(valid_shapes_list)}) or shape name: {', '.join(valid_names)}")


def get_positive_float(prompt: str, min_value: float = 0.01, max_value: float = 100.0, default_value: float = None) -> float:
    """Gets a positive float value from user with validation"""
    while True:
        try:
            val_str = input(prompt).strip()
            
            # Handle empty input if default is provided
            if not val_str and default_value is not None:
                print(f"✓ Using default: {default_value}")
                return default_value
                
            value = float(val_str)
            if value < min_value:
                print(f"✗ Value must be at least {min_value}mm")
                continue
            if value > max_value:
                print(f"✗ Value must be at most {max_value}mm")
                continue
            return value
        except ValueError:
            print("✗ Please enter a valid number")


def get_groove_dimensions() -> Tuple[float, float, float]:
    """Prompts user for groove dimensions (height, width, depth)"""
    print("\n" + "="*60)
    print("GROOVE DIMENSIONS")
    print("="*60)
    print("Enter dimensions in millimeters (mm)")
    print()
    
    height = get_positive_float("Groove height (mm): ", min_value=1.0, max_value=50.0)
    width = get_positive_float("Groove width (mm): ", min_value=0.5, max_value=20.0)
    depth = get_positive_float("Groove depth (mm): ", min_value=0.5, max_value=10.0)
    
    print(f"\n✓ Groove dimensions: height={height}mm, width={width}mm, depth={depth}mm")
    return height, width, depth


def get_clip_height(groove_height: float) -> float:
    """Prompts user for clip height"""
    print("\n" + "="*60)
    print("CLIP HEIGHT")
    print("="*60)
    print(f"Groove height: {groove_height}mm")
    
    # Default is 20mm, but warn if it seems excessive compared to groove
    default_height = 20.0
    print(f"Default clip height: {default_height}mm")
    
    # Allow larger clips if user insists (max_value increased significantly)
    clip_height = get_positive_float(
        f"Clip height (mm) [default: {default_height}]: ", 
        min_value=0.5, 
        max_value=200.0, 
        default_value=default_height
    )
    
    print(f"✓ Clip height: {clip_height}mm")
    return clip_height


def get_optional_clearances() -> Tuple[float, float]:
    """Prompts user for optional assembly clearance and retention offset"""
    print("\n" + "="*60)
    print("ASSEMBLY CLEARANCES (Optional)")
    print("="*60)
    print("Press Enter to use defaults")
    print()
    
    clearance_input = input("Assembly clearance (default: 0.2mm): ").strip()
    if clearance_input:
        try:
            assembly_clearance = float(clearance_input)
            if assembly_clearance < 0 or assembly_clearance > 1.0:
                print("✗ Using default 0.2mm (invalid range)")
                assembly_clearance = 0.2
        except ValueError:
            print("✗ Using default 0.2mm (invalid input)")
            assembly_clearance = 0.2
    else:
        assembly_clearance = 0.2
    
    offset_input = input("Retention offset (default: 0.1mm): ").strip()
    if offset_input:
        try:
            retention_offset = float(offset_input)
            if retention_offset < 0 or retention_offset > 0.5:
                print("✗ Using default 0.1mm (invalid range)")
                retention_offset = 0.1
        except ValueError:
            print("✗ Using default 0.1mm (invalid input)")
            retention_offset = 0.1
    else:
        retention_offset = 0.1
    
    print(f"✓ Assembly clearance: {assembly_clearance}mm, Retention offset: {retention_offset}mm")
    return assembly_clearance, retention_offset


def get_body_thickness() -> float:
    """Prompts for body thickness (mm)"""
    print("\n" + "="*60)
    print("BODY THICKNESS")
    print("="*60)
    print("Enter the desired uniform wall thickness for the body.")
    return get_positive_float("Thickness (mm) [default: 2.65]: ", min_value=0.1, max_value=20.0, default_value=2.65)

def get_groove_count() -> int:
    """Prompts for number of grooves/clips to generate"""
    print("\n" + "="*60)
    print("GROOVE/CLIP COUNT")
    print("="*60)
    print("Enter the number of grooves (and matching clips) to generate.")
    while True:
        try:
            val_str = input("Number of grooves (1-100) [default: 10]: ").strip()
            if not val_str:
                return 10
            val = int(val_str)
            if 1 <= val <= 100:
                print(f"✓ Count: {val}")
                return val
            print("✗ Please enter a number between 1 and 100.")
        except ValueError:
            print("✗ Invalid number.")

def collect_all_inputs() -> dict:
    """
    Main orchestrator function to collect all user inputs.
    Returns a dictionary with all parameters.
    """
    print("\n" + "="*60)
    print("CAD AUTOMATION - GROOVE AND CLIP GENERATION")
    print("="*60)
    print("This tool will generate grooves and matching clips on the inner surface")
    print("Clips will have IDENTICAL shape to grooves, with adjusted dimensions")
    print()
    
    # 1. Body Thickness
    thickness = get_body_thickness()
    
    # 2. Groove Count
    groove_count = get_groove_count()
    
    # 3. Collect groove parameters
    groove_shape = get_groove_shape()
    groove_height, groove_width, groove_depth = get_groove_dimensions()
    
    # 4. Collect clip parameters
    clip_height = get_clip_height(groove_height)
    
    # 5. Optional clearances
    assembly_clearance, retention_offset = get_optional_clearances()
    
    # Summary
    print("\n" + "="*60)
    print("INPUT SUMMARY")
    print("="*60)
    print(f"Body Thickness:       {thickness}mm")
    print(f"Groove/Clip Count:    {groove_count}")
    print(f"Groove Shape:         {groove_shape.value}")
    print(f"Groove Dimensions:    {groove_height}mm × {groove_width}mm × {groove_depth}mm (H×W×D)")
    print(f"Clip Height:          {clip_height}mm")
    print(f"Assembly Clearance:   {assembly_clearance}mm")
    print(f"Retention Offset:     {retention_offset}mm")
    print()
    
    calculated_clip_width = groove_width - assembly_clearance
    calculated_clip_depth = groove_depth - retention_offset
    
    print(f"Calculated Clip Dimensions: {clip_height}mm × {calculated_clip_width}mm × {calculated_clip_depth}mm (H×W×D)")
    print("="*60)
    
    confirm = input("\nProceed with these parameters? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Aborted by user.")
        exit(0)
    
    return {
        "thickness": thickness,
        "groove_count": groove_count,
        "groove_shape": groove_shape,
        "groove_height": groove_height,
        "groove_width": groove_width,
        "groove_depth": groove_depth,
        "clip_height": clip_height,
        "assembly_clearance": assembly_clearance,
        "retention_offset": retention_offset
    }


if __name__ == "__main__":
    # Test the input collection
    params = collect_all_inputs()
    print("\nCollected parameters:")
    for key, value in params.items():
        print(f"  {key}: {value}")
